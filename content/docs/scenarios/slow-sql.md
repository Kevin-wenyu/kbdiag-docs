---
title: "Find running slow SQL"
description: "Find a running query and verify what it is waiting for."
weight: 10
---

Captured on 2026-09-16 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `dist/kbdiag` from source commit `3bea0be`. This is lab evidence, not production validation. PIDs, counts and timings belong to this capture only.

## 1. Find candidate queries

```bash
~/kbdiag perf slow -v --no-color --exit-code
rc=$?
printf 'EXIT_CODE=%s\n' "$rc"
```

The default filter selects active queries running longer than 5 seconds; adjust `KB_SLOW_THRESHOLD` if needed. This is not historical slow-query logging. Short or completed queries may be absent.

## 2. Compare real output

A bounded `pg_sleep(22)` session tested detection, without simulating CPU or disk pressure. `PROCESS_EXIT` is recorded by the capture script, not printed by kbdiag.

```text
==> Slow queries (running > 5s)
[WARN]  Slow queries: 1 running > 5s
PID    USER    DURATION  CLIENT_ADDR  QUERY
81070  system  0:00:09   -            SET application_name='kbdiag_docs_slow'; SELECT pg_sleep(22);

PROCESS_EXIT=1
```
Independent system-view check:

```text
pid|application_name|state|wait_event_type|wait_event|query
81070|kbdiag_docs_slow|active|Timeout|PgSleep|SET application_name='kbdiag_docs_slow'; SELECT pg_sleep(22);
(1 row)

PROCESS_EXIT=0
```

## 3. Inspect and decide

Use `~/kbdiag sql <PID>` with a PID from your current sample. Check the user, SQL, state and wait event; do not reuse this page's PID. The command also attempts plain EXPLAIN, not EXPLAIN ANALYZE. A completed session, multiple statements or permissions may make the plan unavailable.

Here, `Timeout / PgSleep` matches deliberate sleeping and does not justify adding an index. For a real workload, investigate locks, plans, data volume and call frequency. Without `--exit-code`, finding a slow query does not guarantee a nonzero status; this example explicitly enables it and returns 1.

## 4. Verify completion

The test finished naturally and a subsequent check found zero test sessions. After a real intervention, sample again and check application latency. A single empty list does not establish that an intermittent issue is resolved.

[Continue with lock waits]({{< relref "/docs/scenarios/lock-waits" >}})
