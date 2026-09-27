---
title: "waits: wait events"
description: "What the working sessions are waiting on right now, biggest pile first."
weight: 50
---

Captured on 2026-09-27 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `93bf65d` (static linux/amd64 binary). This is lab evidence, not production validation. The sessions in the examples were created by fault-injection scripts: two sessions idle in transaction, two waiting for table locks, and a `pg_sleep(3600)`. PIDs, counts and timings belong to this capture only.

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
waits  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:18+08:00)

not idle: 5
  wait               state                sessions  pids
  Lock:relation      active               2         1045724 1046007
  Client:ClientRead  idle in transaction  2         1045715 1045809
  Timeout:PgSleep    active               1         1046088

not shown: 3 idle, 8 background
EXIT_CODE=0
```

- `not idle` groups the sessions that are doing something by wait event and state. `sessions` counts them and `pids` lists them. The biggest group comes first, since a pile-up is what to look for; on a tie `active` comes first.
- `Lock:relation`: two sessions wait for table locks; who blocks them and for how long is in [`locks`]({{< relref "/docs/reference/locks" >}}).
- `Client:ClientRead` with `idle in transaction`: the sessions wait for their client to send the next statement while holding a transaction open.
- `Timeout:PgSleep` is the injected `pg_sleep`. An active session with no wait event shows `(running)`: on CPU, or in code without a wait event.
- `pids` lists up to 10 PIDs, then `... (+N)`. `--json` has them all.
- `not shown` counts what is left out. `idle` sessions do not answer "where is it stuck". Nor do background processes idling in their main loop (any `Activity` wait, such as a walsender with nothing to send or the checkpointer between checkpoints). A background process stuck on a real wait, for example the checkpointer on `IO:DataFileSync`, is listed with the state `(background)`.

There are no thresholds and no options. Ten sessions waiting on IO can be an incident on one database and routine on another, so waits only reports. A lock wait that is too long is judged by `locks`.

A quiet primary:

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:44+08:00)

not idle: 0

not shown: 3 idle, 8 background
EXIT_CODE=0
```

On a busy primary a walsender catching up may appear with a wait such as `IO:WALRead`; that is normal.

## On a standby

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:21+08:00)

not idle: 1
  wait           state   sessions  pids
  Lock:advisory  active  1         599825

not shown: 3 idle, 4 background
EXIT_CODE=0
```

## Insufficient privilege

Connect as `kbdiag_ro`, which has no monitoring role:

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro waits
echo EXIT_CODE=$?
```

```text
waits  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:35:27+08:00)

not idle: 0

not shown: 1 background, 15 hidden (state unknown)
redacted: 15 rows of wait.summary hide wait, state (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- Other users' sessions have no visible wait event or state. They may be idle or not, so they are counted as `hidden (state unknown)`, not as idle. Sessions that turned off `track_activities` are counted as `untracked (state unknown)` for the same reason.
- With hidden sessions kbdiag cannot claim nothing is waiting, so the verdict is UNKNOWN, exit code 3. Grant `sys_monitor` to see everything.

## JSON

`--json` has every group, idle and background ones included, with the full PID lists: `wait_event_type`, `wait_event`, `state`, `sessions` and `pids`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
