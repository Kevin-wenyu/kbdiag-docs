---
title: "wal: WAL position and what keeps it"
description: "Where WAL is, how much sys_wal holds, and what keeps it: settings, slots, archiving."
weight: 200
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. Nothing was injected. Values belong to this capture only.

## Usage

```text
kbdiag wal [--json]
```

No options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## Primary

```bash
~/kbdiag wal
echo EXIT_CODE=$?
```

```text
wal  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:59+08:00)

position
  lsn   0/C9352468
  file  0000000300000000000000C9

sys_wal: 214 files, 3248 MB

what keeps WAL here
  max_wal_size        1024 MB
  wal_keep_segments   8192 MB  (512 x 16 MB)
  slot repmgr_slot_2  0 bytes  (active)
  archiving           38 .ready files waiting  (kbdiag archive)
EXIT_CODE=0
```

- `position` is the current write position and its WAL file.
- `sys_wal` is the same size as on [`space`]({{< relref "/docs/reference/space" >}}): same probe, same columns.
- `what keeps WAL here` puts on one screen what you would otherwise assemble from three commands: the parameters (`max_wal_size`, `wal_keep_segments` as its size), each replication slot with the WAL it retains and whether it is active, and the archive backlog. Here the slot retains 0 bytes and is active, but 38 `.ready` files wait for archiving (the lab's archiving is failing, see [`archive`]({{< relref "/docs/reference/archive" >}})).
- It shows and does not repeat the judgment. An inactive slot is reported by `kbdiag slots` and a failing archive by `kbdiag archive`; this screen only points there. The same problem reported in three commands would look like three problems.
- The WAL generation rate needs two samples over time; a single query cannot give it, so this version does not.

## Standby

```bash
~/kbdiag wal
echo EXIT_CODE=$?
```

```text
wal  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:06+08:00)

position
  replayed  0/C9352A80

sys_wal: 198 files, 3136 MB

what keeps WAL here
  max_wal_size       1024 MB
  wal_keep_segments  8192 MB  (512 x 16 MB)
  slots              none
  archiving          0 .ready files waiting
EXIT_CODE=0
```

On a standby `position` is the replay position (there is no write position, and no WAL file name). This standby has no slots of its own, and nothing waits for archiving.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
