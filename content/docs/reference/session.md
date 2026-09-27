---
title: "session: one session"
description: "One session: its full SQL, what it waits for, whom it blocks and which locks it holds."
weight: 20
---

Captured on 2026-09-27 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `93bf65d` (static linux/amd64 binary). This is lab evidence, not production validation. The sessions in the examples were created by fault-injection scripts: 1045715 holds an exclusive lock on table `kbdiag_inj_lock` idle in transaction, 1045724 waits for it, and 1045809 is a second session idle in transaction. PIDs, counts and timings belong to this capture only.

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

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}). The thresholds and findings are the same as those of `sessions` and [`locks`]({{< relref "/docs/reference/locks" >}}).

## A session waiting for a lock

```bash
~/kbdiag session 1045724
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:22+08:00)

[WARN] lock.waiting  session 1045724 has waited 35s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1045715
  verify: kbdiag session 1045715  # what the blocking session is doing

session 1045724
  user         system
  database     test
  application  kbdiag_inj_lock_waiter
  client       local
  type         client backend
  state        active  (for 35s)
  xact         35s
  query        35s
  wait         Lock:relation
  xid / xmin   - / 6343

sql
  select count(*) from kbdiag_inj_lock;

waiting for: 1
  object                  wants            waited  blocked by
  public.kbdiag_inj_lock  AccessShareLock  35s     1045715

blocking: 0

holds: 0
EXIT_CODE=1
```

- The block at the top says who the session is (user, database, application, client, type) and what it does: its state and how long it has been in it, the transaction and statement ages, the wait event, and its transaction id and snapshot xmin.
- `sql` is the statement in full, with its line breaks. This is the only command that shows the whole SQL. For an idle session the heading reads `last sql`, since that statement has finished.
- `waiting for` is the lock it wants, how long it has waited and who blocks it directly.
- It has waited 35 seconds, over the default 10, so there is a `lock.waiting` WARN and the exit code is 1. The `verify` line points at the blocker.
- `waited` is measured from the session's last state change, so it can overstate the wait a little, never understate it.

## The blocking session

```bash
~/kbdiag session 1045715
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:21+08:00)

[WARN] lock.waiting  session 1045724 has waited 34s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1045715

session 1045715
  user         system
  database     test
  application  kbdiag_inj_lock_holder
  client       local
  type         client backend
  state        idle in transaction  (for 34s)
  xact         34s
  query        34s
  wait         -
  xid / xmin   6343 / -

last sql
  lock table kbdiag_inj_lock in access exclusive mode;

waiting for: 0

blocking: 1
  pid      object                  wants            waited
  1045724  public.kbdiag_inj_lock  AccessShareLock  34s

holds: 1
  object                  mode
  public.kbdiag_inj_lock  AccessExclusiveLock
EXIT_CODE=1
```

- `blocking` lists the sessions waiting for locks this session holds. `holds` lists its locks.
- Every transaction holds its own `virtualxid` and `transactionid` locks; they are left out of `holds` unless someone waits for a lock of that type. The xid is in the block at the top.
- A row lock is labelled with its type, for example `public.t (tuple)`, so it is not read as a table lock.
- The WARN is the waiter's `lock.waiting`: it says this session has been blocking another for 34 seconds, which is this session's problem. It has no `verify` line, since it would point back here.
- The session has been idle in transaction for 34 seconds: it took the lock and never committed. Its own `session.idle_in_txn` would come at 300 seconds.

## Idle in transaction

With the threshold lowered to 10 seconds:

```bash
~/kbdiag session 1045809 --idle-in-txn-warn 10
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:23+08:00)

[WARN] session.idle_in_txn  session 1045809 has been idle in transaction for 32s

session 1045809
  user         system
  database     test
  application  kbdiag_inj_idle_txn
  client       local
  type         client backend
  state        idle in transaction  (for 33s)
  xact         35s
  query        34s
  wait         -
  xid / xmin   6344 / -

last sql
  select txid_current() as kbdiag_last, pg_sleep(1);

waiting for: 0

blocking: 0

holds: 0
EXIT_CODE=1
```

The session has a transaction id but holds no lock others want, so `holds` is empty. What it holds back is the vacuum horizon; see [`txn`]({{< relref "/docs/reference/txn" >}}).

## Insufficient privilege

Connect as `kbdiag_ro`, which has no monitoring role, and look at the blocker:

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro session 1045715
echo EXIT_CODE=$?
```

```text
session  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:35:28+08:00)

session 1045715
  user         system
  database     test
  application  kbdiag_inj_lock_holder
  client       ?
  type         ?
  state        ?
  xact         ?
  query        ?
  wait         ?
  xid / xmin   6343 / -

sql
  ?

waiting for: 0

blocking: 1
  pid      object                  wants            waited
  1045724  public.kbdiag_inj_lock  AccessShareLock  ?

holds: 1
  object                  mode
  public.kbdiag_inj_lock  AccessExclusiveLock
redacted: 1 row of session.activity hides state, backend_type, client_addr, ages, wait, query (insufficient_privilege; grant sys_monitor)
redacted: 1 row of lock.list hides wait (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- User, database and application are visible, and so are the transaction id and xmin. State, times, client, type, wait and SQL show `?`.
- Locks and who blocks whom are visible; how long the other session has waited is not.
- The session cannot be judged, so the verdict is UNKNOWN with exit code 3. Grant `sys_monitor` to see everything.

## No such session

```bash
~/kbdiag session 999999
echo EXIT_CODE=$?
```

```text
kbdiag: no session with pid 999999 (it may have ended)
session  UNKNOWN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:46+08:00)

session 999999: not found (it may have ended)
EXIT_CODE=3
```

When the PID is not found (it may have ended), a note goes to standard error, the verdict is UNKNOWN and the exit code 3. Omitting the PID is a usage error, exit code 64.

## JSON

`--json` carries the activity row and the lock rows the text is built from, with raw values: times in seconds and every lock row, including `virtualxid`. The `lock.waiting` finding of the waiter above, with the fields scripts can use:

```json
{
  "id": "lock.waiting",
  "level": "WARN",
  "symptom": "session 1045724 has waited 37s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1045715",
  "evidence": [
    {
      "probe_id": "lock.list",
      "fields": {
        "blocker_pids": [
          1045715
        ],
        "lock_mode": "AccessShareLock",
        "relation": "public.kbdiag_inj_lock",
        "wait_s": 37.3,
        "waiter_pid": 1045724
      }
    }
  ],
  "cause": null,
  "next": [
    {
      "kind": "verify",
      "command": "kbdiag session 1045715",
      "note": "what the blocking session is doing"
    }
  ]
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: a lock wait or idle in transaction over its threshold |
| 3 | UNKNOWN: no such session, or data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
