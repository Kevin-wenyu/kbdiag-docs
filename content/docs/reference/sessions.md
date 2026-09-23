---
title: "sessions: list sessions"
description: "List sessions and flag long idle-in-transaction ones."
weight: 10
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `84c883e` (static linux/amd64 binary). This is lab evidence, not production validation. The two application sessions in the examples were created by fault-injection scripts; PIDs, counts and timings belong to this capture only.

## Usage

```text
kbdiag sessions [--active] [--limit N] [--idle-in-txn-warn SECONDS] [--json]
```

| Flag | Effect |
|---|---|
| `--active` | Show only sessions running a query. Rows whose state cannot be seen (insufficient privilege, or the session turned off track_activities) are still shown |
| `--limit N` | Show at most N rows, default 50; `0` shows all |
| `--idle-in-txn-warn SECONDS` | WARN when a session is idle in transaction longer than this, default 300 |
| `--json` | Print the report as JSON |

Connection flags `--host`, `-p`, `-d`, `-U` and `--timeout` are global. Defaults: local socket in `/tmp`, port 54321, database `test`, user `system`. The password comes from `PGPASSWORD` or `~/.pgpass`. The connection runs read-only transactions and sets `lock_timeout`.

`--active` and `--limit` only change what is displayed. Findings always cover every session, so a hidden session can still raise a WARN.

## Default output

```bash
~/kbdiag sessions --limit 6
echo EXIT_CODE=$?
```

```text
kbdiag sessions [--active] [--limit N] [--idle-in-txn-warn 秒] [--json]
```

- The first line gives the verdict and context: OK, version, role (primary), connection identity and capture time.
- Rows are sorted by transaction age (`xact_age_s`) descending, rows without a transaction last, then by PID. Background processes are listed too.
- Every `*_age_s` column is in seconds. `-` means null.
- Session 320047 has been idle in transaction for 9.8 seconds, below the default 300, so the verdict is OK.

## A WARN

Lower the threshold to 5 seconds and show only active sessions:

```bash
~/kbdiag sessions --active --idle-in-txn-warn 5
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T00:09:11+08:00)

session.activity: 6 rows
pid     usename  datname  application_name       client_addr  backend_type         state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event         query
320047  system   test     kbdiag_inj_idle_txn    -            client backend       idle in transaction  5898         -             11.8        10.8         9.8          Client           ClientRead         select txid_current() as kbdiag_last, pg_sleep(1);
320211  system   test     kbdiag_inj_long_query  -            client backend       active               -            5898          9           9            9            Timeout          PgSleep            select pg_sleep(3600);
3271    -        -        check pointer          -            checkpointer         -                    -            -             -           -            -            Activity         CheckpointerMain   
3272    -        -        background flush       -            background writer    -                    -            -             -           -            -            Activity         BgWriterHibernate  
3273    -        -        wal flush              -            walwriter            -                    -            -             -           -            -            Activity         WalWriterMain      
3274    -        -        auto vacuum            -            autovacuum launcher  -                    -            -             -           -            -            Activity         AutoVacuumMain     
... 7 more rows not shown (use --limit 0 to show all)
EXIT_CODE=0
```

- Session 320047 is hidden by `--active`, but the WARN is still raised: display filters do not affect findings.
- The `verify` line gives the next command to run; see [`session`]({{< relref "/docs/reference/session" >}}).
- Exit status 1 means at least one WARN.

`--json` carries the same content: `verdict`, `context`, `data` (per probe: `status`, `columns`, `rows`, `truncated`), `findings` (each with `evidence` and `next`) and `redacted`. The symptom text is currently Chinese.

## Insufficient privilege

Connect remotely as `kbdiag_ro`, an account without a monitoring role:

```bash
PGPASSWORD=... ~/kbdiag sessions --host 127.0.0.1 -U kbdiag_ro --active
echo EXIT_CODE=$?
```

```text
sessions  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T00:09:12+08:00)

[WARN] session.idle_in_txn  会话 320047 处于 idle in transaction 已 10 秒
  verify: kbdiag session 320047  # 看它持有哪些锁、有没有挡住别人

session.activity: 2 rows
pid     usename  datname  application_name       client_addr     backend_type    state   backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event     query
320211  system   test     kbdiag_inj_long_query  -               client backend  active  -            5898          9.5         9.5          9.5          Timeout          PgSleep        select pg_sleep(3600);
261437  esrep    -        node2                  192.168.105.11  walsender       active  -            -             -           -            10392.7      Activity         WalSenderMain  
EXIT_CODE=1
```

- The state of 12 rows is hidden, so they cannot be judged. The verdict is UNKNOWN with exit status 3, not OK. The same idle-in-transaction session is still there; this account just cannot see its state.
- `redacted` lists each hidden column and how many rows it affects. `backend_xid` and `backend_xmin` stay visible.
- Granting the `sys_monitor` role reveals the full information.
- A session that turns off `track_activities` for itself (`SET` or `ALTER ROLE ... SET`) shows `state` as `disabled`. Such rows are also treated as UNKNOWN, with the redaction reason `track_activities_off`.

## Exit status

| Status | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN |
| 2 | FAIL |
| 3 | UNKNOWN: some data was not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect to the database |

[Back to the user manual]({{< relref "/docs/reference" >}})
