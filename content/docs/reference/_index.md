---
title: "User manual"
weight: 90
type: docs
cascade:
  type: docs
---

Snapshot of the [kbdiag README](https://github.com/Kevin-wenyu/kbdiag#readme) at generation time.

Command pages: [`status`]({{< relref "/docs/reference/status" >}}) · [`sessions`]({{< relref "/docs/reference/sessions" >}}) · [`session`]({{< relref "/docs/reference/session" >}}) · [`locks`]({{< relref "/docs/reference/locks" >}}) · [`txn`]({{< relref "/docs/reference/txn" >}}) · [`waits`]({{< relref "/docs/reference/waits" >}}) · [`slots`]({{< relref "/docs/reference/slots" >}})

KingbaseES command-line diagnostics. One static binary that talks the wire protocol directly: no `ksql`, no interactive screens. Each command runs a single read-only look at a live instance and prints a verdict, the evidence, and the next command to run. Works on single nodes and on repmgr primary/standby clusters.

This is kbdiag 2.0, rewritten in Go; `v2.0.0-alpha.1` is its first release. The shell toolkit (`v1.x`) is frozen; use release [`v1.0.0`](https://github.com/Kevin-wenyu/kbdiag/releases/tag/v1.0.0) if you need it.

## Install

Build a static Linux binary (Go from `go.mod`), then copy it to the database host:

```bash
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w -X main.version=$(git describe --tags --match 'v2*' --always)" -o kbdiag ./cmd/kbdiag
scp kbdiag kingbase@db-host:~/kbdiag
```

Use `GOARCH=arm64` for ARM hosts. The binary has no runtime dependencies.

## Quick start

```bash
sudo -iu kingbase        # run as the database OS user
~/kbdiag status          # what is this instance
~/kbdiag sessions        # who is connected, who is idle in transaction
~/kbdiag locks           # who waits for a lock, and who blocks them
echo $?                  # 0 OK, 1 WARN, 2 FAIL, 3 UNKNOWN
```

## Commands

| Command | What it shows | Flags |
|---|---|---|
| `status` | Version, data directory, port, role; each standby (on a primary) or the WAL upstream (on a standby); uptime, connections used / usable, database sizes, disk of the data directory (local runs only). FAIL when ordinary users can no longer connect; WARN when a standby is not receiving WAL | |
| `sessions` | Who holds the connections (counted by user, database, application, client), then the client sessions that are not idle, longest transaction first; WARN on long idle in transaction. JSON always carries every session | `--all`, `--limit N`, `--idle-in-txn-warn S` |
| `session <pid>` | One session: who and what it is, its full SQL, the lock it waits for and who blocks it, whom it blocks, what it holds | `--lock-wait-warn S`, `--idle-in-txn-warn S` |
| `locks` | Who blocks the most (and what it holds), then every lock wait, longest first, with its direct blockers; WARN on long waits | `--limit N`, `--lock-wait-warn S` |
| `txn` | The oldest xid holding back vacuum and who holds it, open transactions, prepared (2PC) ones; WARN on old ones | `--limit N`, `--xact-warn S`, `--prepared-warn S` |
| `waits` | What the sessions doing something wait on, grouped by wait event and state, biggest pile first; idle sessions and background processes only counted | |
| `slots` | Replication slots, inactive ones and the ones keeping the most WAL first; WARN on inactive ones | |

Defaults: idle in transaction 300 s, lock wait 10 s, transaction 300 s, prepared transaction 900 s, all WARN. `--limit` only trims what is shown; findings always cover every row.

## Connection

| Flag | Default |
|---|---|
| `--host` | `/tmp` (local socket `/tmp/.s.KINGBASE.54321`); a host name or IP for TCP |
| `-p, --port` | `54321` |
| `-d, --dbname` | `test` |
| `-U, --user` | `system` |
| `--timeout` | `10s` per query |
| `--json` | print the report as JSON |

The password comes from `PGPASSWORD` or `~/.pgpass`. Every connection is a read-only transaction with a `lock_timeout`; kbdiag never changes anything. Suggested fixes (such as `ROLLBACK PREPARED`) are printed, never run.

## Output

```text
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-26T19:41:41+08:00)

[WARN] lock.waiting  session 803890 has waited 14s for AccessShareLock on public.kbdiag_inj_lock, blocked by 803881
  verify: kbdiag session 803881  # what the blocking session is doing

blockers: 1
  pid     blocks  holds
  803881  1       public.kbdiag_inj_lock AccessExclusiveLock

waiting: 1
  pid     object                  wants            waited  blocked by
  803890  public.kbdiag_inj_lock  AccessShareLock  14s     803881
```

- First line: command, verdict, and context (version, role, user@location, collection time).
- Findings: an id, a symptom, and a `verify` or `fix` next step.
- Data: laid out for reading, sizes and durations in readable units; `-` is null, `?` is hidden from this account. `--json` gives every probe's raw table (bytes, seconds) with stable field names.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN |
| 2 | FAIL |
| 3 | UNKNOWN: something could not be collected or seen, so kbdiag will not claim OK |
| 64 | Usage error |
| 69 | Cannot connect |

## Privileges

Run as `system` over the local socket for the full picture. An account without a monitoring role cannot see other sessions' state, timings or SQL; kbdiag lists those fields under `redacted` and answers UNKNOWN instead of OK, unless what it can see is already WARN or FAIL. Granting `sys_monitor` lifts this. On a standby, prepared transactions are `not_applicable` (run `txn` on the primary); this does not change the verdict.

## Requirements

- KingbaseES V8R6 (tested on V008R006C009B0014)
- Linux amd64 or arm64
- repmgr is optional
