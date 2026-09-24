---
title: "Find long-running SQL"
description: "Find a statement that has been running for a while and see what it is waiting on."
weight: 10
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `6803c61` (static linux/amd64 binary). This is lab evidence, not production validation. PIDs, counts and timings belong to this capture only. A fault-injection script started `select pg_sleep(3600);`, a statement that only sleeps. It tests detection, not CPU or disk pressure.

kbdiag 2.0 has no slow-SQL threshold yet: a long statement is listed and sorted, but not a WARN on its own. It becomes a finding when it holds a transaction open too long (`txn`) or makes others wait for a lock (`locks`).

## 1. What is running?

```bash
~/kbdiag sessions --active
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:14+08:00)

session.activity: 2 rows
pid     usename  datname  application_name       client_addr     backend_type    state   backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event     query
436010  system   test     kbdiag_inj_long_query  -               client backend  active  -            6101          9           9            9            Timeout          PgSleep        select pg_sleep(3600);
407405  esrep    -        node2                  192.168.105.11  walsender       active  -            -             -           -            10050.7      Activity         WalSenderMain  
EXIT_CODE=0
```

- `--active` shows only sessions whose state is `active`; the verdict still covers every session.
- Sessions are sorted by transaction age, longest first: 436010 has run `select pg_sleep(3600);` for 9 seconds. `query_age_s` is how long the current statement has been running.
- The `walsender` row is replication to the standby; it is always active and has no transaction, so it sorts after client sessions.

## 2. What is it waiting on?

```bash
~/kbdiag session 436010
echo EXIT_CODE=$?
```

```text
session  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:14+08:00)

lock.list: 1 rows
pid     locktype    relation  mode           granted  wait_s  blocked_by
436010  virtualxid  -         ExclusiveLock  true     -       []

session.activity: 1 rows
pid     usename  datname  application_name       client_addr  backend_type    state   backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
436010  system   test     kbdiag_inj_long_query  -            client backend  active  -            6101          9.5         9.5          9.5          Timeout          PgSleep     select pg_sleep(3600);
EXIT_CODE=0
```

`Timeout / PgSleep` says the statement is sleeping on purpose. It holds only its own `virtualxid` lock and blocks nobody. For a real statement you would see `IO` (reading data), `Lock` (waiting for another session), or no wait event at all (running on CPU).

## 3. Is it one statement or many?

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:15+08:00)

wait.summary: 9 rows
wait_event_type  wait_event           state   sessions  pids
Client           ClientRead           idle    3         [3294 179417 222736]
Activity         KshMain              idle    2         [3279 3280]
Activity         AutoVacuumMain       -       1         [3274]
Activity         BgWriterHibernate    -       1         [3272]
Activity         CheckpointerMain     -       1         [3271]
Activity         LogicalLauncherMain  -       1         [3281]
Activity         WalSenderMain        active  1         [407405]
Activity         WalWriterMain        -       1         [3273]
Timeout          PgSleep              active  1         [436010]
EXIT_CODE=0
```

`waits` groups every session by wait event and state. One `Timeout / PgSleep` session among idle clients and background processes means a single statement, not a pile-up. When dozens of sessions share one wait event, that event is where to look.

## 4. Decide

Here the sleep is deliberate; there is nothing to tune. For a real statement, check its plan and the data it touches with the application owner. kbdiag does not cancel statements; if you decide to, use `select pg_cancel_backend(<pid>);` in `ksql`. The injected session was released afterwards and a follow-up check found none left.

[Continue with lock waits]({{< relref "/docs/scenarios/lock-waits" >}})
