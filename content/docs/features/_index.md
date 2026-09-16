---
title: "Capabilities"
description: "Choose commands for health, replication, SQL, locks, maintenance and diagnosis."
weight: 20
---

Start with the question you need to answer. Examples assume installation at `~/kbdiag`; see the [user manual](../reference/) for all options.

## Health checks {#health}

**Is the database healthy, and what needs attention?**

- `status`: process state, connectivity, role and uptime.
- `check`: threshold-based findings; `check --os` adds host conformance checks.
- `report [file]`: a Markdown report assembled from existing checks.

```bash
~/kbdiag status
~/kbdiag check
~/kbdiag report inspection.md
```

Review WARN / FAIL findings, then choose a focused command. `report` writes a local file; it does not replace backups or continuous monitoring. Choose a new filename to avoid replacing an existing report.

→ [Run and interpret your first inspection](../get-started/)

## Replication and HA {#replication}

**What is the topology? Is replication behind? Are failover prerequisites met?**

- `cluster`: repmgr topology.
- `cluster ready`: failover readiness checks.
- `replication`: replication state and lag.

```bash
~/kbdiag cluster
~/kbdiag replication
~/kbdiag cluster ready
```

Primary and standby nodes expose different metrics. repmgr, node configuration and related processes determine the scope of cluster checks. Readiness checks do not perform a failover or replace a failover exercise.

## SQL and performance {#performance}

**What is slow now, which recorded statements consume time, and how has workload changed?**

| View | Command | Focus |
|---|---|---|
| Current activity | `perf slow`, `wait` | Active slow queries and waits |
| Accumulated statement statistics | `stmt` | Recorded SQL timing and calls |
| Query plan | `explain` | Plan structure and findings to investigate |
| Time interval | `workload` | Available historical workload evidence |

```bash
~/kbdiag perf slow
~/kbdiag stmt
~/kbdiag workload --from 1h --no-snapshot
```

Historical analysis depends on extensions or statistics views; missing records do not prove an absence of slow queries. `workload` prefers `sys_kwr`. Without it, the fallback uses rolling metrics from the last 15 minutes, not an arbitrary requested interval. When snapshots are insufficient, it may create an additional snapshot on a writable primary; `--no-snapshot` disables that behavior.

## Locks and sessions {#locks}

**Who is waiting, who may be blocking them, and what SQL is involved?**

```bash
~/kbdiag sessions
~/kbdiag locks wait
~/kbdiag locks hold
```

Inspect waiting and held locks, then use `sql <pid>` for the relevant session. Use a PID from current output; sessions can end between observations.

`kill` is an intervention: it cancels queries by default, while `--terminate` terminates sessions. Verify the session and business impact before use. It is not needed for a first inspection.

## Space and maintenance {#maintenance}

**Where is space used, and what can indexes and statistics tell me?**

```bash
~/kbdiag space
~/kbdiag idx
~/kbdiag advisor index
```

Use `obj <schema.table>` for object details, `colstat <schema.table>` for column statistics, and `perf bloat` / `perf vacuum` for related checks.

Interpret index usage and estimates with the observation window and workload in mind. `advisor index --fix` emits proposed SQL without executing it; review any suggested DROP or CREATE statements yourself.

## Diagnosis and incident capture {#diagnosis}

**How do the signals relate, and how can I preserve incident evidence?**

- `diagnose` / `diagnose --full`: correlate signals and produce recommendations.
- `advisor`: recommendations across indexes, vacuum, parameters and statistics.
- `snapshot [file]`: package sessions, locks, waits, performance data and some logs.

```bash
~/kbdiag diagnose
~/kbdiag advisor
~/kbdiag snapshot incident.tar.gz
```

Verify diagnoses against the underlying metrics. `snapshot` writes a local archive; it cannot restore a database. The current implementation masks single-quoted literals, not every possible sensitive value. Review the archive before sharing it.

## Script integration {#automation}

Most commands support `--format json`; `watch` does not. Judgment commands such as `check` return health verdicts directly. Most data-query commands do not return nonzero merely because of findings unless you use `--exit-code`. Usage and execution errors can still return nonzero.

```bash
~/kbdiag --format json check
```

Verify the behavior of the command you integrate. See [exit codes](../get-started/#exit-codes).

[Troubleshooting: slow SQL and lock waits]({{< relref "/docs/scenarios" >}})
