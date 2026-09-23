---
title: "slots: replication slots"
description: "List replication slots and flag inactive ones, which keep WAL and hold back vacuum."
weight: 70
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `0a4d61e` (static linux/amd64 binary). This is lab evidence, not production validation. The FAIL example was created by a fault-injection script: it pauses the standby's WAL receiver, so the primary's slot turns inactive after `wal_sender_timeout` (30 seconds here), as when a standby dies. Values belong to this capture only.

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
slots  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:39:07+08:00)

slot.list: 1 rows
slot_name      slot_type  active  active_pid  xmin  catalog_xmin  xmin_age  restart_lsn  retained_wal_bytes
repmgr_slot_2  physical   true    364531      6021  -             0         0/A40F4578   0
EXIT_CODE=0
```

- `active=true`; `active_pid` is the walsender using the slot.
- `xmin` comes from the standby's `hot_standby_feedback`; `xmin_age` is how far it lags the current transaction id.
- `retained_wal_bytes` is the WAL this slot makes the instance keep: measured from the current WAL position on a primary, and from the replay position on a standby.

On a standby with no slots the list is empty and the verdict OK.

## An inactive slot

```bash
~/kbdiag slots
echo EXIT_CODE=$?
```

```text
slots  FAIL  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:39:37+08:00)

[FAIL] slot.inactive  复制槽 repmgr_slot_2 未激活，保留 0 MB WAL，xmin 6021 压着视界
  verify: kbdiag status  # 在备库上运行，确认它是否在线、是否在接收 WAL

slot.list: 1 rows
slot_name      slot_type  active  active_pid  xmin  catalog_xmin  xmin_age  restart_lsn  retained_wal_bytes
repmgr_slot_2  physical   false   -           6021  -             0         0/A40F4578   48
EXIT_CODE=2
```

- Nothing consumes an inactive slot, yet it keeps WAL, and one with an `xmin` stops VACUUM from removing old row versions. Left alone it can fill the disk, so it is a FAIL straight away, with no time threshold.
- Right after the injection little WAL is retained (48 bytes, shown as 0 MB); in a real failure it keeps growing.
- The `verify` line suggests running `kbdiag status` on the standby first to see whether it is alive and receiving WAL. Drop the slot only when the standby is really gone; kbdiag never drops it for you.
- With a FAIL the exit code is 2.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 2 | FAIL |
| 3 | UNKNOWN: data not collected |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
