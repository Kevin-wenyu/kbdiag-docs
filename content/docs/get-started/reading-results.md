---
title: "Read a real result"
description: "Real lab output of a WARN, line by line, in text and JSON."
weight: 10
---

Captured on 2026-09-27 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `93bf65d` (static linux/amd64 binary). This is lab evidence, not production validation. PIDs, counts and timings belong to this capture only. The idle-in-transaction session was created by a fault-injection script. The warning threshold was lowered to 5 seconds with `--idle-in-txn-warn 5` so the example did not have to wait the default 300.

## Command and output

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

## Line by line

- **First line:** the command (`sessions`), the verdict (`WARN`) and the context: server version, role (`primary`), `user@location` (`local` is the socket) and when the data was collected.
- **Finding:** `[WARN]`, then a stable id (`session.idle_in_txn`), then the symptom: session 1049818 has been idle in transaction for 9 seconds. Scripts should rely on the id and the JSON fields; the wording of a symptom may change.
- **`verify:`** the next command to run and why. Here: look at session 1049818 to see which locks it holds and whether it blocks anyone. A `fix:` line, when present, is a statement for you to review; kbdiag never runs it.
- **Data:** laid out for reading. `connected` counts the client sessions by user, database, application and client. `not idle` lists the ones doing something or holding a transaction open, longest transaction first. `-` is null; `?` would be a value this account may not see.
- The `esrep` row is repmgr's own query, caught while it ran. Idle sessions and background processes are only counted in the headings; `--all` lists them.
- **Exit code 1:** WARN, meaning nothing is broken yet but it will be if left alone. A FAIL (the application is already affected) would be 2, UNKNOWN 3.

## The same report in JSON

`--json` carries the same content with stable field names. This is the `findings` array of `~/kbdiag sessions --idle-in-txn-warn 5 --json`, taken a moment later:

```json
[
  {
    "id": "session.idle_in_txn",
    "level": "WARN",
    "symptom": "session 1049818 has been idle in transaction for 9s",
    "evidence": [
      {
        "probe_id": "session.activity",
        "fields": {
          "backend_xid": 6353,
          "pid": 1049818,
          "state": "idle in transaction",
          "state_age_s": 9.1
        }
      }
    ],
    "cause": null,
    "next": [
      {
        "kind": "verify",
        "command": "kbdiag session 1049818",
        "note": "which locks it holds, whether it blocks anyone"
      }
    ]
  }
]
```

The full report also has:

- `command`, `verdict` and `context`.
- `data`: each probe with its `status`, `columns`, `rows` and `truncated`. JSON keeps raw values (seconds, bytes, full SQL) and always carries every session, idle ones and background processes included. Here that is 12 rows, where the text lists 2.
- `redacted`: the fields the account was not allowed to see.

The exit code is the same as in text mode.

## What happened next

The injected session was released and a follow-up check found no test sessions left. In a real case, run the `verify` command and decide with the application owner whether the transaction should be committed, rolled back or the connection closed.

[Investigate lock waits]({{< relref "/docs/scenarios/lock-waits" >}}) · [Back to your first check]({{< relref "/docs/get-started" >}}#exit-codes)
