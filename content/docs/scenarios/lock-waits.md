---
title: "Investigate lock waits"
description: "Find who waits, follow the verify line to the blocker, decide, and confirm the waits are gone."
weight: 20
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `6803c61` (static linux/amd64 binary). This is lab evidence, not production validation. PIDs, counts and timings belong to this capture only. A fault-injection script opened a transaction that took an `ACCESS EXCLUSIVE` lock on a test table and then sat idle, and a second session tried to read the table.

## 1. Who is waiting?

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:02+08:00)

[WARN] lock.waiting  会话 435317 等 public.kbdiag_inj_lock 的 AccessShareLock 已 14 秒，被 435308 挡住
  verify: kbdiag session 435308  # 看挡路的会话在干什么

lock.list: 2 rows
pid     locktype  relation                mode                 granted  wait_s  blocked_by
435308  relation  public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
435317  relation  public.kbdiag_inj_lock  AccessShareLock      false    13.7    [435308]
EXIT_CODE=1
```

- Session 435317 has waited 14 seconds for `AccessShareLock` on `public.kbdiag_inj_lock`; the direct blocker is 435308. Waits over 10 seconds are a WARN (`--lock-wait-warn` changes this).
- `lock.list` shows both sides: 435308 holds `AccessExclusiveLock` (`granted true`), 435317 is not granted and `blocked_by` names 435308.
- `wait_s` is measured from the waiter's last state change, so it can overstate the wait a little, never understate it.

## 2. What is the blocker doing?

Follow the `verify` line:

```bash
~/kbdiag session 435308
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:02+08:00)

[WARN] lock.waiting  会话 435317 等 public.kbdiag_inj_lock 的 AccessShareLock 已 14 秒，被 435308 挡住
  verify: kbdiag session 435308  # 看挡路的会话在干什么

lock.list: 4 rows
pid     locktype       relation                mode                 granted  wait_s  blocked_by
435308  relation       public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
435308  transactionid  -                       ExclusiveLock        true     -       []
435308  virtualxid     -                       ExclusiveLock        true     -       []
435317  relation       public.kbdiag_inj_lock  AccessShareLock      false    14.3    [435308]

session.activity: 1 rows
pid     usename  datname  application_name        client_addr  backend_type    state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
435308  system   test     kbdiag_inj_lock_holder  -            client backend  idle in transaction  6099         -             14.3        14.3         14.3         Client           ClientRead  lock table kbdiag_inj_lock in access exclusive mode;
EXIT_CODE=1
```

- The blocker is `idle in transaction`: its last statement was `lock table kbdiag_inj_lock in access exclusive mode;` and it has been waiting for the client (`Client / ClientRead`) for 14 seconds with the transaction still open. Nothing is running; the lock is held because nobody committed or rolled back.
- The session report repeats the lock finding because the blocked waiter is part of this session's picture.
- If the blocker is itself waiting (its `blocked_by` is not empty), run `session` on its blocker in turn until you reach one that is not waiting. kbdiag shows one hop at a time.
- If `blocked_by` shows `[0]`, the blocker is a prepared (two-phase) transaction with no session; find it with `kbdiag txn` on the primary.

## 3. Decide and act

kbdiag does not end sessions. Confirm with the application owner what the transaction was for. Usually the application should commit or roll back; if it cannot, end the connection yourself, for example with `select pg_terminate_backend(435308);` in `ksql`, after checking the PID still belongs to the same user and application. Ending the blocker rolls back its transaction.

In this lab run the injection script released the holder, which ended the transaction.

## 4. Confirm

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:04+08:00)

lock.list: 0 rows
pid  locktype  relation  mode  granted  wait_s  blocked_by
EXIT_CODE=0
```

No waits, OK, exit 0. One clean sample only says the waits are gone now; if they come back, look for the application path that leaves transactions open.

[Back to scenarios]({{< relref "/docs/scenarios" >}}) · [locks reference]({{< relref "/docs/reference/locks" >}})
