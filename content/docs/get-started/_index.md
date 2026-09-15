---
title: "Your first inspection"
description: "Install, configure the connection, run health checks and interpret the results."
weight: 30
---

Run `status` and `check`, then decide what needs further investigation. Run these commands on the **KingbaseES host**, not on the website build machine.

## 1. Prepare the environment {#requirements}

- A running KingbaseES V8R6+ instance.
- Access to the `kingbase` OS user and the database's `ksql` client.
- The correct port, database and database user, with access to the required system views.
- repmgr is needed for relevant cluster features, not standalone health checks.

## 2. Install {#install}

Switch to the database OS user:

```bash
sudo -i -u kingbase
```

Download the single file:

```bash
curl -fsSL https://raw.githubusercontent.com/Kevin-wenyu/kbdiag/main/dist/kbdiag \
  -o ~/kbdiag
chmod +x ~/kbdiag
~/kbdiag --version
```

For an offline host, download `dist/kbdiag` on a connected machine, copy it to `~/kbdiag` on the database host, and set its executable permission. Downloading to an existing path replaces that file; keep a copy before updating if needed.

## 3. Confirm the target instance {#connection}

Defaults are port `54321`, database `test` and database user `system`. Directory detection does not automatically resolve every connection parameter. Start with:

```bash
~/kbdiag instances
~/kbdiag status
```

On hosts with multiple instances, use `instances` to identify the target port and paths. If necessary, edit `~/.kbdiagrc`, replacing these examples with actual values:

```bash
KB_PORT=54321
KB_DB=test
KB_SUPERUSER=system
KB_BIN_DIR=/actual/install/path/bin
KB_DATA_DIR=/actual/data/path
```

Retry `~/kbdiag status`. Edit existing entries if the file already exists; it is sourced as Shell configuration.

**Resolve connection problems first:** check the process, port, authentication, paths and privileges. Unavailable evidence does not mean health. A failed database connectivity check makes `check` return `2`.

## 4. Run the health check {#run-check}

```bash
~/kbdiag check
check_rc=$?
printf 'check exit code: %s\n' "$check_rc"
```

Save `$?` immediately: later commands replace it. For additional detail:

```bash
~/kbdiag check -v
~/kbdiag check --os
```

`-v` expands some underlying data; `--os` adds host conformance checks. Findings reflect the current sample and thresholds, not every moment in the instance's lifetime.

## 5. Interpret exit codes {#exit-codes}

| `check` exit code | Meaning | Next step |
|---|---|---|
| `0` | No WARN / FAIL in this inspection | Keep the results; investigate relevant dimensions if the application still has problems |
| `1` | At least one warning | Review the finding with the workload and thresholds in mind |
| `2` | A FAIL finding or failed database connectivity | Identify the failed check and connection state first |

This table is specific to `check`. Most data-query commands require `--exit-code` to reflect findings in their exit status; usage and runtime errors can also produce nonzero exits.

[Read an explicitly illustrative result](reading-results/)

## 6. Follow the evidence {#next-check}

| Finding | Next command | Look for |
|---|---|---|
| Lock waits | `~/kbdiag locks wait` | Waiting and blocking information |
| Active slow queries | `~/kbdiag perf slow` | Sessions, duration and SQL |
| Replication findings | `~/kbdiag replication` | Node role and replication state |
| Space findings | `~/kbdiag space` | Host storage and database objects |
| Multiple related signals | `~/kbdiag diagnose` | Evidence, recommendations and verification paths |

To create a handover file, choose a new filename:

```bash
~/kbdiag report inspection.md
```

The report is written to the current directory. Read its WARN / FAIL summary and details; the command can return nonzero because it found problems.

## Completion criteria {#done}

You have identified the target instance, run `status` and `check`, understood the check's exit code, and found a follow-up command for a finding.

[Explore capabilities](../features/) · [Look up command options](../reference/)
