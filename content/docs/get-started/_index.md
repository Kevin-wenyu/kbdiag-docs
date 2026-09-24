---
title: "Your first check"
description: "Build the binary, install it on the database host, connect, and read the verdict and exit code."
weight: 30
---

Build kbdiag once, copy it to the **KingbaseES host**, and run `status` and `sessions`. Then decide what needs a closer look.

## 1. Prepare {#requirements}

- A running KingbaseES V8R6 instance (tested on V008R006C009B0014).
- Access to the `kingbase` OS user on the database host.
- A machine with Go (the version in the repository's `go.mod`) and git, to build the binary. It can be your laptop; the database host needs nothing but the binary.

## 2. Build and install {#install}

On the build machine:

```bash
git clone https://github.com/Kevin-wenyu/kbdiag.git
cd kbdiag
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w -X main.version=$(git describe --tags --match 'v2*' --always)" -o kbdiag ./cmd/kbdiag
scp kbdiag kingbase@db-host:~/kbdiag
```

Use `GOARCH=arm64` for ARM hosts. The result is one static file with no runtime dependencies, so an offline host only needs the file copied over.

On the database host:

```bash
sudo -iu kingbase
chmod +x ~/kbdiag
~/kbdiag --version
```

## 3. Connect {#connection}

By default kbdiag connects over the local socket `/tmp/.s.KINGBASE.54321` to database `test` as user `system`, the way `ksql test system` does. Change the target with flags:

| Flag | Default |
|---|---|
| `--host` | `/tmp` (socket directory); a host name or IP for TCP |
| `-p, --port` | `54321` |
| `-d, --dbname` | `test` |
| `-U, --user` | `system` |
| `--timeout` | `10s` per query |

The password comes from `PGPASSWORD` or `~/.pgpass`. If kbdiag cannot connect, it prints the error and exits with 69; check the port, socket directory and `sys_hba.conf` before anything else.

An account without a monitoring role cannot see other sessions' state, timings or SQL. kbdiag lists those fields under `redacted` and answers UNKNOWN rather than OK; grant `sys_monitor` or use `system` for the full picture.

## 4. Run your first checks {#run-check}

```bash
~/kbdiag status
echo "exit code: $?"
~/kbdiag sessions
echo "exit code: $?"
```

Read `$?` right after the command; the next command replaces it. `status` tells you what the instance is and whether connections are running out. `sessions` lists everyone connected and warns about sessions left idle in transaction.

## 5. Read the verdict and exit code {#exit-codes}

The first line of every report carries the verdict, and the exit code says the same thing:

| Exit code | Verdict | Next step |
|---|---|---|
| `0` | OK | Nothing crossed a threshold in this sample |
| `1` | WARN | Read each finding and run its `verify` command |
| `2` | FAIL | Same, sooner: something is already broken or about to be |
| `3` | UNKNOWN | Something could not be collected or seen; check privileges and the `redacted` list |
| `64` | Usage error | Check the command and flags |
| `69` | Cannot connect | Check the connection first; nothing was looked at |

A WARN or FAIL finding wins over UNKNOWN: if kbdiag found a problem in what it could see, it says so.

[Read a real result line by line](reading-results/)

## 6. Follow the evidence {#next-check}

| You see | Next command | Look for |
|---|---|---|
| A lock wait | `~/kbdiag session <blocker pid>` | What the blocker is doing and how long its transaction has been open |
| Idle in transaction | `~/kbdiag session <pid>` | The locks it holds and whether it blocks anyone |
| An old or prepared transaction | `~/kbdiag txn` | Transaction age, the prepared transaction's gid and owner |
| Many sessions waiting | `~/kbdiag waits` | Which wait event they share |
| Connections near the limit | `~/kbdiag sessions --limit 0` | A pile-up by user, application or client address |
| An inactive slot | `~/kbdiag sessions` on the standby | Whether it is up and has a `walreceiver` |

Each finding already prints the right one of these as its `verify` line.

## Done {#done}

You have built and installed kbdiag, connected to the right instance, run `status` and `sessions`, and know what their exit codes mean.

[Explore capabilities](../features/) · [Look up command options](../reference/)
