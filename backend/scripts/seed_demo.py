"""Idempotent demo seed.

Generates the Mingchuan Bank reporting scene:
  3 accounts, cust_account_202611.csv (5,000 rows by default — the prompt's
  200k narrative is scaled down so the container stack stays small, see
  test-artifacts/gb-545/TESTING.md), org_dict_202611.csv (300 rows),
  5 preset quality rules, 1 historical run with its Issues.

Safe to run repeatedly: users upsert by email, datasets by (name, owner),
rules by (dataset_id, name), the historical batch by its report number.
"""
import csv
import io
import os
import random
from datetime import date, datetime, timedelta

from app.config.database import SessionLocal, init_db
from app.config.settings import settings
from app.constants.issue_status import IssueStatus
from app.constants.rule_run_status import RuleRunStatus
from app.constants.rule_type import RuleType
from app.constants.severity import Severity
from app.models import ColumnProfile, Dataset, Issue, QualityRule, RuleRun, User
from app.rules import engine
from app.services import auth_service, profile_service
from app.utils import storage
from app.utils.logger import log_event

ACCOUNT_FILE = "cust_account_202611.csv"
ORG_FILE = "org_dict_202611.csv"
DEMO_PASSWORD = "QualiScope@2026"

ACCOUNTS = [
    ("steward@mingchuan-bank.cn", "周砚秋", "steward"),
    ("analyst@mingchuan-bank.cn", "沈知微", "analyst"),
    ("audit@mingchuan-bank.cn", "顾清和", "viewer"),
]

SURNAMES = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴", "徐", "孙", "马", "朱", "胡"]
GIVEN = ["伟", "芳", "娜", "敏", "静", "磊", "洋", "勇", "艳", "杰", "涛", "明", "超", "秀英", "桂英"]
REGIONS = ["城东", "城西", "江南", "江北", "高新", "自贸区"]
RISK = ["低", "中", "高"]

PRESET_RULES = [
    {
        "name": "证件号非空校验",
        "rule_type": RuleType.NOT_NULL.value,
        "column_name": "cert_no",
        "params": {},
        "severity": Severity.HIGH.value,
    },
    {
        "name": "账号唯一性校验",
        "rule_type": RuleType.UNIQUE.value,
        "column_name": "account_no",
        "params": {},
        "severity": Severity.CRITICAL.value,
    },
    {
        "name": "账户余额非负校验",
        "rule_type": RuleType.RANGE.value,
        "column_name": "balance",
        "params": {"min": 0, "max": 50000000},
        "severity": Severity.CRITICAL.value,
    },
    {
        "name": "证件号格式校验",
        "rule_type": RuleType.REGEX.value,
        "column_name": "cert_no",
        "params": {"pattern": r"\d{18}"},
        "severity": Severity.MEDIUM.value,
    },
    {
        "name": "账户状态枚举校验",
        "rule_type": RuleType.ENUM_SET.value,
        "column_name": "status",
        "params": {"values": ["A", "I", "D"]},
        "severity": Severity.MEDIUM.value,
    },
]


def build_account_csv(rows: int, org_codes: list[str]) -> bytes:
    random.seed(20261109)
    null_rows = set(range(0, rows, 143))          # ~0.7% empty cert_no
    duplicate_rows = {100: "AC999999000001", 2500: "AC999999000001"}
    negative_rows = {777, 1888, 3141}
    unknown_status = {101: "X", 202: "X", 303: "P", 404: "P"}
    invalid_branch = {1500: "BR9999", 2600: "BR9999"}

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["account_no", "cust_name", "cert_no", "balance", "open_date", "status", "branch_code", "channel"]
    )
    for index in range(rows):
        account_no = duplicate_rows.get(index) or f"AC{202611000000 + index:012d}"
        cust_name = SURNAMES[index % len(SURNAMES)] + GIVEN[(index * 7) % len(GIVEN)]
        cert_no = "" if index in null_rows else str(110101199003070000 + index)
        balance = round(random.uniform(1200.0, 880000.0), 2)
        if index in negative_rows:
            balance = -round(random.uniform(500.0, 9000.0), 2)
        open_date = (date(2019, 1, 1) + timedelta(days=(index * 13) % 2200)).isoformat()
        if index in unknown_status:
            status = unknown_status[index]
        elif index % 17 == 0:
            status = "I"
        elif index % 23 == 0:
            status = "D"
        else:
            status = "A"
        branch_code = invalid_branch.get(index) or org_codes[index % len(org_codes)]
        channel = ["APP", "WEB", "COUNTER"][index % 3]
        writer.writerow([account_no, cust_name, cert_no, f"{balance:.2f}", open_date, status, branch_code, channel])
    return buffer.getvalue().encode("utf-8")


def build_org_csv(rows: int) -> tuple[bytes, list[str]]:
    codes = [f"BR{index:04d}" for index in range(1, rows + 1)]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["branch_code", "branch_name", "region", "risk_level"])
    for index, code in enumerate(codes):
        writer.writerow([code, f"明川银行{REGIONS[index % len(REGIONS)]}支行{index + 1:03d}", REGIONS[index % len(REGIONS)], RISK[index % 3]])
    return buffer.getvalue().encode("utf-8"), codes


def _upsert_dataset(db, owner: User, filename: str, payload: bytes, source_format: str) -> Dataset:
    path, checksum = storage.write_dataset_file(filename, payload)
    from app.profiling.loader import load_frame

    loaded = load_frame(path, source_format)
    dataset = db.query(Dataset).filter(Dataset.name == filename, Dataset.owner_id == owner.id).first()
    if dataset is None:
        dataset = Dataset(owner_id=owner.id, name=filename, source_format=source_format, file_path=path, checksum=checksum)
        db.add(dataset)
    dataset.file_path = path
    dataset.checksum = checksum
    dataset.row_count = loaded.row_count
    dataset.column_count = loaded.column_count
    dataset.file_size = len(payload)
    dataset.status = "profiled"
    dataset.is_deleted = False
    db.commit()
    db.refresh(dataset)
    return dataset


def _ensure_profile(db, dataset: Dataset, actor: User) -> RuleRun:
    existing = (
        db.query(RuleRun)
        .filter(RuleRun.dataset_id == dataset.id, RuleRun.kind == "profile")
        .order_by(RuleRun.id.desc())
        .first()
    )
    if existing is not None and existing.status == RuleRunStatus.SUCCEEDED.value:
        return existing
    run = existing or RuleRun(dataset_id=dataset.id, kind="profile", triggered_by=actor.id, status=RuleRunStatus.QUEUED.value)
    if existing is None:
        db.add(run)
        db.commit()
        db.refresh(run)
    profile_service.compute_profiles(db, dataset, run)
    return run


def _ensure_rules(db, dataset: Dataset, actor: User) -> list[QualityRule]:
    rules = []
    for spec in PRESET_RULES:
        rule = (
            db.query(QualityRule)
            .filter(QualityRule.dataset_id == dataset.id, QualityRule.name == spec["name"])
            .first()
        )
        if rule is None:
            rule = QualityRule(
                dataset_id=dataset.id,
                name=spec["name"],
                rule_type=spec["rule_type"],
                column_name=spec["column_name"],
                params_json=spec["params"],
                severity=spec["severity"],
                is_active=True,
                sample_limit=200,
                created_by=actor.id,
            )
            db.add(rule)
            db.flush()
            log_event(
                "AUDIT_RULE_CREATE",
                rule_id=rule.id,
                dataset_id=dataset.id,
                rule_type=rule.rule_type,
                column=rule.column_name,
                severity=rule.severity,
            )
        rules.append(rule)
    db.commit()
    return rules


def _ensure_history_run(db, dataset: Dataset, rules: list[QualityRule], actor: User, analyst: User) -> RuleRun:
    existing = (
        db.query(RuleRun)
        .filter(RuleRun.dataset_id == dataset.id, RuleRun.kind == "rules", RuleRun.report_no.isnot(None))
        .order_by(RuleRun.id.asc())
        .first()
    )
    if existing is not None:
        return existing

    run = RuleRun(
        dataset_id=dataset.id,
        kind="rules",
        triggered_by=actor.id,
        status=RuleRunStatus.QUEUED.value,
        rules_total=len(rules),
        started_at=datetime.now() - timedelta(minutes=6),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    engine.execute_batch(db, run, dataset, rules, triggered_by=actor.id)
    db.refresh(run)

    severity_by_rule = {rule.id: rule.severity for rule in rules}
    issues = db.query(Issue).filter(Issue.rule_run_id == run.id).order_by(Issue.id.asc()).all()
    high_count = 0
    for issue in issues:
        severity = severity_by_rule.get(issue.rule_id)
        if severity == Severity.CRITICAL.value:
            issue.status = IssueStatus.TRIAGED.value
            issue.assignee_id = analyst.id
            issue.note = "报送前已指派给业务方核对"
        elif severity == Severity.HIGH.value and high_count < 3:
            issue.status = IssueStatus.TRIAGED.value
            issue.assignee_id = actor.id
            high_count += 1
    db.commit()
    return run


def run_seed() -> dict:
    init_db()
    storage.ensure_dirs()
    log_event("SEED_DEMO_STARTED")
    db = SessionLocal()
    try:
        users = {}
        for email, display_name, role in ACCOUNTS:
            users[role] = auth_service.upsert_user(
                db, email, DEMO_PASSWORD, display_name, role, settings.SCAN_DAILY_QUOTA
            )
        steward = users["steward"]
        analyst = users["analyst"]
        db.commit()

        org_bytes, org_codes = build_org_csv(settings.SEED_ORG_ROWS)
        account_bytes = build_account_csv(settings.SEED_ACCOUNT_ROWS, org_codes)

        # the customer account table is the primary specimen -> created first
        account_dataset = _upsert_dataset(db, steward, ACCOUNT_FILE, account_bytes, "csv")
        org_dataset = _upsert_dataset(db, steward, ORG_FILE, org_bytes, "csv")

        _ensure_profile(db, account_dataset, steward)
        _ensure_profile(db, org_dataset, steward)

        rules = _ensure_rules(db, account_dataset, steward)
        run = _ensure_history_run(db, account_dataset, rules, steward, analyst)

        datasets = db.query(Dataset).filter(Dataset.is_deleted.is_(False)).count()
        rule_count = db.query(QualityRule).count()
        run_count = db.query(RuleRun).filter(RuleRun.kind == "rules").count()
        issue_count = db.query(Issue).count()
        log_event(
            "SEED_DEMO_FINISHED",
            datasets=datasets,
            rules=rule_count,
            runs=run_count,
            issues=issue_count,
        )
        return {
            "datasets": datasets,
            "rules": rule_count,
            "runs": run_count,
            "issues": issue_count,
            "report_no": run.report_no,
            "profile_rows": account_dataset.row_count,
        }
    finally:
        db.close()


if __name__ == "__main__":
    print(run_seed())
