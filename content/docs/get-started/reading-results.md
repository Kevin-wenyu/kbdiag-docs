---
title: "Read a real result"
description: "Real lab output of a WARN, line by line, in text and JSON."
weight: 10
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `6803c61` (static linux/amd64 binary). This is lab evidence, not production validation. PIDs, counts and timings belong to this capture only. The idle-in-transaction session was created by a fault-injection script; the warning threshold was lowered to 5 seconds with `--idle-in-txn-warn 5` so the example did not have to wait the default 300.

## Command and output

```bash
~/kbdiag sessions --idle-in-txn-warn 5 --limit 5
echo EXIT_CODE=$?
```

```text
sessions  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:28+08:00)

[WARN] session.idle_in_txn  会话 436492 处于 idle in transaction 已 9 秒
  verify: kbdiag session 436492  # 看它持有哪些锁、有没有挡住别人

session.activity: 5 rows
pid     usename  datname  application_name     client_addr  backend_type         state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event        query
436492  system   test     kbdiag_inj_idle_txn  -            client backend       idle in transaction  6101         -             11.1        10.1         9.1          Client           ClientRead        select txid_current() as kbdiag_last, pg_sleep(1);
3271    -        -        check pointer        -            checkpointer         -                    -            -             -           -            -            Activity         CheckpointerMain  
3272    -        -        background flush     -            background writer    -                    -            -             -           -            -            Activity         BgWriterMain      
3273    -        -        wal flush            -            walwriter            -                    -            -             -           -            -            Activity         WalWriterMain     
3274    -        -        auto vacuum          -            autovacuum launcher  -                    -            -             -           -            -            Activity         AutoVacuumMain    
... 7 more rows not shown (use --limit 0 to show all)
EXIT_CODE=1
```

## Line by line

- **First line:** the command (`sessions`), the verdict (`WARN`) and the context: server version, role (`primary`), `user@location` (`local` is the socket) and when the data was collected.
- **Finding:** `[WARN]`, then a stable id (`session.idle_in_txn`), then the symptom: session 436492 has been idle in transaction for 9 seconds. Symptoms are written in Chinese; the id and fields are the stable part for scripts.
- **`verify:`** the next command to run and why. Here: look at session 436492 to see which locks it holds and whether it blocks anyone. A `fix:` line, when present, is a statement for you to review; kbdiag never runs it.
- **Data:** one table per probe, named by its id (`session.activity`). `-` is null. Sessions are sorted by transaction age, so the idle-in-transaction session comes first; background processes follow because they are part of the list.
- **Truncation:** `--limit 5` showed 5 rows and hid 7. Findings still cover every row, so a problem in a hidden row still sets the verdict.
- **Exit code 1:** WARN. A FAIL would be 2, UNKNOWN 3.

## The same report in JSON

`--json` carries the same content with stable field names. This excerpt is the `findings` array of `~/kbdiag sessions --idle-in-txn-warn 5 --limit 2 --json`, taken a moment later:

```json
[
  {
    "id": "session.idle_in_txn",
    "level": "WARN",
    "symptom": "会话 436492 处于 idle in transaction 已 10 秒",
    "evidence": [
      {
        "probe_id": "session.activity",
        "fields": {
          "backend_xid": 6101,
          "pid": 436492,
          "state": "idle in transaction",
          "state_age_s": 9.6
        }
      }
    ],
    "cause": null,
    "next": [
      {
        "kind": "verify",
        "command": "kbdiag session 436492",
        "note": "看它持有哪些锁、有没有挡住别人"
      }
    ]
  }
]
```

The full report also has `command`, `verdict`, `context`, `data` (each probe with `status`, `columns`, `rows` and `truncated`) and `redacted`, the list of fields the account was not allowed to see. The exit code is the same as in text mode.

## What happened next

The injected session was released and a follow-up check found no test sessions left. In a real case, run the `verify` command and decide with the application owner whether the transaction should be committed, rolled back or the connection closed.

[Investigate lock waits]({{< relref "/docs/scenarios/lock-waits" >}}) · [Back to your first check]({{< relref "/docs/get-started" >}}#exit-codes)
