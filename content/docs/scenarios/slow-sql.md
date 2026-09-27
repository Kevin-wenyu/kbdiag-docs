---
title: "Find long-running SQL"
description: "Find a statement that has been running for a while and see what it is waiting on."
weight: 10
---

Captured on 2026-09-27 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `93bf65d` (static linux/amd64 binary). This is lab evidence, not production validation. PIDs, counts and timings belong to this capture only. A fault-injection script started `select pg_sleep(3600);`, a statement that only sleeps. It tests detection, not CPU or disk pressure.

kbdiag 2.0 has no slow-SQL threshold yet: a long statement is listed and sorted, but not a WARN on its own. It becomes a finding when it holds a transaction open too long (`txn`) or makes others wait for a lock (`locks`).

## 1. What is running?

```bash
~/kbdiag sessions
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:49+08:00)

connected: 4 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user    database  application            client
  2      esrep   esrep     internal_rwcmgr        192.168.105.10
  1      esrep   esrep     internal_rwcmgr        192.168.105.11
  1      system  test      kbdiag_inj_long_query  local

not idle: 1
  pid      user    database  application            client  state   xact  query  wait             sql
  1049328  system  test      kbdiag_inj_long_query  local   active  13s   13s    Timeout:PgSleep  select pg_sleep(3600);
EXIT_CODE=0
```

- `connected` counts the client sessions by user, database, application and client; walsenders and background processes are only counted (`--all` lists them).
- `not idle` lists the sessions doing something or holding a transaction open, longest transaction first. 1049328 has run `select pg_sleep(3600);` for 13 seconds. `query` is how long the current statement has been running; `wait` is what it waits on.
- The `sql` column is cut at 60 characters; `session <pid>` shows the full text.

## 2. What is it waiting on?

```bash
~/kbdiag session 1049328
echo EXIT_CODE=$?
```

```text
session  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:50+08:00)

session 1049328
  user         system
  database     test
  application  kbdiag_inj_long_query
  client       local
  type         client backend
  state        active  (for 14s)
  xact         14s
  query        14s
  wait         Timeout:PgSleep
  xid / xmin   - / 6353

sql
  select pg_sleep(3600);

waiting for: 0

blocking: 0

holds: 0
EXIT_CODE=0
```

`Timeout:PgSleep` says the statement is sleeping on purpose. It waits for nobody, blocks nobody and holds no lock worth showing (every transaction's own `virtualxid` lock is left out). For a real statement you would see `IO` (reading data), `Lock` (waiting for another session), or no wait event at all (running on CPU).

## 3. Is it one statement or many?

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:51+08:00)

not idle: 1
  wait             state   sessions  pids
  Timeout:PgSleep  active  1         1049328

not shown: 3 idle, 8 background
EXIT_CODE=0
```

`waits` groups the sessions that are doing something by wait event and state. One `Timeout:PgSleep` session means a single statement, not a pile-up; the idle sessions and idle background processes are only counted. When dozens of sessions share one wait event, that event is where to look.

## 4. Decide

Here the sleep is deliberate; there is nothing to tune. For a real statement, check its plan and the data it touches with the application owner. kbdiag does not cancel statements; if you decide to, use `select pg_cancel_backend(<pid>);` in `ksql`. The injected session was released afterwards and a follow-up check found none left.

[Continue with lock waits]({{< relref "/docs/scenarios/lock-waits" >}})
