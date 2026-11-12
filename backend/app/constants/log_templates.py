"""Central structured-log catalogue (24 templates).

Every service / controller / task logs exclusively through
``utils.logger.log_event(key, **fields)`` so that changing a template here
changes the API logs, the Celery worker logs and the stdout of the seed script
at the same time.
"""

LOG_TEMPLATES = {
    # --- upload / dataset ---
    "UPLOAD_STARTED": "upload started name={name} size_bytes={size_bytes} format={source_format}",
    "UPLOAD_SUCCEEDED": "upload succeeded dataset_id={dataset_id} rows={rows} columns={columns} checksum={checksum}",
    "UPLOAD_VALIDATION_FAILED": "upload validation failed name={name} error_code={error_code} reason={reason}",
    "DATASET_DELETED": "dataset soft-deleted dataset_id={dataset_id} name={name}",
    "DATASET_FILE_MISSING": "dataset file missing on shared volume dataset_id={dataset_id} path={path}",
    # --- profiling ---
    "PROFILE_ENQUEUED": "profile enqueued dataset_id={dataset_id} run_id={run_id}",
    "PROFILE_STARTED": "profile started dataset_id={dataset_id} run_id={run_id} rows={rows}",
    "PROFILE_FINISHED": "profile finished dataset_id={dataset_id} run_id={run_id} columns={columns} duration_ms={duration_ms}",
    "PROFILE_TIMEOUT": "profile timed out dataset_id={dataset_id} run_id={run_id} after_ms={duration_ms}",
    "PROFILE_RUN_LOCKED": "profile rejected, dataset run locked dataset_id={dataset_id} user_id={user_id}",
    # --- rules ---
    "AUDIT_RULE_CREATE": "rule created rule_id={rule_id} dataset_id={dataset_id} rule_type={rule_type} column={column} severity={severity}",
    "AUDIT_RULE_UPDATE": "rule updated rule_id={rule_id} dataset_id={dataset_id} severity={severity}",
    "AUDIT_RULE_TOGGLE": "rule toggled rule_id={rule_id} is_active={is_active}",
    "AUDIT_RULE_DELETE": "rule deleted rule_id={rule_id} dataset_id={dataset_id}",
    "RULE_PARAMS_REJECTED": "rule params rejected rule_type={rule_type} column={column} reason={reason}",
    # --- runs ---
    "AUDIT_RULE_BULK_RUN": "bulk run enqueued run_id={run_id} dataset_id={dataset_id} rules_total={rules_total}",
    "RUN_STARTED": "run started run_id={run_id} dataset_id={dataset_id} rules_total={rules_total} rows={rows_scanned}",
    "RUN_RULE_FINISHED": "rule finished run_id={run_id} rule_id={rule_id} column={column} passed={passed} violations={violations} duration_ms={duration_ms}",
    "RUN_FINISHED": "run finished run_id={run_id} status={status} passed={rules_passed} failed={rules_failed} duration_ms={duration_ms}",
    "RUN_FAILED": "run failed run_id={run_id} error_code={error_code} reason={reason}",
    "RUN_CANCELLED": "run cancelled run_id={run_id} by={actor_id}",
    # --- issues ---
    "AUDIT_ISSUE_GENERATED": "issues generated run_id={run_id} rule_id={rule_id} violations={violations} persisted={persisted}",
    "AUDIT_ISSUE_ASSIGN": "issue assigned issue_id={issue_id} assignee_id={assignee_id} status={status}",
    "AUDIT_ISSUE_STATUS": "issue status changed issue_id={issue_id} from={before} to={after}",
    "AUDIT_ISSUE_RECHECK": "issues rechecked run_id={run_id} fixed_count={fixed_count} remaining={remaining}",
    # --- cross-cutting ---
    "AUDIT_QUOTA_REJECTED": "quota rejected user_id={user_id} used={used} quota={quota}",
    "AUDIT_RATE_LIMITED": "rate limit hit user_id={user_id} window_max={window_max}",
    "AUDIT_WRITE_FAILED": "audit write failed action={action} entity={entity_type} reason={reason}",
    "SEED_DEMO_STARTED": "demo seed started",
    "SEED_DEMO_FINISHED": "demo seed finished datasets={datasets} rules={rules} runs={runs} issues={issues}",
    "SEED_DEMO_FAILED": "demo seed failed error={error}",
    "AUTH_LOGIN_SUCCEEDED": "login succeeded user_id={user_id} role={role}",
    "AUTH_LOGIN_FAILED": "login failed email={email} reason={reason}",
}

REQUIRED_FIELDS = {
    "UPLOAD_SUCCEEDED": ["dataset_id", "rows", "columns"],
    "PROFILE_FINISHED": ["dataset_id", "run_id", "duration_ms"],
    "RUN_FINISHED": ["run_id", "rules_passed", "rules_failed"],
    "RUN_RULE_FINISHED": ["run_id", "rule_id", "violations"],
    "AUDIT_ISSUE_GENERATED": ["run_id", "rule_id", "violations"],
}
