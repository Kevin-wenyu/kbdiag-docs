---
title: "locks: lock waits"
description: "List lock waits and flag sessions waiting too long, with their direct blockers."
weight: 30
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `0a4d61e` (static linux/amd64 binary). This is lab evidence, not production validation. The lock wait in the examples was created by a fault-injection script: 364809 holds an exclusive lock on table `kbdiag_inj_lock` without committing, and 364818 waits for it. PIDs, counts and timings belong to this capture only.

## Usage

```text
kbdiag locks [--limit N] [--lock-wait-warn SECONDS] [--json]
```

| Option | Effect |
|---|---|
| `--limit N` | Show at most N rows; default 50, `0` for all |
| `--lock-wait-warn SECONDS` | WARN when waiting for a lock longer than this; default 10 |
| `--json` | Print JSON |

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}). `--limit` only affects what is shown; the verdict always covers every lock.

## A session waits for a lock

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:38:53+08:00)

[WARN] lock.waiting  会话 364818 等 public.kbdiag_inj_lock 的 AccessShareLock 已 14 秒，被 364809 挡住
  verify: kbdiag session 364809  # 看挡路的会话在干什么

lock.list: 2 rows
pid     locktype  relation                mode                 granted  wait_s  blocked_by
364809  relation  public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
364818  relation  public.kbdiag_inj_lock  AccessShareLock      false    13.8    [364809]
EXIT_CODE=1
```

- Only locks involved in a wait are listed: locks not yet granted, and the locks the blockers hold on the same object. With no waits the list is empty and the verdict OK.
- `blocked_by` lists the direct blockers, not the whole chain.
- Each waiting session gets one `lock.waiting` finding (in Chinese: who waits, on what, for how long, blocked by whom). Waits shorter than `--lock-wait-warn` are listed but not flagged.
- `wait_s` is an approximation: the time since the session's last state change.
- If the blocker is a prepared (two-phase) transaction, `blocked_by` shows `[0]`, since it belongs to no session; find it with [`kbdiag txn`]({{< relref "/docs/reference/txn" >}}) on the primary.

## Without monitoring privileges

Connected remotely as `kbdiag_ro`, which has no monitoring role, while the wait is still there:

```bash
PGPASSWORD=... ~/kbdiag locks --host 127.0.0.1 -U kbdiag_ro
echo EXIT_CODE=$?
```

```text
locks  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-24T04:41:05+08:00)

lock.list: 2 rows
pid     locktype  relation                mode                 granted  wait_s  blocked_by
367208  relation  public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
367217  relation  public.kbdiag_inj_lock  AccessShareLock      false    -       [367208]

redacted: lock.list.wait_s in 1 rows (insufficient_privilege)
EXIT_CODE=3
```

- The locks and who blocks whom are visible, but this account cannot see other sessions' timestamps, so `wait_s` is unknown and the threshold cannot be checked. The verdict is UNKNOWN, exit code 3.
- Granting the `sys_monitor` role restores the full picture.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
