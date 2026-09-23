---
title: "status: instance overview"
description: "See version, role, uptime, connections, database sizes and downstream count."
weight: 60
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `0a4d61e` (static linux/amd64 binary). This is lab evidence, not production validation. Values belong to this capture only.

## Usage

```text
kbdiag status [--json]
```

No options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## On the primary

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:39:06+08:00)

inst.databases: 5 rows
datname   size_bytes
esrep     15614003
kingbase  15024179
mydb      14877187
security  14844419
test      340459571

inst.downstreams: 1 rows
downstreams
1

inst.info: 1 rows
version                                                       start_time                 uptime_s  connections  max_connections  superuser_reserved_connections  data_directory
KingbaseES V008R006C009B0014 on x86_64-pc-linux-gnu, comp...  2026-09-20T22:19:13+08:00  281992.5  5            100              3                               /home/kingbase/cluster/install/kingbase/data
EXIT_CODE=0
```

- `inst.info`: version, instance start time, uptime in seconds, connections and the connection limit. `connections` counts only backends connected to a database, not background processes, so it compares directly with `max_connections`.
- `inst.databases`: the size in bytes of each non-template database.
- `inst.downstreams`: how many downstreams this instance is sending WAL to (rows of `sys_stat_replication`). On the primary, 1 means one standby is connected.
- The role in the first line (primary / standby) comes from `sys_is_in_recovery()`.
- `status` reports facts and does not judge: once collected, it is OK.

## On the standby

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-24T04:39:07+08:00)

inst.databases: 5 rows
datname   size_bytes
esrep     15614003
kingbase  15024179
mydb      14877187
security  14844419
test      340459571

inst.downstreams: 1 rows
downstreams
0

inst.info: 1 rows
version                                                       start_time                 uptime_s  connections  max_connections  superuser_reserved_connections  data_directory
KingbaseES V008R006C009B0014 on x86_64-pc-linux-gnu, comp...  2026-09-23T15:44:58+08:00  46448.3   3            100              3                               /home/kingbase/cluster/install/kingbase/data
EXIT_CODE=0
```

- The role is standby; it has no cascaded downstream, so `downstreams` is 0.
- Long cells are cut in text output (ending in `...`); `--json` gives the full version string.

## Without privileges

When the account has no CONNECT privilege on a database, that database's `size_bytes` is empty and recorded in `redacted`. Sizes are not judged, so the verdict stays OK rather than UNKNOWN.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 3 | UNKNOWN: data not collected |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
