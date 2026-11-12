"""集成验证：批次中止的并发语义（SQLite + 内存锁降级，无需 MySQL/Redis）。

覆盖题目要求的全部行为：
1. 执行中取消 —— 状态立即冻结为 cancelled，已完成部分留作诊断（item/issue 保留），
   未跑规则补 cancelled 占位，问题单转 ignored 离开待处理台账；
2. 取消后晚到的完成信号（worker 重入 execute_batch / execute_rules）不再改变批次；
3. 取消后同一数据集下一批次立即可跑；旧批次晚到的锁释放伤不到新批次的锁；
4. 台账三态区分：cancelled / failed / succeeded 各自独立；
5. 取消的批次不触发 recheck，不会误伤后续批次的问题单。

用法: PYTHONPATH=<deps> python3 -I scripts/verify_cancellation.py
"""
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

TMP = tempfile.mkdtemp(prefix="qs-cancel-")
os.environ["REDIS_URL"] = "redis://127.0.0.1:6399/0"  # 快速连接失败 → 内存锁降级

from app.config.settings import Settings, settings  # noqa: E402

Settings.database_url = property(lambda self: f"sqlite:///{TMP}/verify.db")
settings.ARTIFACT_DIR = os.path.join(TMP, "datasets")
settings.QUARANTINE_DIR = os.path.join(TMP, "quarantine")

from app.config.database import SessionLocal, init_db  # noqa: E402
from app.constants.issue_status import IssueStatus  # noqa: E402
from app.constants.rule_run_status import RuleRunItemStatus, RuleRunStatus  # noqa: E402
from app.constants.rule_type import RuleType  # noqa: E402
from app.middlewares import quota  # noqa: E402
from app.models import Dataset, Issue, QualityRule, RuleRun, RuleRunItem, User  # noqa: E402
from app.rules import engine  # noqa: E402
from app.services import run_service  # noqa: E402
from app.tasks.execute_rules import execute_rules  # noqa: E402
from app.utils import storage  # noqa: E402

PASSED = []


def check(label: str, condition: bool) -> None:
    PASSED.append((label, condition))
    print(f"  [{'ok' if condition else 'FAIL'}] {label}")
    if not condition:
        raise AssertionError(label)


CSV_PAYLOAD = (
    "account_no,cust_name,balance\n"
    "A001,张三,100\n"
    "A002,,250\n"          # rule1 not_null cust_name 违规
    "A003,李四,-50\n"      # rule2 range balance 违规
    "A003,王五,300\n"      # rule3 unique account_no 违规
    "A004,赵六,400\n"
)


def make_fixtures(db) -> tuple[User, Dataset, list[QualityRule]]:
    actor = User(
        email="verify@mingchuan-bank.cn",
        password_hash="x",
        display_name="验证员",
        role="steward",
        daily_scan_quota=100,
    )
    db.add(actor)
    db.commit()
    path, checksum = storage.write_dataset_file("verify.csv", CSV_PAYLOAD.encode())
    dataset = Dataset(
        owner_id=actor.id,
        name="verify.csv",
        source_format="csv",
        file_path=path,
        checksum=checksum,
        row_count=5,
        column_count=3,
        file_size=len(CSV_PAYLOAD),
        status="profiled",
    )
    db.add(dataset)
    db.commit()
    specs = [
        ("cust_name 非空", RuleType.NOT_NULL.value, "cust_name", {}),
        ("balance 区间", RuleType.RANGE.value, "balance", {"min": 0, "max": 1000}),
        ("account_no 唯一", RuleType.UNIQUE.value, "account_no", {}),
    ]
    rules = []
    for name, rule_type, column, params in specs:
        rule = QualityRule(
            dataset_id=dataset.id,
            name=name,
            rule_type=rule_type,
            column_name=column,
            params_json=params,
            severity="high",
            is_active=True,
            sample_limit=50,
            created_by=actor.id,
        )
        db.add(rule)
        rules.append(rule)
    db.commit()
    return actor, dataset, rules


def run_row(db, run_id: int) -> RuleRun:
    db.expire_all()
    return db.get(RuleRun, run_id)


def scenario_mid_flight_cancel(db, actor, dataset, rules) -> int:
    print("\n场景 1：执行中取消 —— 冻结 + 诊断留存 + 未跑完占位")
    run = run_service.bulk_run(db, actor, dataset.id)  # dispatch 已打桩为 no-op
    run_id = run.id
    check("批次创建为 queued 且带锁令牌", run.status == "queued" and bool(run.lock_token))

    # 锁互斥：同数据集第二批次立即被拒绝
    try:
        run_service.bulk_run(db, actor, dataset.id)
        check("执行中第二批次被 RUN_LOCKED 拒绝", False)
    except Exception as exc:
        check("执行中第二批次被 RUN_LOCKED 拒绝", getattr(exc, "code", None) == "QUAL-2011")

    original_get_checker = engine.get_checker
    calls = {"n": 0}

    def hooked_get_checker(rule_type):
        checker = original_get_checker(rule_type)

        def wrapped(ctx):
            result = checker(ctx)
            calls["n"] += 1
            if calls["n"] == 2:
                # 第 2 条规则扫完、结果落库前：另一会话确认中止
                side = SessionLocal()
                try:
                    run_service.cancel_run(side, side.get(RuleRun, run_id), side.get(User, actor.id))
                finally:
                    side.close()
            return result

        return wrapped

    engine.get_checker = hooked_get_checker
    try:
        outcome = execute_rules(run_id, [rule.id for rule in rules])
    finally:
        engine.get_checker = original_get_checker

    check("worker 上报 cancelled", outcome.get("cancelled") is True)
    run = run_row(db, run_id)
    check("状态冻结为 cancelled（不再变回成功）", run.status == RuleRunStatus.CANCELLED.value)
    check("error_code 标记为 QUAL-5010", run.error_code == "QUAL-5010")
    check("finished_at 已落库", run.finished_at is not None)
    check("取消批次不分配报告单号", run.report_no is None)

    items = db.query(RuleRunItem).filter(RuleRunItem.run_id == run_id).order_by(RuleRunItem.id).all()
    finished = [item for item in items if item.status == RuleRunItemStatus.FINISHED.value]
    placeholders = [item for item in items if item.status == RuleRunItemStatus.CANCELLED.value]
    check("已完成 1 条规则留作诊断（item 保留）", len(finished) == 1)
    check("未跑完的 2 条规则有 cancelled 占位", len(placeholders) == 2)
    check("占位规则点名（rule2/rule3）", {p.rule_id for p in placeholders} == {rules[1].id, rules[2].id})
    check("rules_unfinished = 2", run.rules_unfinished == 2)
    check("通过/失败只统计已完成规则", run.rules_passed + run.rules_failed == 1)

    issues = db.query(Issue).filter(Issue.rule_run_id == run_id).all()
    check("已完成规则的问题单保留（诊断可查）", len(issues) >= 1)
    check(
        "问题单全部转 ignored 且带中止备注",
        all(issue.status == IssueStatus.IGNORED.value and "批次已中止" in (issue.note or "") for issue in issues),
    )
    open_rows = (
        db.query(Issue)
        .join(RuleRun, Issue.rule_run_id == RuleRun.id)
        .filter(RuleRun.dataset_id == dataset.id, Issue.status == IssueStatus.OPEN.value)
        .all()
    )
    check("待处理台账不再出现该批问题单", all(issue.rule_run_id != run_id for issue in open_rows))

    check("取消后数据集锁已释放", quota.acquire_dataset_lock(dataset.id, "probe"))
    quota.release_dataset_lock(dataset.id, "probe")
    return run_id


def scenario_next_batch_and_stale_signals(db, actor, dataset, rules, cancelled_run_id: int) -> int:
    print("\n场景 2：下一批次立即开跑；旧批次的晚到信号全部失效")
    run = run_service.bulk_run(db, actor, dataset.id)
    next_id = run.id
    check("取消后下一批次立即拿到锁", run.status == "queued" and bool(run.lock_token))

    # 旧批次 worker 的 finally 晚到：不得解开新批次的锁
    stale_token = db.get(RuleRun, cancelled_run_id).lock_token
    quota.release_dataset_lock(dataset.id, stale_token)
    try:
        run_service.bulk_run(db, actor, dataset.id)
        check("旧批次晚到的锁释放伤不到新批次", False)
    except Exception as exc:
        check("旧批次晚到的锁释放伤不到新批次", getattr(exc, "code", None) == "QUAL-2011")

    outcome = execute_rules(next_id, [rule.id for rule in rules])
    check("新批次正常跑完", outcome.get("ok") is True and not outcome.get("cancelled"))
    run = run_row(db, next_id)
    check("新批次 succeeded", run.status == RuleRunStatus.SUCCEEDED.value)
    check("新批次报告单号按 run id 唯一", run.report_no == f"QC-202611-{next_id:03d}")

    # 旧批次 worker 被重复投递（晚到的执行信号）
    stale = execute_rules(cancelled_run_id, [rule.id for rule in rules])
    check("旧批次晚到执行被直接拒绝", stale.get("cancelled") is True)
    check("旧批次状态仍是 cancelled", run_row(db, cancelled_run_id).status == RuleRunStatus.CANCELLED.value)

    # 旧批次晚到的 recheck 不得误伤新批次的问题单
    fresh_issues = db.query(Issue).filter(Issue.rule_run_id == next_id).all()
    check("新批次的问题单仍是 open（未被旧批次 recheck）",
          len(fresh_issues) >= 1 and all(issue.status == IssueStatus.OPEN.value for issue in fresh_issues))
    check("旧批次问题单仍是 ignored",
          all(issue.status == IssueStatus.IGNORED.value
              for issue in db.query(Issue).filter(Issue.rule_run_id == cancelled_run_id).all()))
    return next_id


def scenario_queued_cancel(db, actor, dataset, rules) -> int:
    print("\n场景 3：排队中取消 —— 全部规则记未跑完，worker 拾起即退")
    run = run_service.bulk_run(db, actor, dataset.id)
    run_id = run.id
    run_service.cancel_run(db, db.get(RuleRun, run_id), actor)
    run = run_row(db, run_id)
    check("queued 直接转 cancelled", run.status == RuleRunStatus.CANCELLED.value)
    check("全部 3 条规则记未跑完", run.rules_unfinished == 3)
    placeholders = db.query(RuleRunItem).filter(
        RuleRunItem.run_id == run_id, RuleRunItem.status == RuleRunItemStatus.CANCELLED.value
    ).all()
    check("3 条 cancelled 占位 item", len(placeholders) == 3)

    outcome = execute_rules(run_id, [rule.id for rule in rules])  # worker 晚到拾起
    check("worker 拾起已取消批次直接退出", outcome.get("cancelled") is True)
    check("状态保持 cancelled", run_row(db, run_id).status == RuleRunStatus.CANCELLED.value)
    count = db.query(RuleRunItem).filter(RuleRunItem.run_id == run_id).count()
    check("不再产生新的规则结果", count == 3)

    # 直接重入引擎（晚到的完成信号）
    summary = engine.execute_batch(db, run_row(db, run_id), db.get(Dataset, dataset.id), rules)
    check("引擎重入返回 cancelled", summary.get("cancelled") is True)
    check("引擎重入后状态仍 cancelled", run_row(db, run_id).status == RuleRunStatus.CANCELLED.value)
    return run_id


def scenario_failed_distinct(db, actor, dataset, rules) -> None:
    print("\n场景 4：失败与中止是两种终态")
    path, checksum = storage.write_dataset_file("broken.csv", CSV_PAYLOAD.encode())
    broken = Dataset(
        owner_id=actor.id, name="broken.csv", source_format="csv", file_path=path,
        checksum=checksum, row_count=5, column_count=3, file_size=1, status="profiled",
    )
    db.add(broken)
    db.commit()
    rule = QualityRule(
        dataset_id=broken.id, name="cust_name 非空", rule_type=RuleType.NOT_NULL.value,
        column_name="cust_name", params_json={}, severity="low", is_active=True, sample_limit=10,
        created_by=actor.id,
    )
    db.add(rule)
    db.commit()
    os.remove(path)  # 文件缺失 → 执行失败
    run = run_service.bulk_run(db, actor, broken.id)
    try:
        execute_rules(run.id, [rule.id])
    except Exception:
        pass  # worker 侧异常向上抛（celery 记录），此处只关心落库状态
    run = run_row(db, run.id)
    check("文件缺失的批次落为 failed", run.status == RuleRunStatus.FAILED.value)
    check("failed 批次带错误码", bool(run.error_code))
    try:
        run_service.cancel_run(db, run, actor)
        check("failed 终态不可再取消", False)
    except Exception as exc:
        check("failed 终态不可再取消", getattr(exc, "code", None) == "QUAL-2011")
    check("失败后锁已释放", quota.acquire_dataset_lock(broken.id, "probe2"))
    quota.release_dataset_lock(broken.id, "probe2")


def scenario_double_cancel(db, actor, dataset, rules) -> None:
    print("\n场景 5：重复取消幂等拒绝")
    run = run_service.bulk_run(db, actor, dataset.id)
    run_service.cancel_run(db, db.get(RuleRun, run.id), actor)
    try:
        run_service.cancel_run(db, run_row(db, run.id), actor)
        check("第二次取消被拒绝", False)
    except Exception as exc:
        check("第二次取消被拒绝", getattr(exc, "code", None) == "QUAL-2011")


def main() -> None:
    init_db()
    storage.ensure_dirs()
    # bulk_run 默认会 dispatch 到 celery；验证脚本手动控制执行时机
    run_service.dispatch_execute_run = lambda run_id, rule_ids: None

    db = SessionLocal()
    try:
        actor, dataset, rules = make_fixtures(db)
        cancelled_id = scenario_mid_flight_cancel(db, actor, dataset, rules)
        scenario_next_batch_and_stale_signals(db, actor, dataset, rules, cancelled_id)
        scenario_queued_cancel(db, actor, dataset, rules)
        scenario_failed_distinct(db, actor, dataset, rules)
        scenario_double_cancel(db, actor, dataset, rules)
    finally:
        db.close()
    print(f"\n全部通过：{len(PASSED)} 项断言")


if __name__ == "__main__":
    main()
