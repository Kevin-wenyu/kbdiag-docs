---
title: "archive: WAL archiving"
description: "Whether WAL archiving works: settings, last success and failure, WAL waiting to be archived."
weight: 110
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. No fault was injected. The primary's WAL archiving was already failing in the lab (its `archive_command` runs `sys_rman archive-push`, and the last success was 21 days earlier), so the WARN below is what the lab really looks like; why it fails was not investigated for this page, because kbdiag does not read the server log. Values belong to this capture only.

## Usage

```text
kbdiag archive [--json]
```

No options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## Primary: archiving is failing

```bash
~/kbdiag archive
echo EXIT_CODE=$?
```

```text
archive  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:55+08:00)

[WARN] archive.failing  archiving is failing: the last attempt failed (0000000300000000000000A3, 6s ago) and the last success was 21d 3h ago (0000000300000000000000A2); 22590 failures since the statistics reset. WAL that is not archived stays in sys_wal and is missing from the backups
  verify: kbdiag space  # how big sys_wal has grown; why archive_command fails is in the server log (log_directory)

settings
  archive_mode     always
  archive_command  export TZ=Asia/Shanghai;/home/kingbase/cluster/install/kingbase/bin/sys_rman --config /rman/kbbr_repo/sys_rman.conf --stanza=kingbase archive-push %p
  archive_timeout  0 (off)

archiver  (counting since 2026-09-15 23:12:34)
  archived  35     last 0000000300000000000000A2  21d 3h ago
  failed    22590  last 0000000300000000000000A3  6s ago

waiting: 38 .ready, 174 .done  (oldest .ready 21d 3h)
EXIT_CODE=1
```

- `archive.failing` (WARN) fires when the last attempt failed: the last failure is later than the last success, or there has never been a success. WAL that is not archived stays in `sys_wal` and is missing from the backups, but the business keeps running, so it is a WARN.
- `settings` shows `archive_mode`, `archive_command` and `archive_timeout`. kbdiag first excludes what is switched off on purpose: `archive_mode=off` is never judged, and `archive_mode=on` on a standby is not judged either, because a standby does not archive unless the mode is `always`.
- `archiver` is the server's archiver statistics, counted since the statistics reset time: how many succeeded and failed, and the last WAL file and how long ago for each.
- `waiting` counts `.ready` files (WAL waiting to be archived) and `.done` files, and how long the oldest `.ready` has waited. It is display only: it must not change the verdict.
- The `verify` line points to `kbdiag space` (how big `sys_wal` has grown). The reason the command fails is only in the server log (`log_directory`).
- An empty `archive_command` is not judged: the PostgreSQL documentation says WAL then stays until a command is set, but this was not checked on KingbaseES, so the text only writes `(empty)`.

## Standby

```bash
~/kbdiag archive
echo EXIT_CODE=$?
```

```text
archive  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:02+08:00)

settings
  archive_mode     always
  archive_command  export TZ=Asia/Shanghai;/home/kingbase/cluster/install/kingbase/bin/sys_rman --config /rman/kbbr_repo/sys_rman.conf --stanza=kingbase archive-push %p
  archive_timeout  0 (off)

archiver  (counting since 2026-10-07 16:49:26)
  archived  38  last 0000000300000000000000C8  2m 17s ago
  failed    0

waiting: 0 .ready, 212 .done
EXIT_CODE=0
```

The standby runs with `archive_mode=always`, so it archives too. It counts since its own start, and here it succeeds and has nothing waiting, so it is OK.

## Without privileges

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro archive
echo EXIT_CODE=$?
```

```text
archive  WARN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-10-07T17:21:09+08:00)

[WARN] archive.failing  archiving is failing: the last attempt failed (0000000300000000000000A3, 20s ago) and the last success was 21d 3h ago (0000000300000000000000A2); 22590 failures since the statistics reset. WAL that is not archived stays in sys_wal and is missing from the backups
  verify: kbdiag space  # how big sys_wal has grown; why archive_command fails is in the server log (log_directory)

settings
  archive_mode     always
  archive_command  export TZ=Asia/Shanghai;/home/kingbase/cluster/install/kingbase/bin/sys_rman --config /rman/kbbr_repo/sys_rman.conf --stanza=kingbase archive-push %p
  archive_timeout  0 (off)

archiver  (counting since 2026-09-15 23:12:34)
  archived  35     last 0000000300000000000000A2  21d 3h ago
  failed    22590  last 0000000300000000000000A3  20s ago

waiting: skipped  (insufficient_privilege 42501: permission denied for function sys_ls_archive_statusdir)
EXIT_CODE=1
```

`kbdiag_ro` cannot call `sys_ls_archive_statusdir`, so `waiting` is `skipped`. That probe is display only and is not allowed to change the verdict. The finding itself comes from the statistics view, which this account can read.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: the last archive attempt failed |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
