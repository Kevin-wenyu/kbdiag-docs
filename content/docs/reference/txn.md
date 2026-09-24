---
title: "txn: transactions"
description: "List open transactions and prepared (two-phase) ones, and flag long ones."
weight: 40
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `0a4d61e` (static linux/amd64 binary). This is lab evidence, not production validation. The transactions in the examples were created by fault-injection scripts: 365547 opened a transaction and sits idle in transaction, and `kbdiag_inj_2pc` is a prepared transaction that was neither committed nor rolled back. PIDs, counts and timings belong to this capture only.

## Usage

```text
kbdiag txn [--limit N] [--xact-warn SECONDS] [--xact-fail SECONDS] [--prepared-fail SECONDS] [--json]
```

| Option | Effect |
|---|---|
| `--limit N` | Show at most N sessions; default 50, `0` for all |
| `--xact-warn SECONDS` | WARN when a transaction is older than this; default 300 |
| `--xact-fail SECONDS` | FAIL when a transaction is older than this; default 1800 |
| `--prepared-fail SECONDS` | FAIL when a prepared transaction is older than this; default 900 |
| `--json` | Print JSON |

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}). `--limit` only affects what is shown; the verdict always covers every session.

## Default output

```bash
~/kbdiag txn --limit 5
echo EXIT_CODE=$?
```

```text
txn  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:39:03+08:00)

session.activity: 1 rows
pid     usename  datname  application_name     client_addr  backend_type    state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
365547  system   test     kbdiag_inj_idle_txn  -            client backend  idle in transaction  6019         -             5.7         4.7          3.7          Client           ClientRead  select txid_current() as kbdiag_last, pg_sleep(1);

txn.prepared: 1 rows
gid             owner   database  prepared_at                age_s  transaction
kbdiag_inj_2pc  system  test      2026-09-24T04:38:56+08:00  7.4    6018
EXIT_CODE=0
```

- `session.activity` lists two kinds of session: those inside a transaction (with a transaction start, a transaction id `backend_xid` or a snapshot `backend_xmin`), and those whose state is hidden, so it cannot tell (no privilege, track_activities off). The columns are those of `sessions`.
- `txn.prepared` lists every prepared transaction. They belong to no session, so `sessions` cannot show them.
- Neither is past its default threshold, so the verdict is OK.

## WARN and FAIL

With lower thresholds:

```bash
~/kbdiag txn --xact-warn 2 --prepared-fail 2 --limit 5
echo EXIT_CODE=$?
```

```text
txn  FAIL  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:39:04+08:00)

[WARN] txn.long  会话 365547 的事务已开了 6 秒，当前 idle in transaction
  verify: kbdiag session 365547  # 看它在跑什么、持有哪些锁、有没有挡住别人

[FAIL] txn.prepared  两阶段事务 kbdiag_inj_2pc 已 prepare 8 秒未结束，压着视界
  fix: ROLLBACK PREPARED 'kbdiag_inj_2pc'  # 先和应用确认它该提交还是回滚（提交用 COMMIT PREPARED）；要连到库 test 执行，且不能放在事务块里

session.activity: 1 rows
pid     usename  datname  application_name     client_addr  backend_type    state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
365547  system   test     kbdiag_inj_idle_txn  -            client backend  idle in transaction  6019         -             6.2         5.2          4.2          Client           ClientRead  select txid_current() as kbdiag_last, pg_sleep(1);

txn.prepared: 1 rows
gid             owner   database  prepared_at                age_s  transaction
kbdiag_inj_2pc  system  test      2026-09-24T04:38:56+08:00  7.9    6018
EXIT_CODE=2
```

- 365547 is past `--xact-warn` but not `--xact-fail` (default 1800), so it is a WARN.
- A prepared transaction has only a FAIL level: it holds back VACUUM and keeps its locks until someone commits or rolls it back.
- The `fix` line gives the statement to run. kbdiag only prints it. Its note says: confirm with the application whether to commit (`COMMIT PREPARED`) or roll back, connect to database `test`, and run it outside a transaction block.
- With a FAIL the exit code is 2.

## On a standby

```bash
~/kbdiag txn --limit 3
echo EXIT_CODE=$?
```

```text
txn  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-24T04:39:05+08:00)

session.activity: 0 rows
pid  usename  datname  application_name  client_addr  backend_type  state  backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query

txn.prepared: not_applicable  备库看不到主库的两阶段提交事务，请在主库上运行 kbdiag txn
EXIT_CODE=0
```

- A standby cannot see the primary's prepared transactions, so `txn.prepared` is `not_applicable` there. It does not mean "none", and it does not affect the verdict.
- Check prepared transactions on the primary.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN |
| 2 | FAIL |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
