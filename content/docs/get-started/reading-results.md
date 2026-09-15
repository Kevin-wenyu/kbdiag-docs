---
title: "Reading check results"
description: "Use an explicitly illustrative excerpt to understand verdicts, thresholds and next steps."
weight: 10
---

## Provenance {#provenance}

This is an **illustrative excerpt with invented values, written to match the current output format**. It is not captured from a test host and does not represent a complete inspection.

A real capture should record the tool version, database version, node role, timestamp, full command and exit code. 

```text
[OK] Connections: 4% (8/200)
[WARN] Waiting locks: 2
```

## Read each line {#interpretation}

- `Connections`: the example shows 8 connections out of 200, an integer percentage of 4%. An OK here does not mean all other checks passed.
- `Waiting locks`: the current code counts ungranted records in `sys_locks`. The value 2 counts lock records, **not necessarily two users or sessions**.
- An excerpt cannot establish the complete command's exit status. In a full inspection, WARN without FAIL makes `check` return 1; a FAIL makes it return 2.

## Next step {#next}

```bash
~/kbdiag locks wait
```

Inspect waiting relationships, sessions, SQL and the business context. This example cannot tell you which session should be terminated; do not run `kill` based on a count alone.

[Back to your first inspection]({{< relref "/docs/get-started" >}}#run-check)
