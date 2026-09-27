---
title: "locks: lock waits"
description: "Who blocks whom: the blockers first, then every session waiting for a lock, how long, and why."
weight: 30
---

Captured on 2026-09-27 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `93bf65d` (static linux/amd64 binary). This is lab evidence, not production validation. The lock waits were created by fault-injection scripts. On the primary, 1045715 holds an exclusive lock on table `kbdiag_inj_lock` idle in transaction and 1045724 waits for it. A prepared (two-phase) transaction holds a lock on `kbdiag_inj_2pc`, and 1046007 waits for that. PIDs, counts and timings belong to this capture only.

## Usage

```text
kbdiag locks [--limit N] [--lock-wait-warn SECONDS] [--json]
```

| Option | Effect |
|---|---|
| `--limit N` | Show at most N waiting sessions; default 50, `0` for all |
| `--lock-wait-warn SECONDS` | WARN when waiting for a lock longer than this; default 10 |
| `--json` | Print JSON |

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}). `--limit` only cuts the `waiting` list; the findings always cover every wait.

## Sessions waiting for locks

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:17+08:00)

[WARN] lock.waiting  session 1045724 has waited 30s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1045715
  verify: kbdiag session 1045715  # what the blocking session is doing

[WARN] lock.waiting  session 1046007 has waited 25s for AccessExclusiveLock on public.kbdiag_inj_2pc, blocked by an uncommitted two-phase transaction
  verify: kbdiag txn  # the blocker is an uncommitted two-phase transaction: its gid and how long it has been pending

blockers: 2
  pid      blocks  holds
  2PC      1       public.kbdiag_inj_2pc RowExclusiveLock
  1045715  1       public.kbdiag_inj_lock AccessExclusiveLock

waiting: 2
  pid      object                  wants                waited  blocked by
  1045724  public.kbdiag_inj_lock  AccessShareLock      30s     1045715
  1046007  public.kbdiag_inj_2pc   AccessExclusiveLock  25s     2PC
EXIT_CODE=1
```

- `blockers` comes first, because the first question in an incident is who is blocking. One blocker often holds up dozens of sessions, so they are sorted by how many sessions they block. `holds` is what the blocker holds on the objects its waiters want.
- A prepared transaction belongs to no session, so it is shown as `2PC`. Its finding says so and points at [`kbdiag txn`]({{< relref "/docs/reference/txn" >}}), which gives its gid and age.
- A blocker that is itself waiting is marked `(queued ahead for ...)`: the server counts a conflicting session queued earlier as a blocker too.
- `waiting` lists every session waiting for a lock, longest wait first. `blocked by` names the direct blockers only. For a longer chain, run [`session`]({{< relref "/docs/reference/session" >}}) on the blocker in turn.
- Each waiting session over `--lock-wait-warn` gets one `lock.waiting` finding. Shorter waits are listed but not flagged.
- `waited` is measured from the waiter's last state change: V8R6 has no lock-wait start time. It can overstate the wait a little, never understate it.

A 10-second lock wait is already an incident for OLTP but can be normal for a batch job, so it is a WARN, not a FAIL. 10 seconds filters out passing row-lock contention. Batch databases may want it higher.

With no waits:

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:43+08:00)

waiting: 0
EXIT_CODE=0
```

## On a standby

A session-level advisory lock, taken on the standby:

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  WARN  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:19+08:00)

[WARN] lock.waiting  session 599825 has waited 14s for advisory lock, blocked by 599816
  verify: kbdiag session 599816  # what the blocking session is doing

blockers: 1
  pid     blocks  holds
  599816  1       advisory ExclusiveLock

waiting: 1
  pid     object    wants          waited  blocked by
  599825  advisory  ExclusiveLock  14s     599816
EXIT_CODE=1
```

A lock with no table, such as an advisory lock, shows its lock type as the object.

## Insufficient privilege

Connect as `kbdiag_ro`, which has no monitoring role, while the waits on the primary are still there:

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro locks
echo EXIT_CODE=$?
```

```text
locks  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:35:26+08:00)

blockers: 2
  pid      blocks  holds
  2PC      1       public.kbdiag_inj_2pc RowExclusiveLock
  1045715  1       public.kbdiag_inj_lock AccessExclusiveLock

waiting: 2
  pid      object                  wants                waited  blocked by
  1045724  public.kbdiag_inj_lock  AccessShareLock      ?       1045715
  1046007  public.kbdiag_inj_2pc   AccessExclusiveLock  ?       2PC
redacted: 2 rows of lock.list hide wait (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- The locks and who blocks whom are visible. This account cannot see other sessions' timestamps, so the waits show `?` and the threshold cannot be checked. The verdict is UNKNOWN, exit code 3.
- Grant `sys_monitor` to see everything.

## JSON

`--json` lists the lock rows of the waiting sessions, plus the blockers' locks on the same objects: `pid`, `locktype`, `relation`, `mode`, `granted`, `wait_s` and `blocked_by`. `blocked_by` keeps the server's raw list: a prepared transaction appears as `0`.

## Limits

- Parallel query workers have their own PIDs and lock rows, so one waiting parallel query may count as several blocked sessions.
- Several advisory locks of one blocker are listed together in its `holds`, since only the lock type is compared.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: a session waited for a lock too long |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
