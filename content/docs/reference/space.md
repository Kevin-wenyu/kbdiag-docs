---
title: "space: disk, WAL, databases"
description: "Where the space goes: filesystems, WAL size against its settings, database and tablespace sizes."
weight: 80
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. Everything here comes from the healthy lab and from two accounts that cannot see everything: `kbdiag_ro` (no monitoring role) over `127.0.0.1`, and `kbdiag_ro` over the node's network address. No fault was injected for this command. The one FAIL it can report was not produced in the lab (see the last section). Values belong to this capture only.

## Usage

```text
kbdiag space [--json]
```

No options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## Healthy primary

```bash
~/kbdiag space
echo EXIT_CODE=$?
```

```text
space  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:53+08:00)

disk: 1 filesystem
  holds                used   size    free    use
  data_directory, wal  15 GB  199 GB  184 GB  7%

wal: 214 files, 3248 MB
  max_wal_size       1024 MB
  wal_keep_segments  8192 MB  (512 x 16 MB)

databases: 5, total 439 MB
  test      381 MB
  esrep      15 MB
  mydb       14 MB
  kingbase   14 MB
  security   14 MB

tablespaces: 3
  name         location             size
  sys_default  (in data_directory)  467 MB
  sys_global   (in data_directory)  735 kB
  sysaudit     (in data_directory)  24 kB
EXIT_CODE=0
```

- `disk` lists the filesystems that hold the data directory, the WAL directory and the tablespaces, with directories on the same filesystem merged into one row (by device number, so a `sys_wal` that is a symlink to another disk shows up as its own row). `free` is what a non-root user such as `kingbase` can use. It reads the disk with statfs, so it works only when kbdiag runs on the database host (see "Remote connection" below).
- `wal` is the size of `sys_wal`, set beside `max_wal_size` and `wal_keep_segments` (shown as the size it keeps: 512 x 16 MB). kbdiag does not judge it: `max_wal_size` is a soft limit, and PG12 normally keeps about the sum of both plus the WAL written since the last checkpoint, so exceeding only one of them is normal. When `sys_wal` is above that sum, the text points you to `kbdiag slots` and `kbdiag archive`. Here 3248 MB is below 1024 + 8192 MB.
- `databases` reuses the same probe as [`status`]({{< relref "/docs/reference/status" >}}), so the numbers match `status`.
- `tablespaces` lists each one with its location (`in data_directory` for the default ones).

## Standby

```bash
~/kbdiag space
echo EXIT_CODE=$?
```

```text
space  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:00+08:00)

disk: 1 filesystem
  holds                used   size    free    use
  data_directory, wal  13 GB  199 GB  186 GB  6%

wal: 198 files, 3136 MB
  max_wal_size       1024 MB
  wal_keep_segments  8192 MB  (512 x 16 MB)

databases: 5, total 438 MB
  test      381 MB
  esrep      15 MB
  mydb       14 MB
  security   14 MB
  kingbase   14 MB

tablespaces: 3
  name         location             size
  sys_default  (in data_directory)  467 MB
  sys_global   (in data_directory)  735 kB
  sysaudit     (in data_directory)  24 kB
EXIT_CODE=0
```

A standby is judged the same way. Its WAL directory is its own, so the file count and size differ from the primary's.

## Without privileges

`kbdiag_ro` has no monitoring role. It connects over `127.0.0.1`, which is TCP (hence `kbdiag_ro@remote` in the first line), but the database is on this host, so the disk can still be read:

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro space
echo EXIT_CODE=$?
```

```text
space  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-10-07T17:21:07+08:00)

disk: 1 filesystem
  holds                used   size    free    use
  data_directory, wal  15 GB  199 GB  184 GB  7%

wal: skipped  (insufficient_privilege 42501: permission denied for function sys_ls_waldir)

databases: 5, total 439 MB
  test      381 MB
  esrep      15 MB
  mydb       14 MB
  kingbase   14 MB
  security   14 MB

tablespaces: 3
  name         location             size
  sys_default  (in data_directory)  467 MB
  sys_global   (in data_directory)  ?
  sysaudit     (in data_directory)  ?
redacted: 2 rows of space.tablespaces hide size_bytes (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- `wal: skipped`: `sys_ls_waldir` is not allowed for this account, so the WAL size is not collected. `space` is a display command, so any probe that is not collected makes the verdict UNKNOWN instead of OK: OK would only mean "everything was collected", and here it was not.
- `?` in the tablespace table means this account cannot see that size (`pg_tablespace_size(sys_global)` is denied). kbdiag wraps the call in a CASE, so only those cells are NULL and the rest of the statement still runs; the cells are listed in `redacted`. Granting `sys_monitor` lifts both.

## Remote connection

Over the node's network address the data directory may be on another machine than the one you are looking at, so kbdiag does not read a disk:

```bash
PGPASSWORD=... ~/kbdiag --host 192.168.105.10 -U kbdiag_ro space
echo EXIT_CODE=$?
```

```text
space  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-10-07T17:21:10+08:00)

disk: not_applicable  (remote connection)

wal: skipped  (insufficient_privilege 42501: permission denied for function sys_ls_waldir)

databases: 5, total 439 MB
  test      381 MB
  esrep      15 MB
  mydb       14 MB
  kingbase   14 MB
  security   14 MB

tablespaces: 3
  name         location             size
  sys_default  (in data_directory)  467 MB
  sys_global   (in data_directory)  ?
  sysaudit     (in data_directory)  ?
redacted: 2 rows of space.tablespaces hide size_bytes (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- `disk: not_applicable  (remote connection)`. kbdiag reads the disk only when it is certain to run on the database host: a Unix socket, or a host of `localhost`, `127.0.0.1` or `::1` with the `data_directory` present locally. A forwarded port could lead to another machine, so the host name alone is not enough.
- `not_applicable` is not a failure, but with the privilege gaps above the verdict is UNKNOWN here too.

## The FAIL that was not produced

Not produced in the lab, taken from the source: `space.disk_full` (FAIL). It reports a filesystem holding the data directory or the WAL directory whose free space is less than one WAL segment (16 MB here). Making it appear needs the data disk to be really filled, which the lab does not do.

- On the WAL disk no new segment can be created, so the server stops once no old segment is left to reuse. On the data directory's disk, tables, transaction status files and temp files are about to fail to grow (these are ERRORs; the instance does not stop). The finding says which applies.
- Strictly it is "about to be affected", and kbdiag reports it as FAIL because there is one segment of room left and no margin to keep watching.
- Free space on other disks (a tablespace) or "low but more than a segment" depends on the database, so it is only shown.
- One finding per filesystem. The segment size comes from the `wal` probe, so when it is not collected (as for `kbdiag_ro`) this rule does not judge.

The [`status`]({{< relref "/docs/reference/status" >}}) command's `inst.disk` is a shorter, display-only view of the data directory's disk.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 2 | FAIL: a filesystem has less free space than one WAL segment (not produced in the lab) |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
