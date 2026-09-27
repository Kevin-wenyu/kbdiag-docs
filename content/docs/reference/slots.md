---
title: "slots: replication slots"
description: "List replication slots: who consumes them, how much WAL they keep, and whether they hold back vacuum."
weight: 70
---

Captured on 2026-09-27 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `93bf65d` (static linux/amd64 binary). This is lab evidence, not production validation. The WARN example was created by a fault-injection script. It pauses the standby's WAL receiver (SIGSTOP), so after `wal_sender_timeout` (30 seconds here) the primary's slot turns inactive, as it does when a standby dies. Values belong to this capture only.

## Usage

```text
kbdiag slots [--json]
```

No options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## Healthy

```bash
~/kbdiag slots
echo EXIT_CODE=$?
```

```text
slots  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:45+08:00)

slots: 1
  name           type      active            retained  xmin  xmin age  restart_lsn
  repmgr_slot_2  physical  yes (pid 903372)  0 bytes   6342  0         0/A42EE580
EXIT_CODE=0
```

- `active` says whether something consumes the slot, and which process (here the walsender to the standby).
- `retained` is the WAL this slot makes the instance keep, in 1024-based units as `pg_size_pretty` uses. It is measured from the current WAL position on a primary and from the replay position on a standby.
- `xmin` is the oldest transaction id the slot asks the instance to keep. For this physical slot it comes from the standby's `hot_standby_feedback`. `xmin age` is how far it lags behind the current transaction id.
- A logical slot can also carry a `catalog_xmin`, which holds back vacuum of the system catalogs. That column appears only when some slot has one. (The lab runs `wal_level=replica`, so it has no logical slots.)

On a standby with no slots of its own:

```bash
~/kbdiag slots
echo EXIT_CODE=$?
```

```text
slots  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:21+08:00)

slots: 0
EXIT_CODE=0
```

## An inactive slot

```bash
~/kbdiag slots
echo EXIT_CODE=$?
```

```text
slots  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:37:55+08:00)

[WARN] slot.inactive  replication slot repmgr_slot_2 is inactive, retaining 216 bytes WAL, xmin 6354 holding back the vacuum horizon
  verify: kbdiag status  # run on this slot's downstream node (usually a standby): if it cannot connect, the node is down; inst.upstream with no receiver or not streaming means it is not receiving WAL; if it shows streaming, run it again after 10-20s: a last_msg that keeps growing means the receiver is stuck

slots: 1
  name           type      active  retained   xmin  xmin age  restart_lsn
  repmgr_slot_2  physical  no      216 bytes  6354  0         0/A42FF338
EXIT_CODE=1
```

- Nothing consumes an inactive slot, yet it keeps WAL, and one with an `xmin` stops VACUUM from removing old row versions. Being inactive is the line itself, so there is no time threshold and no option.
- It is a WARN, not a FAIL: the application keeps working. The harm (WAL filling the disk, table bloat, no standby keeping up) comes later.
- Right after the injection almost no WAL is retained. In a real failure it keeps growing.
- A standby restarted by repmgr also makes its slot inactive for a few seconds, and that is reported too.
- Drop the slot only when its downstream is really gone. kbdiag never drops it.

## Following the verify line

The `verify` line says to run `kbdiag status` on the slot's downstream node. That is usually a standby, though a standby can have downstreams of its own. On the paused standby:

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:55+08:00)

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-23 15:44:58  (up 3d 21h)
  connections     3 / 97  (max_connections 100 - superuser_reserved 3)

inst.upstream
  status    streaming
  upstream  192.168.105.10:54321
  slot      repmgr_slot_2
  last_msg  44s ago

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

The WAL receiver still shows `streaming`, because a paused process does not change its status. Run it again after 10–20 seconds, as the note says:

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:38:11+08:00)

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-23 15:44:58  (up 3d 21h)
  connections     3 / 97  (max_connections 100 - superuser_reserved 3)

inst.upstream
  status    streaming
  upstream  192.168.105.10:54321
  slot      repmgr_slot_2
  last_msg  1m 0s ago

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

`last_msg` grew from 44 seconds to 1 minute: the receiver is stuck. status does not judge `last_msg`, because a quiet primary only sends a message every `wal_receiver_status_interval` (10 seconds by default). If the node cannot be reached at all, it is down. If `inst.upstream` has no receiver or is not `streaming`, status reports that as a WARN.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: an inactive slot |
| 3 | UNKNOWN: data not collected |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
