---
title: "progress: long operations"
description: "How far running VACUUM, CREATE INDEX, CLUSTER / VACUUM FULL and CHECKPOINT have got."
weight: 180
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. The running example was created by an injection script that ran `CREATE INDEX` on `public.orders` (1,000,000 rows) and was read three times while it ran, once by `kbdiag_ro`. PIDs and timings belong to this capture only.

## Usage

```text
kbdiag progress [--json]
```

No options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## Nothing running

```bash
~/kbdiag progress
echo EXIT_CODE=$?
```

```text
progress  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:58+08:00)

running: 0  (VACUUM, CREATE INDEX, CLUSTER and VACUUM FULL, CHECKPOINT; ANALYZE and base backups have no progress view in this version)
EXIT_CODE=0
```

The text says which operations it looks at. It also says what it cannot: ANALYZE and base backups have no progress view in this version. The standby (kes-node2) printed the same line.

- kbdiag merges three PostgreSQL progress views (VACUUM, CREATE INDEX, CLUSTER / VACUUM FULL) into one probe, since the reader asks "how far is the long operation" and does not care which view it is in. KingbaseES's own checkpoint view is a separate probe, because only its column names were observed and a failure there must not take the other three with it.

## CREATE INDEX in progress

```bash
~/kbdiag progress
echo EXIT_CODE=$?
```

```text
progress  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:24+08:00)

running: 1
  pid    command       database  relation  phase                           progress                  running
  43243  CREATE INDEX  test      orders    building index: scanning table  5058 / 7896 blocks (64%)  3s
EXIT_CODE=0
```

A few seconds later the same build:

```bash
~/kbdiag progress
echo EXIT_CODE=$?
```

```text
progress  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:29+08:00)

running: 1
  pid    command       database  relation  phase                           progress                   running
  43243  CREATE INDEX  test      orders    building index: scanning table  7896 / 7896 blocks (100%)  8s
EXIT_CODE=0
```

- `phase` is the operation's own phase, and `progress` is done / total with its unit and a percentage. The counter is chosen by phase: block counts stop at the end of the scan, and the following phases (vacuum's cleanup, the index's sort and load) count something else, otherwise the display would sit at 100% for a long time. 100% in the second capture is the end of the table scan, not of the index build.
- `running` is how long the operation has been running.
- It only shows. How long is slow has no objective line, and whether a vacuum should run is judged by `kbdiag vacuum`. When a `CREATE INDEX CONCURRENTLY` is still waiting for other transactions, the phase is followed by how many are left and the text points to `kbdiag locks`, which is the usual reason it looks stuck.

## Without privileges

`kbdiag_ro` (no monitoring role, over `127.0.0.1`) reads the same build:

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro progress
echo EXIT_CODE=$?
```

```text
progress  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-10-07T17:21:25+08:00)

running: 1
  pid    command                  database  relation  phase  progress  running
  43243  CREATE INDEX or REINDEX  test      -         ?      ?         ?
redacted: 1 row of progress.list hides phase (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

The operation is visible, but `phase` is hidden (`?`), so progress, running time and relation are not shown, and the label reads `CREATE INDEX or REINDEX`. The hidden cells are recorded under `redacted`. Because something could not be seen, the verdict is UNKNOWN even though the operation was found. Granting `sys_monitor` lifts it.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
