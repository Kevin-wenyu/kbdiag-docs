---
title: "txn: transactions"
description: "Who holds back the vacuum horizon: open transactions, prepared (two-phase) ones, and the oldest of them."
weight: 40
---

Captured on 2026-09-27 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `93bf65d` (static linux/amd64 binary). This is lab evidence, not production validation. The transactions in the examples were created by fault-injection scripts: two sessions idle in transaction (one holding a table lock), sessions waiting for locks, a `pg_sleep(3600)`, and `kbdiag_inj_2pc`, a prepared transaction that was neither committed nor rolled back. PIDs, counts and timings belong to this capture only.

## Usage

```text
kbdiag txn [--limit N] [--xact-warn SECONDS] [--prepared-warn SECONDS] [--json]
```

| Option | Effect |
|---|---|
| `--limit N` | Show at most N transactions; default 50, `0` for all |
| `--xact-warn SECONDS` | WARN when a transaction is older than this; default 300 |
| `--prepared-warn SECONDS` | WARN when a prepared transaction is older than this; default 900 |
| `--json` | Print JSON |

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}). `--limit` only affects what is shown; the findings always cover every transaction.

## Default output

```bash
~/kbdiag txn
echo EXIT_CODE=$?
```

```text
txn  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:18+08:00)

oldest xid: 6343  (1045715 xid, 1045724 xmin, 1046007 xmin, 1046088 xmin)

open transactions: 5
  pid      user    database  application                 state                xact  xid   xmin  sql
  1045715  system  test      kbdiag_inj_lock_holder      idle in transaction  31s   6343  -     lock table kbdiag_inj_lock in access exclusive mode;
  1045724  system  test      kbdiag_inj_lock_waiter      active               30s   -     6343  select count(*) from kbdiag_inj_lock;
  1045809  system  test      kbdiag_inj_idle_txn         idle in transaction  29s   6344  -     select txid_current() as kbdiag_last, pg_sleep(1);
  1046007  system  test      kbdiag_inj_prepared_waiter  active               25s   6347  6343  lock table kbdiag_inj_2pc in access exclusive mode;
  1046088  system  test      kbdiag_inj_long_query       active               25s   -     6343  select pg_sleep(3600);

prepared: 1
  gid             owner   database  age  xid
  kbdiag_inj_2pc  system  test      26s  6346
EXIT_CODE=0
```

- `oldest xid` is the oldest transaction id any session or prepared transaction holds, and who holds it. Here 1045715 has transaction id 6343, and three others have snapshots (`xmin`) taken while 6343 was running. VACUUM cannot remove row versions newer than this, so this line answers "who holds back the vacuum horizon". Ids are compared modulo 2^32, as the server does.
- `open transactions` lists sessions inside a transaction, meaning with a transaction start time, a transaction id or a snapshot xmin. The oldest transaction comes first. `xid` is assigned at the first write; a read-only transaction has only `xmin`.
- `prepared` lists every prepared transaction: gid, owner, database, age and xid. They belong to no session, so [`sessions`]({{< relref "/docs/reference/sessions" >}}) cannot show them.
- Nothing is past its default threshold, so the verdict is OK.

## WARN

With both thresholds lowered to 10 seconds:

```bash
~/kbdiag txn --xact-warn 10 --prepared-warn 10
echo EXIT_CODE=$?
```

```text
txn  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:21+08:00)

[WARN] txn.long  session 1045715 has had a transaction open for 34s, now idle in transaction
  verify: kbdiag session 1045715  # what it is running, which locks it holds, whether it blocks anyone

[WARN] txn.long  session 1045724 has had a transaction open for 34s, now active
  verify: kbdiag session 1045724  # what it is running, which locks it holds, whether it blocks anyone

[WARN] txn.long  session 1045809 has had a transaction open for 32s, now idle in transaction
  verify: kbdiag session 1045809  # what it is running, which locks it holds, whether it blocks anyone

[WARN] txn.long  session 1046007 has had a transaction open for 28s, now active
  verify: kbdiag session 1046007  # what it is running, which locks it holds, whether it blocks anyone

[WARN] txn.long  session 1046088 has had a transaction open for 28s, now active
  verify: kbdiag session 1046088  # what it is running, which locks it holds, whether it blocks anyone

[WARN] txn.prepared  two-phase transaction kbdiag_inj_2pc prepared 29s ago and not finished, holding back the vacuum horizon
  fix: ROLLBACK PREPARED 'kbdiag_inj_2pc'  # check with the application whether to commit (COMMIT PREPARED) or roll back; run it connected to database test, outside a transaction block

oldest xid: 6343  (1045715 xid, 1045724 xmin, 1046007 xmin, 1046088 xmin)

open transactions: 5
  pid      user    database  application                 state                xact  xid   xmin  sql
  1045715  system  test      kbdiag_inj_lock_holder      idle in transaction  34s   6343  -     lock table kbdiag_inj_lock in access exclusive mode;
  1045724  system  test      kbdiag_inj_lock_waiter      active               34s   -     6343  select count(*) from kbdiag_inj_lock;
  1045809  system  test      kbdiag_inj_idle_txn         idle in transaction  32s   6344  -     select txid_current() as kbdiag_last, pg_sleep(1);
  1046007  system  test      kbdiag_inj_prepared_waiter  active               28s   6347  6343  lock table kbdiag_inj_2pc in access exclusive mode;
  1046088  system  test      kbdiag_inj_long_query       active               28s   -     6343  select pg_sleep(3600);

prepared: 1
  gid             owner   database  age  xid
  kbdiag_inj_2pc  system  test      29s  6346
EXIT_CODE=1
```

- `txn.long`: one per transaction older than `--xact-warn`. The `verify` line leads to the session.
- `txn.prepared`: a prepared transaction older than `--prepared-warn`. It keeps its locks and holds back the vacuum horizon until someone commits or rolls it back. The `fix` line gives the statement; kbdiag only prints it. Its note says to confirm with the application whether to commit (`COMMIT PREPARED`) or roll back, and to run it connected to the transaction's database, outside a transaction block.
- If a gid contains control characters, the terminal shows it escaped and a copied statement would not match. In that case there is no `fix` line; the `verify` line says to take the raw gid from `--json`.
- Both are WARN, never FAIL. Their harm, table bloat and locks held for a long time, is still to come. The sessions they block now are reported by [`locks`]({{< relref "/docs/reference/locks" >}}).
- 300 and 900 seconds have no server-side counterpart. 300 can catch a normal batch job, so raise them on batch databases.
- At default thresholds a session idle in transaction for over 300 seconds is also reported by `sessions` as `session.idle_in_txn`. The two answer different questions.

## On a standby

```bash
~/kbdiag txn
echo EXIT_CODE=$?
```

```text
txn  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:20+08:00)

oldest xid: 6354  (599825 xmin)

open transactions: 1
  pid     user    database  application             state   xact  xid  xmin  sql
  599825  system  test      kbdiag_inj_lock_waiter  active  14s   -    6354  select pg_advisory_lock(424242);

txn.prepared: not_applicable  (a standby cannot see the primary's two-phase transactions: run kbdiag txn on the primary)
EXIT_CODE=0
```

A standby cannot see the primary's prepared transactions, so `txn.prepared` is `not_applicable`. That does not mean "none", and it does not affect the verdict. Run `txn` on the primary.

## Insufficient privilege

Connect as `kbdiag_ro`, which has no monitoring role:

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro txn
echo EXIT_CODE=$?
```

```text
txn  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:35:27+08:00)

oldest xid: 6343  (1045715 xid, 1045724 xmin, 1046007 xmin, 1046088 xmin)

open transactions: 5, 10 sessions hidden
  pid      user    database  application                 state  xact  xid   xmin  sql
  1045715  system  test      kbdiag_inj_lock_holder      ?      ?     6343  -     ?
  1045724  system  test      kbdiag_inj_lock_waiter      ?      ?     -     6343  ?
  1045809  system  test      kbdiag_inj_idle_txn         ?      ?     6344  -     ?
  1046007  system  test      kbdiag_inj_prepared_waiter  ?      ?     6347  6343  ?
  1046088  system  test      kbdiag_inj_long_query       ?      ?     -     6343  ?

prepared: 1
  gid             owner   database  age  xid
  kbdiag_inj_2pc  system  test      35s  6346
redacted: 15 rows of session.activity hide state, backend_type, client_addr, ages, wait, query (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- KingbaseES shows other sessions' transaction id and xmin to any account, so `oldest xid` and the open transactions are still found. Their state, age and SQL show `?`.
- Hidden sessions with neither an xid nor an xmin are only counted (`10 sessions hidden`). They are most likely idle, and they are not called transactions.
- The verdict is UNKNOWN, exit code 3. Grant `sys_monitor` to see everything.
- When session activity or the prepared transactions could not be collected, `oldest xid` says an older one may exist, or shows `unknown` if nothing was found.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: a long transaction or a long-pending prepared transaction |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
