---
title: "session: one session"
description: "See what one session runs, waits on, which locks it holds, and whom it blocks or is blocked by."
weight: 20
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `0a4d61e` (static linux/amd64 binary). This is lab evidence, not production validation. The lock wait in the examples was created by a fault-injection script: 367208 holds an exclusive lock on table `kbdiag_inj_lock` without committing, and 367217 waits for it. PIDs, counts and timings belong to this capture only.

The finding text is in Chinese; the tool prints it that way. The JSON fields are stable for scripts.

## Usage

```text
kbdiag session <pid> [--lock-wait-warn SECONDS] [--idle-in-txn-warn SECONDS] [--json]
```

| Option | Effect |
|---|---|
| `<pid>` | PID of the session to show; required |
| `--lock-wait-warn SECONDS` | WARN when waiting for a lock longer than this; default 10 |
| `--idle-in-txn-warn SECONDS` | WARN when idle in transaction longer than this; default 300 |
| `--json` | Print JSON |

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## A session waiting for a lock

```bash
~/kbdiag session 367217
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:41:05+08:00)

[WARN] lock.waiting  会话 367217 等 public.kbdiag_inj_lock 的 AccessShareLock 已 13 秒，被 367208 挡住
  verify: kbdiag session 367208  # 看挡路的会话在干什么

lock.list: 2 rows
pid     locktype    relation                mode             granted  wait_s  blocked_by
367217  virtualxid  -                       ExclusiveLock    true     -       []
367217  relation    public.kbdiag_inj_lock  AccessShareLock  false    12.9    [367208]

session.activity: 1 rows
pid     usename  datname  application_name        client_addr  backend_type    state   backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
367217  system   test     kbdiag_inj_lock_waiter  -            client backend  active  -            6022          12.9        12.9         12.9         Lock             relation    select count(*) from kbdiag_inj_lock;
EXIT_CODE=1
```

- `lock.list` holds this session's own locks. The row with `granted=false` is the lock it waits for; `blocked_by` lists the sessions blocking it directly.
- `session.activity` is this session's activity row, with the same columns as `sessions`.
- It has waited 13 seconds, over the default 10, so the verdict is WARN and the exit code 1. The finding says session 367217 has waited 13 seconds for an AccessShareLock on `public.kbdiag_inj_lock`, blocked by 367208; the `verify` line points at the blocker.
- `wait_s` is an approximation: the time since the session's last state change.

## The blocking session

```bash
~/kbdiag session 367208
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:41:05+08:00)

[WARN] lock.waiting  会话 367217 等 public.kbdiag_inj_lock 的 AccessShareLock 已 13 秒，被 367208 挡住
  verify: kbdiag session 367208  # 看挡路的会话在干什么

lock.list: 4 rows
pid     locktype       relation                mode                 granted  wait_s  blocked_by
367208  relation       public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
367208  transactionid  -                       ExclusiveLock        true     -       []
367208  virtualxid     -                       ExclusiveLock        true     -       []
367217  relation       public.kbdiag_inj_lock  AccessShareLock      false    13      [367208]

session.activity: 1 rows
pid     usename  datname  application_name        client_addr  backend_type    state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
367208  system   test     kbdiag_inj_lock_holder  -            client backend  idle in transaction  6022         -             13.1        13.1         13.1         Client           ClientRead  lock table kbdiag_inj_lock in access exclusive mode;
EXIT_CODE=1
```

- For a blocker, `lock.list` also shows the locks of the sessions it blocks (the last row, 367217).
- The blocker is idle in transaction: it holds the lock, its transaction is open, and it runs nothing. This is the usual shape of an application that forgot to commit.
- It would only get its own `session.idle_in_txn` after 300 seconds; the WARN here comes from 367217, which it blocks.

`--json` prints the same content. The `evidence` of `lock.waiting` carries `waiter_pid`, `blocker_pids`, `relation`, `lock_mode` and `wait_s` for scripts:

```json
{
  "id": "lock.waiting",
  "level": "WARN",
  "symptom": "会话 367217 等 public.kbdiag_inj_lock 的 AccessShareLock 已 13 秒，被 367208 挡住",
  "evidence": [
    {
      "probe_id": "lock.list",
      "fields": {
        "blocker_pids": [367208],
        "lock_mode": "AccessShareLock",
        "relation": "public.kbdiag_inj_lock",
        "wait_s": 13.1,
        "waiter_pid": 367217
      }
    }
  ],
  "cause": null,
  "next": [{"kind": "verify", "command": "kbdiag session 367208", "note": "看挡路的会话在干什么"}]
}
```

## No such session

```bash
~/kbdiag session 999999
echo EXIT_CODE=$?
```

```text
kbdiag: no session with pid 999999 (it may have ended)
session  UNKNOWN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:38:55+08:00)

lock.list: 0 rows
pid  locktype  relation  mode  granted  wait_s  blocked_by

session.activity: 0 rows
pid  usename  datname  application_name  client_addr  backend_type  state  backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
EXIT_CODE=3
```

- When the PID is not found (it may have ended), a note goes to standard error, the verdict is UNKNOWN and the exit code 3.
- Omitting the PID is a usage error, exit code 64.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN |
| 2 | FAIL |
| 3 | UNKNOWN: no such session, or data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
