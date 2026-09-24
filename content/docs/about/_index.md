---
title: "About kbdiag"
description: "Read-only command-line diagnostics for KingbaseES: a verdict, the evidence and the next step."
weight: 10
---

## What problem does it solve? {#purpose}

When something feels wrong with a database, the first questions are usually the same: who is connected, who is waiting for a lock and who blocks them, which transaction has been open too long, whether a standby's slot is piling up WAL. Answering them means remembering system views and joining them by hand.

kbdiag packages those questions into commands. Each command runs one read-only look at a live instance and prints a verdict, the evidence it is based on, and the next command to run.

## Who is it for? {#audience}

| Reader | Start with | What you get |
|---|---|---|
| Operations | `status`, `sessions` | Instance facts, connection pressure, sessions left idle in transaction |
| DBAs | `locks`, `session <pid>`, `txn` | Who blocks whom, what a session holds, old and prepared transactions |
| Monitoring scripts | any command, `--json` | A verdict in the exit code and a stable JSON report |

## Look, query, diagnose {#layers}

1. **Look:** one command gives one fact, such as the instance's role or its connection usage (`status`).
2. **Query:** a focused command looks at one dimension in depth, such as lock waits (`locks`) or one session (`session <pid>`).
3. **Diagnose:** correlating several dimensions into a root cause is planned for later versions. This version does look and query; each finding's `verify` line tells you which query to run next.

## Runtime and requirements {#requirements}

- KingbaseES V8R6 (tested on V008R006C009B0014), standalone or repmgr primary/standby.
- One static Linux binary (amd64 or arm64). It speaks the wire protocol itself: no `ksql`, no runtime, no service.
- Run it on the database host as the `kingbase` OS user over the local socket for the full picture. Other accounts and TCP work too; what they cannot see is reported, not hidden.
- repmgr is optional.

## Operating boundaries {#boundaries}

- **Read-only.** Every connection is a read-only transaction with a `lock_timeout`. Suggested fixes, such as `ROLLBACK PREPARED`, are printed for you to review and never run.
- **No pretend OK.** When something the verdict depends on could not be collected or seen, and nothing visible is WARN or FAIL, the verdict is UNKNOWN (exit 3), not OK.
- **One look, not monitoring.** Each run is a single sample. A clean result says nothing about a moment ago or a moment later.

kbdiag 2.0 is a Go rewrite. The shell toolkit (`v1.x`) is frozen; its other commands (health check, reports, performance and advisors) are available in release [`v1.0.0`](https://github.com/Kevin-wenyu/kbdiag/releases/tag/v1.0.0).

## Next {#next}

[Run your first check](../get-started/) · [Explore capabilities](../features/) · [View source](https://github.com/Kevin-wenyu/kbdiag)
