---
title: "Investigate lock waits"
description: "Find who waits, follow the verify line to the blocker, decide, and confirm the waits are gone."
weight: 20
---

Captured on 2026-09-27 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `93bf65d` (static linux/amd64 binary). This is lab evidence, not production validation. PIDs, counts and timings belong to this capture only. A fault-injection script opened a transaction that took an `ACCESS EXCLUSIVE` lock on a test table and then sat idle, and a second session tried to read the table.

## 1. Who is waiting?

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:33+08:00)

[WARN] lock.waiting  session 1048829 has waited 13s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1048819
  verify: kbdiag session 1048819  # what the blocking session is doing

blockers: 1
  pid      blocks  holds
  1048819  1       public.kbdiag_inj_lock AccessExclusiveLock

waiting: 1
  pid      object                  wants            waited  blocked by
  1048829  public.kbdiag_inj_lock  AccessShareLock  13s     1048819
EXIT_CODE=1
```

- Session 1048829 has waited 13 seconds for `AccessShareLock` on `public.kbdiag_inj_lock`; the direct blocker is 1048819. Waits over 10 seconds are a WARN (`--lock-wait-warn` changes this).
- `blockers` comes first, because the first question is who is in the way. It shows 1048819 blocks one session and holds `AccessExclusiveLock` on the table. When one blocker holds up dozens of sessions, it is the top row.
- `waiting` lists each waiting session, longest wait first. The wait is measured from the waiter's last state change, so it can overstate the wait a little, never understate it.

## 2. What is the blocker doing?

Follow the `verify` line:

```bash
~/kbdiag session 1048819
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:34+08:00)

[WARN] lock.waiting  session 1048829 has waited 14s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1048819

session 1048819
  user         system
  database     test
  application  kbdiag_inj_lock_holder
  client       local
  type         client backend
  state        idle in transaction  (for 14s)
  xact         14s
  query        14s
  wait         -
  xid / xmin   6351 / -

last sql
  lock table kbdiag_inj_lock in access exclusive mode;

waiting for: 0

blocking: 1
  pid      object                  wants            waited
  1048829  public.kbdiag_inj_lock  AccessShareLock  14s

holds: 1
  object                  mode
  public.kbdiag_inj_lock  AccessExclusiveLock
EXIT_CODE=1
```

- The blocker is `idle in transaction`: its last statement was `lock table kbdiag_inj_lock in access exclusive mode;` and it has been waiting for the client for 14 seconds with the transaction still open. Nothing is running; the lock is held because nobody committed or rolled back.
- `blocking` shows who it holds up; `holds` shows the lock they want.
- If `waiting for` is not empty, the blocker is itself waiting: run `session` on its blocker in turn until you reach one that is not waiting. kbdiag shows one hop at a time.
- If a blocker is shown as `2PC`, it is a prepared (two-phase) transaction with no session; find it with `kbdiag txn` on the primary.

## 3. Decide and act

kbdiag does not end sessions. Confirm with the application owner what the transaction was for. Usually the application should commit or roll back; if it cannot, end the connection yourself, for example with `select pg_terminate_backend(1048819);` in `ksql`, after checking the PID still belongs to the same user and application. Ending the blocker rolls back its transaction.

In this lab run the injection script released the holder, which ended the transaction.

## 4. Confirm

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:36+08:00)

waiting: 0
EXIT_CODE=0
```

No waits, OK, exit 0. One clean sample only says the waits are gone now; if they come back, look for the application path that leaves transactions open.

[Back to scenarios]({{< relref "/docs/scenarios" >}}) · [locks reference]({{< relref "/docs/reference/locks" >}})
