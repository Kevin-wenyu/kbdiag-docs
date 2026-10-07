---
title: "repl: replication from this node"
description: "Replication from this node: each standby's lag and the synchronous settings on a primary; receive and replay on a standby."
weight: 130
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. The WARN example was created by a fault-injection script that pauses the standby's WAL receiver (SIGSTOP), the same one used on the [`slots`]({{< relref "/docs/reference/slots" >}}) page. Values belong to this capture only.

## Usage

```text
kbdiag repl [--json]
```

No options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## Primary

```bash
~/kbdiag repl
echo EXIT_CODE=$?
```

```text
repl  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:56+08:00)

sync
  synchronous_standby_names  ANY 1( node2)  (any 1 of node2 must confirm)
  synchronous_commit         remote_apply
  synchronous now            1 (node2)

downstreams: 1  (bytes behind this node's current WAL position)
  name   address         state      sync    sent     flushed  replayed  replay lag  last reply
  node2  192.168.105.11  streaming  quorum  0 bytes  0 bytes  0 bytes   0s          1s ago
EXIT_CODE=0
```

- `sync` shows `synchronous_standby_names` and what it means (`any 1 of node2 must confirm`), `synchronous_commit`, and how many standbys the server currently counts as synchronous. `quorum` in the `sync` column is the server's own `sync_state`; repmgr reports `quorum` here rather than `sync` or `async`, so kbdiag does not translate it.
- `downstreams` is one row per standby: the position it has been sent, flushed and replayed, as bytes behind this node's current WAL position, the replay lag in time (empty when the standby is caught up and idle), and how long ago it last replied.
- Lag is shown, not judged. There is no objective line on the server for it.

## Standby

```bash
~/kbdiag repl
echo EXIT_CODE=$?
```

```text
repl  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:03+08:00)

upstream
  status    streaming
  upstream  192.168.105.10:54321
  slot      repmgr_slot_2
  last_msg  3s ago

replay
  received                   0/C9352A80
  replayed                   0/C9352A80  (caught up with what was received)
  last replayed transaction  1m 0s ago
  paused                     no

downstreams: 0
EXIT_CODE=0
```

- `upstream` is the same WAL receiver view as `kbdiag status` (`inst.upstream`), with `last_msg` the time since the last message from the primary.
- `replay` compares what was received with what was replayed. `caught up with what was received` means the two positions are equal. `last replayed transaction 1m 0s ago` is not a delay: on an idle primary it can read hours while the positions are identical, so kbdiag does not use it as a lag.
- `paused` is whether replay was paused with `sys_wal_replay_pause()`.

## A stuck WAL receiver

With the standby's receiver paused, the standby reports:

```bash
~/kbdiag repl
echo EXIT_CODE=$?
```

```text
repl  WARN  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:22:58+08:00)

[WARN] inst.upstream  the standby's WAL receiver shows streaming, but nothing has come from the primary for 1m 12s, longer than wal_receiver_timeout (30s), after which a working receiver reconnects: it is stuck (stopped or blocked), so it is not receiving WAL: if the primary fails now, no standby can take over
  verify: kbdiag slots  # run on the primary: is this standby's slot inactive?

upstream
  status    streaming
  upstream  192.168.105.10:54321
  slot      repmgr_slot_2
  last_msg  1m 12s ago

replay
  received                   0/CCCC9228
  replayed                   0/CCCC9228  (caught up with what was received)
  last replayed transaction  1m 12s ago
  paused                     no

downstreams: 0
EXIT_CODE=1
```

- The finding is `inst.upstream`, the same rule `kbdiag status` uses: the receiver says `streaming`, but `last_msg` is older than `wal_receiver_timeout` (30 s in the lab). A working receiver asks the primary for a reply at half that time and reconnects when it is full, so only a stuck one gets past it. Without a receiver, or in a state other than `streaming`, the same finding fires.
- The `received` and `replayed` positions stay equal: nothing arrived, so there is nothing to replay. It is the age of the last message that shows it.
- Known edge: the receiver sets its receive time at connection start, so a slow connection (more than half the timeout) or a timeline switch can raise this finding once for a moment. There is no margin on purpose, because no objective value for one exists.

The primary at the same moment:

```bash
~/kbdiag repl
echo EXIT_CODE=$?
```

```text
repl  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:22:56+08:00)

sync
  synchronous_standby_names  (none: asynchronous only)
  synchronous_commit         remote_apply

downstreams: 0
EXIT_CODE=0
```

- The standby is gone from `downstreams` (0), and `synchronous_standby_names` now reads `(none: asynchronous only)`; it was `ANY 1( node2)` before the injection. So `repl.sync_short` did not fire. kbdiag shows what the server has; the the setting changed during the injection because repmgr changed it: with `synchronous='quorum'` in repmgr.conf, repmgrd clears `synchronous_standby_names` about 2 seconds after the standby disconnects (falling back to asynchronous commits) and restores it when the standby reconnects (seen in the lab's hamgr.log, 2026-09-28). It is repmgr, not KingbaseES itself. So on this kind of cluster `repl.sync_short` shows only in that short window; the usual state after a standby is lost is "already asynchronous", which `repl` shows as `(none: asynchronous only)`.
- Use [`slots`]({{< relref "/docs/reference/slots" >}}) on the primary to see the slot turned inactive, and [`cluster`]({{< relref "/docs/reference/cluster" >}}) for repmgr's view.

## WARN findings not produced in the lab

Taken from the source, not captured:

- `repl.replay_paused` (WARN): replay is paused on a standby (`sys_wal_replay_pause()`). Queries still run, but it falls further behind and a failover would have to replay everything received first. The `fix` is `SELECT sys_wal_replay_resume()` unless it was paused on purpose. It has no injection in the lab: pausing replay there blocks every commit on the primary (`synchronous_commit` is `remote_apply`).
- `repl.sync_short` (WARN): `synchronous_standby_names` needs more standbys than the server counts as synchronous candidates (`sync` or `quorum`). The text says commits either wait or the server has stopped waiting, so the synchronous copy is not guaranteed. It is a WARN rather than FAIL because in the lab, commits went through after the standby disconnected (repmgr had switched to asynchronous, see above). kbdiag counts the server's own `sync_state` instead of redoing the candidate rules, and it judges only when `synchronous_commit` makes commits wait for a standby (this connection's value; per-role or per-database settings are not visible).

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: no WAL being received, replay paused, or too few synchronous standbys |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
