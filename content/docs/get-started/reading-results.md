---
title: "Read a real health check"
description: "Real lab output, exit status and next steps."
weight: 10
---

Captured on 2026-09-16 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `dist/kbdiag` from source commit `3bea0be`. This is lab evidence, not production validation. PIDs, counts and timings belong to this capture only.

## Command and complete output

```bash
KB_DB=test ~/kbdiag check --no-color
rc=$?
printf "EXIT_CODE=%s\n" "$rc"
```

```text
==> Health check
[OK]    Connections: 12% (12/100)
[OK]    Long transactions: none
[OK]    Waiting locks: none
[WARN]  Archiver: 1407 failed file(s)
[OK]    Autovacuum backlog: none
[OK]    Buffer hit rate: 99.6%
[OK]    Checkpoint pressure: 0 requested checkpoints
[OK]    Temp file usage: 0 bytes
[OK]    Deadlocks: none
[OK]    Replication slot lag: 0bytes
[OK]    BGWriter pressure: 0% backend writes
[OK]    XID age: 4717
[OK]    oldest active transaction: 0s
[WARN]  WAL archiving: failing (1407 failures, last: 2026-09-16 07:05:31.025697+08) — run: kbdiag backup
EXIT_CODE=1
```

## Interpretation

- Connections are 12/100. An OK connection check does not cover archiving or other checks.
- No waiting locks were found. When present, `check` counts ungranted lock records, not unique sessions.
- The two archive warnings are related signals: do not add the two counts of 1407. Failure counters include history; compare the last failure with subsequent successes to assess current failure.
- The complete command returned 1: WARN findings, no FAIL. A FAIL makes `check` return 2.

## Next step

Run `~/kbdiag backup`, then inspect the archive command, destination capacity, permissions and database logs. Do not reset statistics merely to clear a warning. This capture does not resolve or validate the archiving issue.

[Investigate lock waits]({{< relref "/docs/scenarios/lock-waits" >}}) · [Back to first inspection]({{< relref "/docs/get-started" >}}#run-check)

## Follow-up repair

On 2026-09-16, the repository SSH host key was independently verified and updated, and the backup check connection port/user were corrected. `sys_rman check` confirmed newly archived WAL. Both pending queues were zero; the primary had archived 35 WAL segments while historical failures remained 1422. Statistics were not reset. The sample above preserves the pre-repair state; this was not a full restore drill.
