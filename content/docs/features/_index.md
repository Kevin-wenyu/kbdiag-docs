---
title: "Capabilities"
description: "Choose a command by the question you need answered: instance, sessions, locks, transactions, waits, replication slots."
weight: 20
---

Start with the question you need to answer. Examples assume the binary is at `~/kbdiag`; see the [user manual](../reference/) for every flag and output field.

## Instance {#instance}

**What is this instance, and are connections running out?**

```bash
~/kbdiag status
```

Version, role (primary / standby), uptime, database sizes, how many downstreams it sends WAL to, and connections. Connections are measured against what ordinary users may open (`max_connections` less `superuser_reserved_connections`): WARN at 80%, FAIL at 100%, adjustable with `--conn-warn` / `--conn-fail`.

→ [status]({{< relref "/docs/reference/status" >}})

## Sessions {#sessions}

**Who is connected, who is sitting idle in transaction, and what is one session doing?**

```bash
~/kbdiag sessions
~/kbdiag sessions --active
~/kbdiag session <pid>
```

`sessions` lists every session, longest transaction first, and warns about sessions idle in transaction for more than 300 seconds. `session <pid>` shows one session's activity, the locks it holds and whom it blocks or is blocked by.

→ [sessions]({{< relref "/docs/reference/sessions" >}}) · [session]({{< relref "/docs/reference/session" >}})

## Locks {#locks}

**Who is waiting for a lock, and which session blocks them?**

```bash
~/kbdiag locks
```

Each waiting session gets its own finding naming its direct blocker, WARN after 10 seconds. The `verify` line points to the blocker's `session`. When a chain is several sessions long, follow it one hop at a time.

→ [locks]({{< relref "/docs/reference/locks" >}}) · [Scenario: lock waits]({{< relref "/docs/scenarios/lock-waits" >}})

## Transactions {#txn}

**Which transaction has been open too long, and is a prepared (2PC) transaction forgotten?**

```bash
~/kbdiag txn
```

Open transactions WARN at 300 seconds and FAIL at 1800; prepared transactions FAIL at 900 seconds, with a `ROLLBACK PREPARED` / `COMMIT PREPARED` suggestion printed for you to decide. Prepared transactions live on the primary; on a standby they are reported as not applicable.

→ [txn]({{< relref "/docs/reference/txn" >}})

## Waits {#waits}

**What are sessions waiting on right now?**

```bash
~/kbdiag waits
```

Sessions grouped by wait event and state, with their PIDs. It summarizes without thresholds; use `locks` for how long and on whom.

→ [waits]({{< relref "/docs/reference/waits" >}}) · [Scenario: long-running SQL]({{< relref "/docs/scenarios/slow-sql" >}})

## Replication slots {#slots}

**Is a slot keeping WAL for a standby that is gone?**

```bash
~/kbdiag slots
```

An inactive slot keeps WAL and, with an `xmin`, holds back vacuum, so it is a FAIL at once. The `verify` line sends you to the standby to check whether it is alive. kbdiag never drops a slot.

→ [slots]({{< relref "/docs/reference/slots" >}})

## Script integration {#automation}

Every command sets its exit code from the verdict and supports `--json`:

```bash
~/kbdiag --json locks
echo $?   # 0 OK, 1 WARN, 2 FAIL, 3 UNKNOWN, 64 usage error, 69 cannot connect
```

UNKNOWN means something could not be collected or seen, so kbdiag will not claim OK. 69 only means the connection failed; a database that accepts the connection but cannot answer is UNKNOWN. See [exit codes](../get-started/#exit-codes).

## Not in this version {#not-yet}

Replication lag, repmgr cluster checks, slow-SQL history, vacuum and bloat, deadlock history and correlated diagnosis are not in kbdiag 2.0 yet. The frozen shell toolkit [`v1.0.0`](https://github.com/Kevin-wenyu/kbdiag/releases/tag/v1.0.0) still has health checks and reports if you need them.
