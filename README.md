# QualiScope · 数据质量剖析与规则治理平台

把一份数据集从「不知道能不能用」验到「每一行违规都有据可查」：上传 → 列级剖析 → 规则构建 → 批量执行 → 违规隔离 → 问题分诊 → 报告单归档。

模拟客户是**明川银行**数据治理组（城商行，数仓 600+ 张表，监管报送一年 4 次）。系统替换的是「个人 SQL + Excel 台账」这一段：不再只给一个通过率，而是能回答哪一列、第几行、观测到什么值、期望什么、谁在跟进、这一批次报告单编号是多少。

## 快速启动

```bash
cp .env.example .env
docker compose up -d
```

首次启动会自动建表并（`SEED_DEMO=true`）灌入演示数据；MySQL 首次初始化需要 20~40 秒，等 `docker compose ps` 全部 `healthy` 再访问：

- 前端：<http://localhost:18114>
- API 文档：<http://localhost:19114/docs>
- MySQL 对本机：`127.0.0.1:17614`（仅排查用）

### 手动灌演示数据（幂等）

```bash
docker compose exec backend python -m scripts.seed_demo
```

重复执行不会出现第二份 `cust_account_202611.csv`、不会重复插入同名规则与重复批次（dataset 按 `(name, owner_id)`、rule 按 `(dataset_id, name)`、历史批次按 `report_no` upsert）。

`SEED_DEMO=false` 启动的是一个空库版本（只有表结构与空目录），适合干净环境演示对比。

### 演示账号（密码统一 `QualiScope@2026`）

| 角色 | 邮箱 | 主要页面 |
|---|---|---|
| 数据管家 steward | `steward@mingchuan-bank.cn` | /datasets、/datasets/:id/profile、/rules、/runs |
| 分析师 analyst | `analyst@mingchuan-bank.cn` | /datasets/:id/profile、/rules、/runs、/issues |
| 审计 viewer | `audit@mingchuan-bank.cn` | /runs、/issues（只读） |

## 典型使用场景

报送前第 3 天上午：管家登录 `/datasets`，数据集里已有 `cust_account_202611.csv`（客户账户，演示 seed 为 5,000 行，见下方说明）与机构字典 `org_dict_202611.csv`（300 行）；进 `/datasets/:id/profile` 看报告单：`cert_no` 空值率约 0.7%，`balance` 出现负数，`status` 有 2 个未知值（不在机构字典枚举里），`pattern_summary` 给出证件号正则与命中率；进 `/rules` 从剖析推荐补规则；点批量执行后 `/runs` 逐条规则打勾，结束显示真实违规条数；进 `/issues` 把 critical 指派给业务方，每条都带 `row_index` 与 `observed_value`；复跑同一批规则后已收敛条目转 fixed；导出 `QC-202611-001` 报告单给审计；审计用只读账号复核，上传/建规则/执行/指派按钮全部被禁用。

> 演示数据说明：题目叙事里 `cust_account_202611.csv` 是 20 万行、37 条违规，但 20 万行 × 0.7% 空值率 ≈ 1,400 行违规，两者本身不自洽。为了容器可快速起停，seed 默认生成 **5,000 行**（`SEED_ACCOUNT_ROWS` 可调），空值率仍按 0.7% 构造；页面上的违规条数由后端真实扫描得出，不做任何写死。详见 `test-artifacts/gb-545/TESTING.md` 的「已知差异」。

## 主要功能

- **列级剖析**：`profiling/loader.py` 读 CSV/Parquet/JSONL/XLSX（重复列名 400、非 UTF-8 400、超行数 400）；`type_infer.py` 抽样 1 万行按命中率 ≥0.95 判类型；`stats.py` 全量算空值率/基数/分位/Top 值；`pattern.py` 字符类归并推断正则与命中率；`outliers.py` IQR 1.5 倍异常值。
- **规则构建与批量执行**：7 种 `RuleType` 各自独立校验器，pandas 向量化定位 + 逐条保留 `row_index` 与原文 `observed_value`，每规则最多落 `sample_limit` 条 Issue 但统计值记真实数量；违规行同时写入隔离卷 `run_XXXXXX_quarantine.csv`。
- **问题分诊与指派**：状态机 `open → triaged → fixed/ignored`，支持按严重度/状态/规则筛选、批量指派、复制复现片段。
- **审计与配额**：写操作在响应阶段写入 `audit_logs`（before/after 快照）；`users.daily_scan_quota` + Redis 滑动窗口 + `SET runlock:{dataset_id} {token} NX EX` 保证同一数据集不并行执行，超限 429 并带 `retry_after`；批次中止后锁按 token 定向释放，旧批次晚到的结束信号解不开新批次的锁。

## 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Vue 3.4 + TypeScript 5 + Vite 5 + Pinia + Tailwind CSS 3.4（oklch token） |
| 后端 | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Alembic |
| 数据库 | MySQL 8.0（utf8mb4，JSON 列存 params/top_values，`null_rate` DECIMAL(6,4)） |
| 队列 | Celery 5 + Redis 7（剖析与规则执行在 worker 内完成） |
| 统计 | pandas 2.2 + numpy 2.1（分位、IQR、向量化违规定位） |

## 目录结构

```
gb-545/
├── docker-compose.yml            # 5 个服务 + 4 个命名卷
├── .env / .env.example
├── frontend/                     # Vue SPA，Nginx 托管并反代 /api/
│   └── src/{api,stores,types,components,hooks,pages,router,utils,constants,styles}
├── backend/                      # FastAPI + 剖析 + 规则引擎 + seed
│   ├── app/{routes,controllers,services,models,schemas,middlewares,utils,profiling,rules,constants,config,tasks}
│   ├── alembic/versions/
│   └── scripts/seed_demo.py
└── worker/                       # Celery worker（复用 backend 依赖层）
    ├── Dockerfile
    ├── entrypoint.sh             # 等 db/redis → 心跳文件 → celery worker
    └── healthy.py                # compose healthcheck 读心跳
```

共享卷：`dataset_data` → backend & worker 的 `/data/datasets`（上传即落盘、执行即可读）；`quarantine_data` → 两者的 `/data/quarantine`（每批次违规行隔离样本）。

## 环境变量

| 键 | 用途 | 示例 | 必填 |
|---|---|---|---|
| COMPOSE_PROJECT_NAME | 容器名前缀 | qualiscope | 是 |
| DB_NAME | 业务库名 | qualiscope_db | 是 |
| DB_USER / DB_PASSWORD | 业务账号 | qualiscope_user / qualiscope_pwd | 是 |
| DB_ROOT_PASSWORD | root 口令 | qualiscope_root_pwd | 是 |
| JWT_SECRET | JWT 签名密钥（8 小时过期） | change_me_to_a_long_random_string | 是 |
| FRONTEND_PORT | 前端宿主端口 | 18114 | 是 |
| BACKEND_PORT | 后端宿主端口 | 19114 | 是 |
| DB_PORT | MySQL 宿主映射 | 17614 | 是 |
| REDIS_URL | Redis 连接串 | redis://redis:6379/0 | 是 |
| ARTIFACT_DIR | 数据集落盘目录 | /data/datasets | 是 |
| QUARANTINE_DIR | 隔离样本目录 | /data/quarantine | 是 |
| MAX_UPLOAD_MB | 单文件上限 | 64 | 是 |
| MAX_ROWS | 行数上限 | 200000 | 是 |
| SCAN_DAILY_QUOTA | 每日扫描配额 | 40 | 是 |
| SEED_DEMO | 启动时自动 seed | true | 是 |

## Docker 说明

- 5 个服务：`frontend`（Nginx + SPA）、`backend`（FastAPI，`:8000` → `${BACKEND_PORT}`）、`worker`（Celery，无对外端口，靠心跳文件 healthcheck）、`db`（mysql:8.0）、`redis`（redis:7-alpine，`--appendonly yes`）。
- 端口映射：`18114:80`、`19114:8000`、`17614:3306`；redis 与 worker 不对宿主暴露。
- 四个命名卷：`mysql_data`、`redis_data`、`dataset_data`、`quarantine_data`。
- 首次启动要等 MySQL 初始化：`backend`/`worker` 都 `depends_on: db: service_healthy`，`frontend` 等 `backend: service_healthy`。
- 看 worker 执行日志：`docker compose logs -f worker`（每条规则完成、批次完成都有结构化 `event=` 行）。
- 重建数据库：`docker compose down -v` 后重新 `up -d`（会删除 `mysql_data` 与数据卷）。
- 上传大小与行数上限：改 `.env` 的 `MAX_UPLOAD_MB` / `MAX_ROWS`，并同步 `frontend/nginx.conf` 的 `client_max_body_size`。

## 本地三端开发（Docker 之外）

```bash
# 前端
cd frontend && pnpm install && pnpm dev        # http://localhost:18114，/api 代理到 19114

# 后端
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                            # 或让启动钩子 create_all
uvicorn app.main:app --reload --port 19114

# worker
cd backend && celery -A app.config.celery_app worker -l info
```

## 共享枚举出现位置清单

### ColumnType（integer/decimal/string/date/boolean/unknown）

- 前端：`constants/columnType.ts`（枚举定义 + 中文标签 + 数值类型集合）、`types/profile.ts`（inferred_type 字段）、`utils/columnFormat.ts`（对齐与截断）、`components/profile/ColumnTable.vue`（类型角标）、`components/rule/ColumnPicker.vue`（列选择器类型角标）、`pages/DatasetProfilePage.vue`（报告单表头）、`pages/RulesPage.vue`（列面板）
- 后端：`app/constants/column_type.py`（定义 + NUMERIC_TYPES）、`profiling/type_infer.py`（判定）、`profiling/stats.py`（数值列分位分支）、`profiling/suggest.py`（推荐规则）、`schemas/profile.py`（序列化 + is_numeric）、`services/profile_service.py`（模式摘要分支）、`utils/formatters.py`（中文名）、`constants/messages.py`（COLUMN_TYPE_LABELS）、`models/column_profile.py`（inferred_type 列）

### RuleType（not_null/unique/range/regex/enum_set/referential/expression）

- 前端：`constants/ruleType.ts`（定义 + 标签 + 提示）、`types/rule.ts`（QualityRule.rule_type / RuleDraft）、`utils/ruleSerialize.ts`（按类型序列化与校验）、`api/rule.ts`（draftToPayload 分派）、`components/rule/RuleParamForm.vue`（参数表单分派）、`components/rule/RuleCard.vue`、`pages/RulesPage.vue`
- 后端：`app/constants/rule_type.py`（定义 + PARAM_KEYS）、`schemas/rule.py`（Literal）、`rules/registry.py`（分派表 + 校验）、`rules/{not_null,unique,range_rule,regex_rule,enum_set,referential,expression}.py`、`rules/engine.py`（逐规则执行）、`rules/base.py`（上下文）、`utils/formatters.py`（参数摘要/期望表达式）、`constants/error_codes.py`、`constants/log_templates.py`、`models/quality_rule.py`

### Severity（low/medium/high/critical）

- 前端：`constants/severity.ts`（定义 + 顺序 + 权重）、`utils/severityTone.ts`（配色与形状）、`utils/percent.ts`（加权统计）、`components/common/SeverityBadge.vue`、`components/rule/SeveritySelect.vue`、`pages/IssuesPage.vue`（筛选与汇总）、`pages/RunsPage.vue`
- 后端：`app/constants/severity.py`（定义 + 权重 + 中文名）、`schemas/rule.py`（Literal）、`rules/engine.py`（RuleRunItem.severity）、`services/issue_service.py`（按严重度统计）、`utils/formatters.py`（severity_label / 加权）、`models/quality_rule.py`、`constants/log_templates.py`（审计 payload）、`scripts/seed_demo.py`（预置规则分档）

### IssueStatus（open/triaged/fixed/ignored）

- 前端：`constants/issueStatus.ts`（定义 + 标签）、`types/issue.ts`、`components/issue/IssueStatusMenu.vue`（状态按钮组）、`components/issue/IssueDrawer.vue`、`components/issue/IssueFilterBar.vue`、`stores/issueStore.ts`、`pages/IssuesPage.vue`（列分组）
- 后端：`app/constants/issue_status.py`（定义 + 状态机 TRANSITIONS）、`services/issue_service.py`（流转校验）、`rules/engine.py`（新建 open）、`rules/engine.py#recheck_open_issues`（收敛转 fixed）、`models/issue.py`、`scripts/seed_demo.py`（triaged 预置）

### RuleRunStatus（queued/running/succeeded/failed/cancelled）

- 前端：`constants/ruleRunStatus.ts`（枚举定义 + 中文标签 + 终态 + item 状态）、`components/run/RunStatusTag.vue`、`components/run/RunProgressList.vue`（未跑完占位）、`hooks/useRunPolling.ts`（终态停表）、`types/run.ts`、`pages/RunsPage.vue`（中止按钮 + 确认框）
- 后端：`app/constants/rule_run_status.py`（定义 + TERMINAL_STATUSES + ACTIVE_STATUSES + RuleRunItemStatus + RunKind）、`tasks/execute_rules.py`（取消观测 / 守卫置 failed）、`tasks/profile_dataset.py`、`services/run_service.py`（queued / cancel_run 冻结批次）、`rules/engine.py`（协作式取消 + 守卫终态写入）、`models/rule_run.py`、`models/rule_run_item.py`、`constants/log_templates.py`

中止语义：`POST /runs/{id}/cancel` 仅在 queued/running 时生效（条件更新，幂等于并发），批次即刻冻结为 `cancelled`；该批 open/triaged 问题单批量转 `ignored`（仅诊断留存，可再打开），未跑规则补 `cancelled` 占位 item；worker 每条规则前后检查取消信号，终态写入全部带状态守卫，晚到的完成信号直接丢弃；数据集锁按 `lock_token` 定向释放，旧批次无法解开新批次的锁。

## 七种规则类型（params 形态 + 最小示例）

| rule_type | params_json | 示例 |
|---|---|---|
| not_null | `{}` | 列 `cert_no` 非空 |
| unique | `{}` | 列 `account_no` 唯一 |
| range | `{"min":0,"max":50000000}` | 余额介于 0 与 5000 万 |
| regex | `{"pattern":"\\d{18}"}` | 证件号 18 位数字 |
| enum_set | `{"values":["A","I","D"]}` | 账户状态枚举 |
| referential | `{"target_dataset_id":2,"target_column":"branch_code"}` | 开户机构必须在机构字典里 |
| expression | `{"expr":"balance > 0 and status in [\"A\",\"I\"]"}` | 白名单运算符/函数，拒绝属性访问与导入 |

## 三处代码分层（严禁合并职责到单一文件）

前端每个页面至少触达 api → store → hook → 组件四层；后端每个写操作至少触达 route → controller → service → model 四层，剖析与规则执行再经 tasks → profiling/rules。`main.py` 中中间件挂载顺序：`auth → rate limit(quota) → 业务路由 → audit（响应阶段）→ error_handler（最外层兜底）`。

## License

MIT
