---
title: "checkpoint: checkpoint activity"
description: "The last checkpoint, timed vs requested checkpoints, who writes dirty buffers, and the settings."
weight: 190
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. Nothing was injected. Values belong to this capture only.

## Usage

```text
kbdiag checkpoint [--json]
```

No options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## Primary

```bash
~/kbdiag checkpoint
echo EXIT_CODE=$?
```

```text
checkpoint  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:59+08:00)

last checkpoint
  time  2026-10-07 17:18:33  (2m 26s ago)
  redo  0/C651C548  (0000000300000000000000C6)

since the statistics reset 2026-09-15 23:12:34 (21d 18h ago)
  checkpoints        1606: 1606 timed, 0 requested (0%; requested covers WAL volume, CHECKPOINT, base backups, promotion)
  write, sync time   6m 54s, 490 ms
  buffers written    17029: checkpointer 10565 (62%), bgwriter 0 (0%), backends and others 6464 (38%)
  buffers allocated  37300
  backend fsyncs     0
  bgwriter stopped   0 times at bgwriter_lru_maxpages

settings
  checkpoint_timeout            5m 0s
  max_wal_size                  1024 MB
  checkpoint_completion_target  0.5
  checkpoint_warning            30s
  log_checkpoints               on
EXIT_CODE=0
```

- `last checkpoint` is the time and the `redo` position (with its WAL file) of the latest checkpoint.
- `checkpoints` counts timed and requested checkpoints since the statistics reset. "Requested" is not only WAL volume: a manual `CHECKPOINT`, a base backup (including a repmgr clone), a promotion, and creating or dropping a database count too. kbdiag gives the share but draws no conclusion. The server's own "checkpoints too frequent" warning looks at the interval between two checkpoints (`checkpoint_warning`), which cumulative counters cannot give.
- `buffers written` splits dirty-buffer writes into three: the checkpointer, the background writer, and "backends and others". The third is not "the checkpointer cannot keep up": in PG12 `buffers_backend` also counts relation extension, the ring buffers of VACUUM and COPY, and the standby's startup process, so an idle node can show 60-70% there (65% and 70% were measured in this lab).
- `backend fsyncs` above 0 is shown, not reported as a WARN. It means an fsync request could not be handed to the checkpointer, which happens when the queue is full or the checkpointer was not running at that moment (9 was measured earlier on this lab's node2, which kbha had restarted).
- `settings` is the relevant parameters.
- Display only, so any probe that is not collected makes the verdict UNKNOWN; OK means "all collected", not "good numbers".

## Standby

```bash
~/kbdiag checkpoint
echo EXIT_CODE=$?
```

```text
checkpoint  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:06+08:00)

checkpoint record the last restartpoint started from (written by the primary)
  time  2026-10-07 17:18:33  (2m 33s ago)
  redo  0/C651C548  (0000000300000000000000C6)

since the statistics reset 2026-10-07 16:49:26 (31m 40s ago)
  checkpoints        43 timed, 0 requested restartpoint attempts (a standby counts every try, one every 15s while no new checkpoint record has arrived)
  write, sync time   2m 51s, 26 ms
  buffers written    45117: checkpointer 7496 (17%), bgwriter 0 (0%), backends and others 37621 (83%)
  buffers allocated  38458
  backend fsyncs     1
  bgwriter stopped   0 times at bgwriter_lru_maxpages

settings
  checkpoint_timeout            5m 0s
  max_wal_size                  1024 MB
  checkpoint_completion_target  0.5
  checkpoint_warning            30s
  log_checkpoints               on
EXIT_CODE=0
```

- On a standby these are not restartpoint counts. In PG12 the checkpointer adds one for every attempt, and with no new checkpoint record it tries every 15 seconds (over four days that was 15917 attempts on this lab's node2), so the text says `restartpoint attempts` and gives no ratio.
- The header says the checkpoint record the last restartpoint started from was written by the primary: the time is the primary's.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
