---
title: "status: instance overview"
description: "See version, role, uptime, connections, database sizes and downstream count."
weight: 60
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `6803c61` (static linux/amd64 binary). This is lab evidence, not production validation. Values belong to this capture only.

## Usage

```text
kbdiag status [--conn-warn PCT] [--conn-fail PCT] [--json]
```

`--conn-warn` / `--conn-fail` set the connection thresholds as a percentage of the connections ordinary users may open (`max_connections` minus `superuser_reserved_connections`); defaults 80 and 100. Both must be positive, and `--conn-fail` must not be below `--conn-warn`. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## On the primary

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T07:32:08+08:00)

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
KingbaseES V008R006C009B0014 on x86_64-pc-linux-gnu, comp...  2026-09-20T22:19:13+08:00  292374.4  5            100              3                               /home/kingbase/cluster/install/kingbase/data
EXIT_CODE=0
```

- `inst.info`: version, instance start time, uptime in seconds, connections and the connection limit. `connections` counts only backends connected to a database, not background processes, so it compares directly with `max_connections`.
- `inst.databases`: the size in bytes of each non-template database.
- `inst.downstreams`: how many downstreams this instance is sending WAL to (rows of `sys_stat_replication`). On the primary, 1 means one standby is connected.
- The role in the first line (primary / standby) comes from `sys_is_in_recovery()`.
- The only judgment is on connections: below 80% of the usable connections there is no finding and the verdict is OK.

## On the standby

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-24T07:32:08+08:00)

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
KingbaseES V008R006C009B0014 on x86_64-pc-linux-gnu, comp...  2026-09-23T15:44:58+08:00  56830.3   4            100              3                               /home/kingbase/cluster/install/kingbase/data
EXIT_CODE=0
```

- The role is standby; it has no cascaded downstream, so `downstreams` is 0.
- Long cells are cut in text output (ending in `...`); `--json` gives the full version string.

## Connections nearing the limit

The example below was created by a fault-injection script that opens idle sessions as an ordinary account until no usable connection is left. kbdiag, connected as `system`, still gets in through the superuser reserve.

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  FAIL  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T07:32:12+08:00)

[FAIL] inst.connections  连接已用 98 个，普通用户可用 97 个（max_connections 100 减去超级用户保留 3），占 101%
  verify: kbdiag sessions --limit 0  # 看连接是谁占的：按 usename、application_name、client_addr 看有没有扎堆

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
KingbaseES V008R006C009B0014 on x86_64-pc-linux-gnu, comp...  2026-09-20T22:19:13+08:00  292378.9  98           100              3                               /home/kingbase/cluster/install/kingbase/data
EXIT_CODE=2
```

- Usable connections are 100 − 3 = 97. At 80% (78 connections) the finding is WARN; at 100% it is FAIL. Here 98 are in use, 101%, so ordinary users can no longer connect.
- The `verify` line points to `sessions --limit 0`: look for a pile-up by user, application or client address.
- To test a threshold on a quiet instance, scale it down, e.g. `--conn-warn 1`.

## Without privileges

When the account has no CONNECT privilege on a database, that database's `size_bytes` is empty and recorded in `redacted`. Sizes are not judged, so the verdict stays OK rather than UNKNOWN.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: connections at or above `--conn-warn` |
| 2 | FAIL: connections at or above `--conn-fail` |
| 3 | UNKNOWN: data not collected |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
