---
title: "sessions: list sessions"
description: "Who holds the connections and which sessions are doing something; flag long idle-in-transaction ones."
weight: 10
---

Captured on 2026-09-27 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `93bf65d` (static linux/amd64 binary). This is lab evidence, not production validation. The application sessions named `kbdiag_inj_*` were created by fault-injection scripts. PIDs, counts and timings belong to this capture only.

## Usage

```text
kbdiag sessions [--all] [--limit N] [--idle-in-txn-warn SECONDS] [--json]
```

| Flag | Effect |
|---|---|
| `--all` | List every session, including idle ones and background processes |
| `--limit N` | Show at most N rows, default 50; `0` shows all |
| `--idle-in-txn-warn SECONDS` | WARN when a session is idle in transaction longer than this, default 300 |
| `--json` | Print the report as JSON |

Connection flags `--host`, `-p`, `-d`, `-U` and `--timeout` are global. Defaults: local socket in `/tmp`, port 54321, database `test`, user `system`. The password comes from `PGPASSWORD` or `~/.pgpass`. The connection runs read-only transactions and sets `lock_timeout`.

`--all` and `--limit` only change what is displayed. The summary and the findings always cover every session, so a session that is not shown can still raise a WARN.

## Default output

Several injected sessions are open: a table lock held idle in transaction and a reader waiting for it, a second idle-in-transaction session, a session waiting on a prepared transaction, and a `pg_sleep(3600)`.

```bash
~/kbdiag sessions
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:17+08:00)

connected: 8 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user    database  application                 client
  2      esrep   esrep     internal_rwcmgr             192.168.105.10
  1      esrep   esrep     internal_rwcmgr             192.168.105.11
  1      system  test      kbdiag_inj_idle_txn         local
  1      system  test      kbdiag_inj_lock_holder      local
  1      system  test      kbdiag_inj_lock_waiter      local
  1      system  test      kbdiag_inj_long_query       local
  1      system  test      kbdiag_inj_prepared_waiter  local

not idle: 5
  pid      user    database  application                 client  state                xact  query  wait             sql
  1045715  system  test      kbdiag_inj_lock_holder      local   idle in transaction  30s   30s    -                lock table kbdiag_inj_lock in access exclusive mode;
  1045724  system  test      kbdiag_inj_lock_waiter      local   active               30s   30s    Lock:relation    select count(*) from kbdiag_inj_lock;
  1045809  system  test      kbdiag_inj_idle_txn         local   idle in transaction  28s   27s    -                select txid_current() as kbdiag_last, pg_sleep(1);
  1046007  system  test      kbdiag_inj_prepared_waiter  local   active               25s   25s    Lock:relation    lock table kbdiag_inj_2pc in access exclusive mode;
  1046088  system  test      kbdiag_inj_long_query       local   active               24s   24s    Timeout:PgSleep  select pg_sleep(3600);
EXIT_CODE=0
```

- `connected:` answers "who holds the connections". Client sessions are counted by user, database, application and client, leaving out kbdiag's own connection. Walsenders and background processes are only counted in the heading. `local` is the Unix socket.
- `not idle:` lists the client sessions that are doing something or hold a transaction open: `active`, `idle in transaction` and the like. Idle sessions and background processes are not listed; `--all` lists them.
- Rows are sorted by transaction age, longest first. Sessions without a transaction come last, then by PID.
- `xact` is the transaction age and `query` the age of the current (or last) statement. `wait` is the wait event as `type:event`. `sql` is cut to 60 characters; [`session <pid>`]({{< relref "/docs/reference/session" >}}) shows it in full. `-` means null.
- The two idle-in-transaction sessions have been so for about 30 seconds, below the default 300, so the verdict is OK.

## A WARN

Only the idle-in-transaction session is left, and the threshold is lowered to 5 seconds so the example does not have to wait 300:

```bash
~/kbdiag sessions --idle-in-txn-warn 5
echo EXIT_CODE=$?
```

```text
sessions  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:37:04+08:00)

[WARN] session.idle_in_txn  session 1049818 has been idle in transaction for 9s
  verify: kbdiag session 1049818  # which locks it holds, whether it blocks anyone

connected: 4 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user    database  application          client
  2      esrep   esrep     internal_rwcmgr      192.168.105.10
  1      esrep   esrep     internal_rwcmgr      192.168.105.11
  1      system  test      kbdiag_inj_idle_txn  local

not idle: 2
  pid      user    database  application          client          state                xact  query  wait  sql
  1049818  system  test      kbdiag_inj_idle_txn  local           idle in transaction  11s   10s    -     select txid_current() as kbdiag_last, pg_sleep(1);
  179417   esrep   esrep     internal_rwcmgr      192.168.105.10  active               0s    0s     -     SELECT n.node_id, n.type, n.upstream_node_id, n.node_name...
EXIT_CODE=1
```

- One finding per session over the threshold. The `verify` line gives the next command to run.
- The `esrep` row is repmgr's own query, caught while it ran.
- Exit code 1 means at least one WARN.

Idle in transaction for 5 minutes is a fault whatever the application: a pool that leaked a connection, or a missing commit. 300 seconds filters out noise; it is not a capacity line. Raise it if DBAs routinely hold transactions open by hand. [`txn`]({{< relref "/docs/reference/txn" >}}) reports the same session as a long transaction at the same default. The two findings answer different questions ("it sits idle" and "its transaction is long"), so both stay.

## Who holds the connections

When [`status`]({{< relref "/docs/reference/status" >}}) reports that ordinary users can no longer connect, its `verify` line points here. A fault-injection script filled every connection ordinary users may open:

```bash
~/kbdiag sessions
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:38:17+08:00)

connected: 96 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user       database  application      client
  93     kbdiag_ro  test      kbdiag_inj_conn  127.0.0.1
  2      esrep      esrep     internal_rwcmgr  192.168.105.10
  1      esrep      esrep     internal_rwcmgr  192.168.105.11

not idle: 0
EXIT_CODE=0
```

The summary shows the pile-up at once: 93 idle sessions of `kbdiag_ro` from `127.0.0.1`, application `kbdiag_inj_conn`. They are idle, so `not idle` is empty.

## Fewer rows

```bash
~/kbdiag sessions --limit 2
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:20+08:00)

connected: 8 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user    database  application                 client
  2      esrep   esrep     internal_rwcmgr             192.168.105.10
  1      esrep   esrep     internal_rwcmgr             192.168.105.11
  1      system  test      kbdiag_inj_idle_txn         local
  1      system  test      kbdiag_inj_lock_holder      local
  1      system  test      kbdiag_inj_lock_waiter      local
  1      system  test      kbdiag_inj_long_query       local
  1      system  test      kbdiag_inj_prepared_waiter  local

not idle: 5
  pid      user    database  application             client  state                xact  query  wait           sql
  1045715  system  test      kbdiag_inj_lock_holder  local   idle in transaction  33s   33s    -              lock table kbdiag_inj_lock in access exclusive mode;
  1045724  system  test      kbdiag_inj_lock_waiter  local   active               33s   33s    Lock:relation  select count(*) from kbdiag_inj_lock;
... 3 more rows not shown (use --limit 0 to show all)
EXIT_CODE=0
```

`--limit` cuts the `not idle` list (and the rows in `--json`); the last line says how many are not shown. The summary and the findings still cover every session.

## Every session

```bash
~/kbdiag sessions --all
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:46+08:00)

connected: 3 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user   database  application      client
  2      esrep  esrep     internal_rwcmgr  192.168.105.10
  1      esrep  esrep     internal_rwcmgr  192.168.105.11

all: 11
  pid     user    database  application          client          type                          state   xact  query  wait                    sql
  3271    -       -         check pointer        -               checkpointer                  -       -     -      -                       -
  3272    -       -         background flush     -               background writer             -       -     -      -                       -
  3273    -       -         wal flush            -               walwriter                     -       -     -      -                       -
  3274    -       -         auto vacuum          -               autovacuum launcher           -       -     -      -                       -
  3279    system  kingbase  ksh writer           -               ksh writer                    idle    -     2s     -                       select pg_catalog.metric_update_timer();
  3280    system  -         sys_ksh collector    -               ksh collector                 idle    -     -      -                       -
  3281    system  -         logical replication  -               logical replication launcher  -       -     -      -                       -
  3294    esrep   esrep     internal_rwcmgr      192.168.105.10  client backend                idle    -     2s     -                       SELECT n.node_id as nodeId, n.type as nodeType, n.upstrea...
  179417  esrep   esrep     internal_rwcmgr      192.168.105.10  client backend                idle    -     2s     -                       SELECT pg_catalog.pg_is_in_recovery()
  759699  esrep   esrep     internal_rwcmgr      192.168.105.11  client backend                idle    -     2s     -                       SELECT state,sync_state FROM pg_stat_replication where ap...
  903372  esrep   -         node2                192.168.105.11  walsender                     active  -     -      Activity:WalSenderMain  -
EXIT_CODE=0
```

`--all` lists idle sessions and background processes too, and adds a `type` column (`backend_type`). The walsender is the replication connection to the standby.

## Insufficient privilege

Connect as `kbdiag_ro`, an account without a monitoring role, while the injected sessions are still there:

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro sessions
echo EXIT_CODE=$?
```

```text
sessions  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:35:25+08:00)

connected: 1 walsender, 15 hidden
  count  user    database  application                 client
  3      esrep   esrep     internal_rwcmgr             ?
  1      -       -         auto vacuum                 ?
  1      -       -         background flush            ?
  1      -       -         check pointer               ?
  1      -       -         wal flush                   ?
  1      system  -         logical replication         ?
  1      system  -         sys_ksh collector           ?
  1      system  kingbase  -                           ?
  1      system  test      kbdiag_inj_idle_txn         ?
  1      system  test      kbdiag_inj_lock_holder      ?
  1      system  test      kbdiag_inj_lock_waiter      ?
  1      system  test      kbdiag_inj_long_query       ?
  1      system  test      kbdiag_inj_prepared_waiter  ?

not idle: 0 visible, 15 hidden
redacted: 15 rows of session.activity hide state, backend_type, client_addr, ages, wait, query (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- This account cannot see the state, type, client address, times, wait event or SQL of other users' sessions. It cannot tell whether a session is working, idle or a background process, so none is called idle: all 15 are `hidden`, and they are still counted in the summary by user, database and application.
- `?` is a value this account may not see; `-` is null.
- The sessions cannot be judged, so the verdict is UNKNOWN with exit code 3, not OK. The `redacted` line names the hidden columns and the fix: grant `sys_monitor`.
- A session that turns off `track_activities` for itself (`SET` or `ALTER ROLE ... SET`) shows the state `disabled`. It is still listed, but its times show `?`: the server keeps old values. It also makes the verdict UNKNOWN, with the reason `track_activities_off`.

## JSON

`--json` always carries every session, idle ones and background processes included, with raw values: times in seconds and the full SQL. See [Read a real result]({{< relref "/docs/get-started/reading-results" >}}) for its shape.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: a session idle in transaction too long |
| 3 | UNKNOWN: some sessions not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
