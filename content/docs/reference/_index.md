---
title: "User manual"
weight: 30
type: docs
cascade:
  type: docs
---

Snapshot of the [kbdiag README](https://github.com/Kevin-wenyu/kbdiag#readme) at generation time.

KingbaseES command-line DBA toolkit. Non-interactive — runs directly against a live instance and outputs status, topology, replication lag, performance bottlenecks, index health, column statistics, and optimization advice. Supports single-node and HA clusters (repmgr).

## Install

Single-file, no dependencies:

```bash
curl -fsSL https://raw.githubusercontent.com/Kevin-wenyu/kbdiag/main/dist/kbdiag \
  -o ~/kbdiag && chmod +x ~/kbdiag
```

## Update

```bash
~/kbdiag update
```

## Team Deployment

Push kbdiag to multiple hosts at once:

```bash
# Create a hosts file (one user@host per line)
cp scripts/hosts.example my-hosts.txt
vim my-hosts.txt

# Deploy
bash scripts/deploy.sh my-hosts.txt

# Custom SSH port or destination
SSH_PORT=2222 DB_USER=kingbase bash scripts/deploy.sh my-hosts.txt
```

## Quick Start

```bash
# Switch to the kingbase OS user first
sudo -i -u kingbase

# Full scan (daily health check)
~/kbdiag all

# Health gate (suitable for monitoring scripts)
~/kbdiag check
echo $?   # 0=all OK  1=WARN  2=FAIL

# Verbose DBA view
~/kbdiag check -v
~/kbdiag perf slow -v
```

kbdiag auto-detects the install/data dir from the running `kingbase` process, so this usually works with zero config. If your install layout is unusual and `all`/`status` still can't find it, set `KB_BIN_DIR`/`KB_DATA_DIR` explicitly — see [Environment Variables](#environment-variables).

## Global Flags

```
kbdiag [global-flags] <command> [subcommand] [command-flags]

  -v, --verbose       Show full underlying data
  -q, --quiet         Only show WARN/FAIL (suppress OK/INFO)
  -n N, --top N       Limit result rows (default: 10)
  --format text|json  Output format (default: text). JSON is supported
                      by every command except `watch`.
  --exit-code         Data-query commands (DBA-tier + most OPS-tier)
                      default to exit 0 regardless of findings; this
                      makes them exit with their worst verdict instead
                      (0=OK / 1=WARN / 2=FAIL) — useful for monitoring
                      scripts. Judgment commands (check, cluster ready,
                      diagnose, report) already reflect verdict
                      unconditionally and ignore this flag.
  --no-color          Disable ANSI colors
  --timeout N         DB query timeout in seconds (default: 10)
```

## Command Reference

### [OPS] Quick Fact Lookup

One command, one deterministic answer — no interpretation required.

| Command | Description |
|---------|-------------|
| `status` | Process, connectivity, role, uptime |
| `instances` | List all kingbase processes on this host (PID, port, data dir, bin dir, OS user) — disambiguates multi-instance hosts |
| `license` | License validity, expiry date, type (trial/commercial) |
| `cluster [ready]` | Repmgr cluster topology; `ready` = failover readiness checklist (topology, repmgrd, arbitration, slots, standby promotability, VIP), exit 0/1/2 |
| `replication` | Replication lag / standby connections |
| `check [--os]` | 15-item health threshold check — exit 0=OK / 1=WARN / 2=FAIL; `--os` adds OS conformance (THP, swappiness, swap, overcommit, ulimits, NTP, data-dir FS, CPU governor) |
| `space [frag]` | Disk, tables, WAL, archive; `frag` adds fragmentation |
| `backup` | Backup & WAL archiving readiness: archiver state, pending WAL, sys_rman, slots |
| `report [file]` | Verdict-first Markdown inspection report assembled from existing checks, exit 0/1/2 |
| `params [pattern]` | Instance parameters |
| `update` | Update kbdiag to the latest version from GitHub |

### [DBA] Single-Dimension Deep Query

Answers one specific question in depth; also used to verify a ROOT-CAUSE finding.

| Command | Description |
|---------|-------------|
| `sessions` | Non-idle session list |
| `locks [hold\|wait\|deadlock]` | Lock analysis |
| `perf [slow\|bloat\|vacuum\|index\|wait\|io\|wal\|top]` | Performance diagnostics |
| `sql [pid\|all]` | SQL text + EXPLAIN for a session |
| `stmt [queryid]` | SQL history stats — Top N by mean/total/IO/calls (AWR-style) |
| `workload [--from <dur>] [--to <dur>] [--no-snapshot]` | Interval workload-diff report (sys_kwr AWR-style, falls back to sys_stat_sysmetric_history) |
| `explain <queryid\|"SQL">` | Plan analysis: EXPLAIN + red flags (seq scans, nested loops, sorts) |
| `wait` | Wait event distribution |
| `progress` | Long-running operation progress |
| `jobs` | Scheduler job health (kdb_schedule: broken jobs, failed runs) |
| `partition` | Partition table health: missing DEFAULT, size skew, orphan (empty) partitions |
| `stat` | Throughput metrics (TPS, buffer hit rate) |
| `obj <schema.table>` | Object deep-dive: size, indexes, constraints |
| `colstat <schema.table> [--col <col>]` | Column statistics (n_distinct, MCV, correlation) |
| `temp` | Temp file and sort spill analysis |
| `idx [unused\|dup\|bloat\|missing]` | Index health analysis |
| `kill [--terminate] [pid\|--long N\|--idle-txn N] [--dry-run] [--force]` | Cancel or terminate queries |
| `conf [diff]` | Configuration restart-pending status / cross-node comparison |
| `audit` | Security and compliance checks (roles, hba connection whitelist, KingbaseES security extensions) |
| `logs` | Log file analysis (slow queries, errors) |
| `snapshot [file]` | Pack volatile incident state (sessions, locks, waits, perf, log tail) into a literal-masked tar.gz — not a backup |

### [ROOT-CAUSE] Multi-Dimension Correlation

Full diagnostic chain: symptom → evidence → cause → fix. Each conclusion traces back to a DBA-tier command for verification.

| Command | Description |
|---------|-------------|
| `diagnose [--full]` | Root-cause diagnostic report (fast <15s; `--full` ~90s) |
| `advisor [index\|vacuum\|params\|analyze] [--fix]` | Consolidated DBA recommendations; `--fix` emits executable SQL |

### [UTIL]

| Command | Description |
|---------|-------------|
| `watch <N> <cmd>` | Repeat any command every N seconds |
| `remote <nodes> <cmd>` | Multi-node batch diagnostics |
| `all` | Run all checks |

## Configuration File

Per-host settings can be placed in `~/.kbdiagrc` (sourced at startup before any defaults):

```bash
# ~/.kbdiagrc — example
KB_PORT=5432
KB_BIN_DIR=/opt/kingbase/bin
KB_SUPERUSER=dba
KB_SLOW_THRESHOLD=3
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KB_PORT` | `54321` | Database port |
| `KB_BIN_DIR` | `/home/kingbase/cluster/install/kingbase/bin` | Binary directory (auto-detected from the running process if this default doesn't exist) |
| `KB_DATA_DIR` | `/home/kingbase/cluster/install/kingbase/data` | Data directory (auto-detected from the running process if this default doesn't exist) |
| `KB_SUPERUSER` | `system` | Superuser name |
| `KB_DB` | `test` | Database name |
| `KB_WARN_CONN` / `KB_FAIL_CONN` | `70` / `90` | Connection usage % |
| `KB_WARN_LAG` / `KB_FAIL_LAG` | `30` / `300` | Replication lag (seconds) |
| `KB_SLOW_THRESHOLD` | `5` | Slow query threshold (seconds) |
| `KB_WARN_SWAPPINESS` | `10` | vm.swappiness upper bound (`check --os`) |
| `KB_WARN_NOFILE` / `KB_WARN_NPROC` | `65536` / `4096` | ulimit lower bounds (`check --os`) |
| `KB_WARN_HIT` / `KB_FAIL_HIT` | `95` / `90` | Buffer hit rate % lower bound |

## Requirements

- Run as the `kingbase` OS user (`sudo -i -u kingbase`)
- KingbaseES V8R6+
- repmgr optional (cluster commands skipped when absent)

