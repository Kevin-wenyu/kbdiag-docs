---
title: "Investigate lock waits"
description: "Verify blockers, inspect transactions and confirm recovery."
weight: 20
---

Captured on 2026-09-16 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `dist/kbdiag` from source commit `3bea0be`. This is lab evidence, not production validation. PIDs, counts and timings belong to this capture only.

## 1. Inspect waiting relationships

```bash
~/kbdiag locks wait -v --no-color --exit-code
```

Save output and exit status, then inspect current sessions with `~/kbdiag sql <WAIT_PID>` and `~/kbdiag sql <BLOCK_PID>`. PIDs can disappear or be reused: recheck user, application and SQL before acting.

## 2. Real lab output

Two transactions updated the same row in a dedicated table. The holder paused for 28 seconds and rolled back; the waiter had a 35-second statement timeout and also rolled back after completion. This tests one row-update conflict, not a deadlock. SQL columns below retain the tool's truncation.

```text
==> Waiting locks
[WARN]  Waiting locks: 1 blocked session(s) (longest 6s, showing top 10)
[OK]    Long lock waits: none > 60s

WAIT_PID  WAIT_USER  BLOCK_PID  BLOCK_USER  LOCKTYPE       MODE       WAIT     WAIT_QUERY                                                                                            BLOCK_QUERY
81518     system     81440      system      transactionid  ShareLock  0:00:06  SET application_name='kbdiag_docs_waiter'; SET statement_timeout='35000'; BEGIN; UPDATE kbdiag_docs_  SET application_name='kbdiag_docs_holder'; BEGIN; UPDATE kbdiag_docs_20260916.lock_demo SET value=1 

PROCESS_EXIT=1
```
Independent system-view evidence:

```text
pid|application_name|state|wait_event_type|wait_event
81440|kbdiag_docs_holder|active|Timeout|PgSleep
81518|kbdiag_docs_waiter|active|Lock|transactionid
(2 rows)
pid|locktype|mode|granted
81518|transactionid|ShareLock|f
(1 row)

PROCESS_EXIT=0
```

## 3. Interpret the result

- `WAIT_PID=81518` is waiting and `BLOCK_PID=81440` holds the matching lock. This pair was verified in this controlled case only.
- `transactionid / ShareLock` means waiting for the related transaction; it does not mean a whole table is held in ShareLock mode.
- `WAIT` is elapsed time since query start, not precise lock-wait duration.
- Any wait produces WARN; no wait exceeding the default 60 seconds can still produce an OK long-wait line. These are different checks.
- Counts come from joined lock rows. Complex cases may produce multiple rows per session; do not equate them with affected users.
- With `--exit-code`, this sample returns 1. `PROCESS_EXIT` is capture-script metadata.

## 4. Act and verify

Confirm with the owning application whether the transaction should continue, commit or roll back. Do not terminate a session merely because its PID appears. `kbdiag kill <PID>` cancels the current statement by default; `--terminate` ends the connection. Cancellation does not guarantee that the transaction ends or every lock is released, especially for idle-in-transaction sessions.

In this experiment the holder rolled back voluntarily. Both transactions exited, the original row remained `id=1, value=0`, the dedicated table and schema were removed, and test-session and schema counts were both zero.

After a real intervention, run `locks wait` again and check application recovery and transaction state. Current waits and cumulative deadlock statistics answer different questions; this experiment neither generated deadlocks nor reset their statistics.
