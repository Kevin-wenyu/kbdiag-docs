---
title: "Investigate replication lag"
description: "Compare sender, receiver and replay positions."
weight: 30
---

Lab capture on 2026-09-16, KingbaseES V008R006C009B0014, tool source `3bea0be`. Host addresses use documentation-only replacements. This is a healthy replication baseline, not an induced lag experiment.

## 1. Inspect both nodes

Confirm the target and role with `~/kbdiag status`, then run on each node:

```bash
~/kbdiag replication -v --no-color --exit-code
```

Primary output and independent system-view check:

```text
==> Replication
[INFO]  Standby connections:
client_addr        state      sync_state  replay_lag
192.0.2.11/32  streaming  quorum      0 bytes
[OK]    1 standby(s) connected
EXIT_CODE=0
current_timestamp|application_name|state|sync_state|sent_lsn|write_lsn|flush_lsn|replay_lsn
2026-09-16 08:38:13.508273+08|node2|streaming|quorum|0/A00117E8|0/A00117E8|0/A00117E8|0/A00117E8
(1 row)
```
Standby output and independent check:

```text
==> Replication
[OK]    WAL receiver: streaming
[INFO]  Replay delay : +00000000000:00:43.000000000
[INFO]  Receive LSN  : 0/A00117E8
[INFO]  Replay  LSN  : 0/A00117E8
EXIT_CODE=0
current_timestamp|status
2026-09-16 08:38:15.648926+08|streaming
(1 row)
pg_last_wal_receive_lsn|pg_last_wal_replay_lsn
0/A00117E8|0/A00117E8
(1 row)
```

## 2. Bytes and elapsed time differ

- Primary `replay_lag` is `sent_lsn - replay_lsn` in bytes, not seconds. This sample shows 0 bytes.
- Equal receive/replay LSNs mean received WAL was replayed to that position at this sample. Queries across nodes are not an atomic snapshot.
- `Replay delay` is time since the last replayed transaction. It can grow during idle periods even when caught up. The roughly 43 seconds here do not establish 43 seconds of backlog.
- `streaming` describes receiver state, not absence of lag; `quorum` is not a complete disaster-recovery acceptance test.
- Exit status was 0. This command does not apply thresholds to every lag value; do not monitor replication latency using exit status alone.

## 3. Follow the evidence

| Observation | Next check |
|---|---|
| Expected standby missing on primary | Standby process, connection logs, network and authentication; standalone instances may intentionally have none |
| Receive position persistently behind sender | Network, WAL sender/receiver and standby write capacity |
| Received WAL increasingly ahead of replay | Paused replay, recovery conflicts, disk load and logs |
| LSNs caught up but elapsed time grows | Check whether writes are idle before declaring a replication fault |

Use `~/kbdiag check` and `~/kbdiag cluster ready` for additional evidence. Do not switch primaries, rebuild a standby or advance slots merely to clear warnings.

## 4. Verify recovery

Take repeated samples during normal commits. Confirm expected standbys remain connected, receive/replay positions advance and gaps converge; check application visibility. A momentary catch-up is not sustained stability or backup recoverability.
