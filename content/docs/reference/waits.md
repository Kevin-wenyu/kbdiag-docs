---
title: "waits: wait events"
description: "Group sessions by wait event and state to see what they wait on right now."
weight: 50
---

Captured on 2026-09-24 (UTC+08) on a local KingbaseES V008R006C009B0014 primary, database `test`, using `~/kbdiag` built from Go source commit `0a4d61e` (static linux/amd64 binary). This is lab evidence, not production validation. The lock wait in the examples was created by a fault-injection script: 364809 holds a table lock idle in transaction, and 364818 waits for it. PIDs, counts and timings belong to this capture only.

## Usage

```text
kbdiag waits [--json]
```

No options of its own. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## Default output

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:38:54+08:00)

wait.summary: 10 rows
wait_event_type  wait_event           state                sessions  pids
Client           ClientRead           idle                 3         [3294 179417 222736]
Activity         KshMain              idle                 2         [3279 3280]
Activity         AutoVacuumMain       -                    1         [3274]
Activity         BgWriterHibernate    -                    1         [3272]
Activity         CheckpointerMain     -                    1         [3271]
Activity         LogicalLauncherMain  -                    1         [3281]
Activity         WalSenderMain        active               1         [364531]
Activity         WalWriterMain        -                    1         [3273]
Client           ClientRead           idle in transaction  1         [364809]
Lock             relation             active               1         [364818]
EXIT_CODE=0
```

- Each row is one (wait event type, wait event, state) group; `sessions` counts them and `pids` lists them. Rows are sorted by count, largest first.
- Sessions not waiting (no wait event) are grouped by state too, so the table covers every session except kbdiag's own connection.
- `waits` summarizes and applies no thresholds: it is OK when every session is visible, and UNKNOWN when some are hidden (see below). The `Lock / relation` row is 364818 waiting for the lock; for how long and who blocks it, use [`locks`]({{< relref "/docs/reference/locks" >}}).

## Without monitoring privileges

Connected remotely as `kbdiag_ro`, which has no monitoring role:

```bash
PGPASSWORD=... ~/kbdiag waits --host 127.0.0.1 -U kbdiag_ro
echo EXIT_CODE=$?
```

```text
waits  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-24T04:41:05+08:00)

wait.summary: 2 rows
wait_event_type  wait_event     state   sessions  pids
-                -              -       12        [3271 3272 3273 3274 3279 3280 3281 3294 179417 222736 36...
Activity         WalSenderMain  active  1         [366619]

redacted: wait.summary.wait_event_type in 12 rows (insufficient_privilege)
redacted: wait.summary.wait_event in 12 rows (insufficient_privilege)
redacted: wait.summary.state in 12 rows (insufficient_privilege)
EXIT_CODE=3
```

- Hidden sessions have no wait event or state, so they fall into the all-empty row (12 here); `redacted` says this is a privilege issue, not an absence of waits.
- With hidden sessions kbdiag cannot claim nothing is waiting, so the verdict is UNKNOWN, exit code 3.
- Long cells are cut in text output (ending in `...`); `--json` gives the full PID list.
- Granting the `sys_monitor` role restores the full picture.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
