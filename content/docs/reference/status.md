---
title: "status: instance overview"
description: "What this instance is and whether its basics hold: role, replication, connections, database sizes, disk."
weight: 60
---

Captured on 2026-09-27 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `93bf65d` (static linux/amd64 binary). This is lab evidence, not production validation. The FAIL example was created by a fault-injection script that fills every connection ordinary users may open. Values belong to this capture only.

## Usage

```text
kbdiag status [--json]
```

status has no options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

Only two things are judged:

- **FAIL** when every connection ordinary users may open is taken (`max_connections` less `superuser_reserved_connections`). At that point the application can no longer connect.
- **WARN** on a standby that is not receiving WAL, meaning it has no WAL receiver or its status is not `streaming`. Queries still work, but if the primary fails now there is no up-to-date standby to take over.

There is no "almost full" warning. How many connections is too many depends on the application, so status shows the count and leaves that call to you.

## On the primary

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:42+08:00)

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-20 22:19:13  (up 6d 15h)
  connections     5 / 97  (max_connections 100 - superuser_reserved 3)

inst.downstreams: 1
  name   address         state      sync
  node2  192.168.105.11  streaming  quorum

inst.upstream: not_applicable  (primary)

inst.databases: 5, total 382 MB
  test      325 MB
  esrep      15 MB
  mydb       14 MB
  kingbase   14 MB
  security   14 MB

inst.disk  (filesystem of data_directory)
  used   14 GB / 199 GB  (7%)
  free  185 GB
EXIT_CODE=0
```

- The role in the first line (primary / standby) comes from `sys_is_in_recovery()`.
- `inst.info`: `connections` counts only backends connected to a database, not background processes. It compares directly with the 97 connections ordinary users may open.
- `inst.downstreams`: one row per standby this instance sends WAL to, from `sys_stat_replication`. `sync` is shown as the server reports it. With repmgr it reads `quorum` here, not `sync` / `async`.
- `inst.upstream` only applies to a standby.
- `inst.databases`: non-template databases, largest first. Sizes use 1024-based units, as `pg_size_pretty` does.
- `inst.disk`: the filesystem holding `data_directory`, as `df` reports it. Used plus free is less than the total by the blocks reserved for root. It is shown, not judged.

## On the standby

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:22+08:00)

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-23 15:44:58  (up 3d 21h)
  connections     5 / 97  (max_connections 100 - superuser_reserved 3)

inst.upstream
  status    streaming
  upstream  192.168.105.10:54321
  slot      repmgr_slot_2
  last_msg  11s ago

inst.downstreams: 0

inst.databases: 5, total 382 MB
  test      325 MB
  esrep      15 MB
  kingbase   14 MB
  mydb       14 MB
  security   14 MB

inst.disk  (filesystem of data_directory)
  used   12 GB / 199 GB  (6%)
  free  187 GB
EXIT_CODE=0
```

- On a standby the upstream comes first. It comes from `sys_stat_wal_receiver`: where the standby gets WAL from, through which slot, and when the last message arrived.
- `last_msg` is shown, not judged. A quiet primary only sends a message every `wal_receiver_status_interval` (10 seconds by default), so a few seconds is normal.
- A paused WAL receiver (for example one stopped with SIGSTOP) keeps the status `streaming`, so status does not report it. If `last_msg` keeps growing, check the standby's WAL receiver process yourself. The [`slots`]({{< relref "/docs/reference/slots#following-the-verify-line" >}}) page shows a real capture of this.

## All connections taken

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  FAIL  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:38:16+08:00)

[FAIL] inst.connections  98 connections in use, reaching the 97 ordinary users may open (max_connections 100 minus 3 reserved for superusers): ordinary users can no longer connect
  verify: kbdiag sessions  # who holds the connections: the summary at the top counts them by user, database, application and client

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-20 22:19:13  (up 6d 15h)
  connections     98 / 97  (max_connections 100 - superuser_reserved 3)

inst.downstreams: 1
  name   address         state      sync
  node2  192.168.105.11  streaming  quorum

inst.upstream: not_applicable  (primary)

inst.databases: 5, total 382 MB
  test      325 MB
  esrep      15 MB
  mydb       14 MB
  kingbase   14 MB
  security   14 MB

inst.disk  (filesystem of data_directory)
  used   14 GB / 199 GB  (7%)
  free  185 GB
EXIT_CODE=2
```

- 98 is above 97 because superusers still get in through the reserve, including kbdiag's own `system` connection.
- The `verify` line points to [`sessions`]({{< relref "/docs/reference/sessions" >}}), whose summary counts connections by user, database, application and client. [In this capture]({{< relref "/docs/reference/sessions#who-holds-the-connections" >}}) it shows 93 idle sessions of `kbdiag_ro` from `127.0.0.1`.

## Standby not receiving WAL

This case has not been reproduced in the lab yet. The finding below is quoted from the source code, not captured. On a standby with no WAL receiver, status reports:

```text
[WARN] inst.upstream  the standby has no WAL receiver and is not receiving WAL from the primary: if the primary fails now, no standby can take over
  verify: kbdiag slots  # run on the primary: is this standby's slot inactive?
```

If the receiver exists but its status is not `streaming`, the finding names that status instead. The exit code is 1.

## Over TCP

kbdiag only reads `inst.disk` when it is sure it runs on the database host. That means one of:

- the Unix socket;
- `--host` set to localhost / 127.0.0.1 / ::1, with `data_directory` present locally. The directory check is needed because a forwarded port could lead to another machine.

Otherwise `inst.disk` is `not_applicable`. Here kbdiag connects to the primary's own network address as `kbdiag_ro`:

```bash
PGPASSWORD=... ~/kbdiag status --host 192.168.105.10 -U kbdiag_ro
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:40:08+08:00)

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-20 22:19:13  (up 6d 15h)
  connections     5 / 97  (max_connections 100 - superuser_reserved 3)

inst.downstreams: 1
  name   address         state      sync
  node2  192.168.105.11  streaming  quorum

inst.upstream: not_applicable  (primary)

inst.databases: 5, total 382 MB
  test      325 MB
  esrep      15 MB
  mydb       14 MB
  kingbase   14 MB
  security   14 MB

inst.disk: not_applicable  (remote connection)
EXIT_CODE=0
```

`not_applicable` does not affect the verdict.

## Without privileges

`kbdiag_ro` has no monitoring role. On KingbaseES V8R6 it still sees `sys_stat_replication`, `sys_stat_wal_receiver` and `data_directory` in full, so status gives it the same result as `system`. Only database sizes can be hidden. Without CONNECT on a database, that database's size is empty and recorded in `redacted`. Sizes are not judged, so the verdict stays OK rather than UNKNOWN.

## JSON

`--json` keeps raw values: sizes in bytes, times in seconds, and the version as the short number. `inst.info` also carries `usable_connections`. `inst.disk` carries `total_bytes`, `used_bytes` and `avail_bytes`. A probe that does not apply has `"status": "not_applicable"` and a reason, for example `"primary"` or `"remote connection"`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: a standby is not receiving WAL |
| 2 | FAIL: all connections ordinary users may open are taken |
| 3 | UNKNOWN: data not collected |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
