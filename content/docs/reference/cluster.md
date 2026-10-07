---
title: "cluster: repmgr's view"
description: "repmgr's view of the cluster (nodes, roles, upstreams, latest events), checked against this node."
weight: 140
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. The cluster is managed by repmgr, with its metadata in database `esrep`. The WARN example was created by the fault-injection script that pauses the standby's WAL receiver (SIGSTOP) until the standby is no longer attached to the primary, the same one used on the [`slots`]({{< relref "/docs/reference/slots" >}}) page. Values belong to this capture only.

## Usage

```text
kbdiag cluster [--json]
```

No options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}), with one difference: without `-d`, `cluster` connects to database `esrep`, where repmgr keeps its metadata. kbdiag holds only one connection, so it does not open a second one for it. If there is no `esrep` database it falls back to the default database (not exit code 69, which only means the instance cannot be reached). It does not run the repmgr binaries, so the per-node `Status` column of `repmgr cluster show` (which connects to each node) is not available.

## Primary

```bash
~/kbdiag cluster
echo EXIT_CODE=$?
```

```text
cluster  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:56+08:00)

nodes: 2  (repmgr metadata in database esrep)
  id  name   type     upstream  active  priority  location  slot
  1   node1  primary  -         yes     100       default   repmgr_slot_1
  2   node2  standby  node1     yes     100       default   repmgr_slot_2
  this node is node1: repmgr says primary, the database is a primary
  attached here: node2

events: 20  (the latest, at most 20)
  time                 node   event                   ok   details
  2026-10-07 17:20:02  node2  standby_recovery        yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:20:01  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:20:01  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:19:18  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:12:14  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 17:12:08  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:01:21  node2  standby_recovery        yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:01:21  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:01:19  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:00:38  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 16:49:31  node1  child_node_new_connect  yes  new standby "node2" (ID: 2) has connected
  2026-10-07 16:49:28  node2  repmgrd_start           yes  monitoring connection to upstream node "node1" (ID: 1)
  2026-10-07 16:49:26  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 16:49:26  node2  node_rejoin             yes  node 2 is now attached to node 1
  2026-10-07 16:48:36  node1  repmgrd_start           yes  monitoring cluster primary "node1" (ID: 1)
  2026-09-29 20:06:21  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 8 seconds
  2026-09-29 20:06:13  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-09-29 19:22:45  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-09-29 19:22:38  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-09-28 15:42:40  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 106 seconds
EXIT_CODE=0
```

- `nodes` is repmgr's node table: type, upstream, active, priority, location and replication slot. The text marks which node this is, using repmgr's `get_local_node_id()` first and the `primary_slot_name` (`repmgr_slot_N`) otherwise. If it cannot tell which node it is, it does not compare roles and the verdict is not OK.
- The line `this node is node1: repmgr says primary, the database is a primary` is the comparison between repmgr's metadata and what the database itself says. `attached here: node2` is the standbys repmgr says follow this node that really have a walsender here.
- `events` is the latest 20 repmgr events. The disconnect and reconnect events in the list are from earlier test runs in this lab.
- A node that is up or not, and whether `repmgrd` is running, are not visible from one database; run `kbdiag status` on each node.
- The conninfo is not collected: it may contain a password.

## Standby

```bash
~/kbdiag cluster
echo EXIT_CODE=$?
```

```text
cluster  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:03+08:00)

nodes: 2  (repmgr metadata in database esrep)
  id  name   type     upstream  active  priority  location  slot
  1   node1  primary  -         yes     100       default   repmgr_slot_1
  2   node2  standby  node1     yes     100       default   repmgr_slot_2
  this node is node2: repmgr says standby, the database is a standby

events: 20  (the latest, at most 20)
  time                 node   event                   ok   details
  2026-10-07 17:20:02  node2  standby_recovery        yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:20:01  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:20:01  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:19:18  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:12:14  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 17:12:08  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:01:21  node2  standby_recovery        yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:01:21  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:01:19  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:00:38  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 16:49:31  node1  child_node_new_connect  yes  new standby "node2" (ID: 2) has connected
  2026-10-07 16:49:28  node2  repmgrd_start           yes  monitoring connection to upstream node "node1" (ID: 1)
  2026-10-07 16:49:26  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 16:49:26  node2  node_rejoin             yes  node 2 is now attached to node 1
  2026-10-07 16:48:36  node1  repmgrd_start           yes  monitoring cluster primary "node1" (ID: 1)
  2026-09-29 20:06:21  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 8 seconds
  2026-09-29 20:06:13  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-09-29 19:22:45  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-09-29 19:22:38  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-09-28 15:42:40  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 106 seconds
EXIT_CODE=0
```

The standby's repmgr metadata is replicated from the primary, so the node table and the events are the same. Only the comparison line is its own. `cluster.detached` is judged on the primary only.

## An explicit `-d`

```bash
~/kbdiag -d test cluster
echo EXIT_CODE=$?
```

```text
cluster  UNKNOWN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:11+08:00)

nodes: skipped  (no repmgr schema in database test named by -d; repmgr keeps it in database esrep by default)

events: skipped  (no repmgr schema in database test named by -d; repmgr keeps it in database esrep by default)
EXIT_CODE=3
```

When you give `-d` yourself, kbdiag trusts it. Database `test` has no repmgr schema, so both probes are `skipped`, which makes the verdict UNKNOWN (without `-d` the same absence would be `not_applicable`: not a repmgr cluster, or the metadata is somewhere else). The text says where repmgr keeps its data by default.

## A standby that is not attached

```bash
~/kbdiag cluster
echo EXIT_CODE=$?
```

```text
cluster  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:22:57+08:00)

[WARN] cluster.detached  repmgr lists node2 as an active standby of this node (node1), but no walsender here has that application_name: it is not attached (repmgr cluster show would report it so), unless its conninfo sets another application_name
  verify: kbdiag status  # run on node2: is it up, is it receiving WAL
  verify: kbdiag slots  # whether its slot here is inactive

nodes: 2  (repmgr metadata in database esrep)
  id  name   type     upstream  active  priority  location  slot
  1   node1  primary  -         yes     100       default   repmgr_slot_1
  2   node2  standby  node1     yes     100       default   repmgr_slot_2
  this node is node1: repmgr says primary, the database is a primary
  not attached here: node2

events: 20  (the latest, at most 20)
  time                 node   event                   ok   details
  2026-10-07 17:22:20  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:20:02  node2  standby_recovery        yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:20:01  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:20:01  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:19:18  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:12:14  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 17:12:08  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:01:21  node2  standby_recovery        yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:01:21  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:01:19  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:00:38  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 16:49:31  node1  child_node_new_connect  yes  new standby "node2" (ID: 2) has connected
  2026-10-07 16:49:28  node2  repmgrd_start           yes  monitoring connection to upstream node "node1" (ID: 1)
  2026-10-07 16:49:26  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 16:49:26  node2  node_rejoin             yes  node 2 is now attached to node 1
  2026-10-07 16:48:36  node1  repmgrd_start           yes  monitoring cluster primary "node1" (ID: 1)
  2026-09-29 20:06:21  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 8 seconds
  2026-09-29 20:06:13  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-09-29 19:22:45  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-09-29 19:22:38  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
EXIT_CODE=1
```

- `cluster.detached` (WARN): repmgr still lists `node2` as an active standby of this node, but no walsender here has that application name, so it is not attached. repmgr would report it so too, unless the standby's conninfo sets another `application_name`. The text line `not attached here: node2` is the same fact.
- The newest event, `child_node_disconnect` at 17:22:20, is repmgr's own record of the same thing.
- It is a WARN: the business is not hit yet. Whether it is really down or only stuck shows only on the node itself, so the `verify` lines say to run `kbdiag status` on `node2` and `kbdiag slots` here.

## WARN findings not produced in the lab

Taken from the source, not captured. All are WARN, because repmgr acts on its metadata and a mismatch is a risk, but the business is not affected yet; whether it is a real split brain shows only on each node.

- `cluster.primaries`: repmgr lists more than one active primary. Its metadata says split brain; run `kbdiag status` on each to see which one is out of recovery.
- `cluster.inactive`: repmgr marks a node inactive, counted as failed or removed, so the cluster has one node less to fail over to.
- `cluster.role_mismatch`: repmgr says this node is a primary (or standby), but the database is the other.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
