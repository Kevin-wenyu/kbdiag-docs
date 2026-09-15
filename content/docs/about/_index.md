---
title: "About kbdiag"
description: "Command-line health checks, investigations and diagnostics for KingbaseES."
weight: 10
---

## What problem does it solve? {#purpose}

Database investigations often involve querying system views, inspecting the host and connecting scattered observations. kbdiag packages common checks into commands so you can establish the state of an instance and investigate a specific problem.

It runs on the database host, queries the instance and prints results. Use it for routine inspections, incident investigation and script integration.

## Who is it for? {#audience}

| Reader | Start with | What you get |
|---|---|---|
| Operations | `status`, `check`, `report` | Instance facts, health findings and a handover report |
| DBAs | `perf`, `locks`, `stmt`, `idx` | Evidence about sessions, SQL and objects |
| Incident responders | `diagnose`, `snapshot` | Diagnostic recommendations and captured incident state |

## How do the three layers work? {#layers}

1. **Inspect:** use `check` to find signals worth investigating.
2. **Investigate:** use a focused command, such as `locks wait` when lock waits appear.
3. **Diagnose:** use `diagnose` to review correlated signals, then verify with specific commands.

Each layer also works independently. Interpret recommendations with your workload, collection time and database environment in mind; they do not cover every possible failure.

## Runtime and requirements {#requirements}

- The documented target is **KingbaseES V8R6+**; available evidence depends on version, privileges and extensions.
- Run the distributed `dist/kbdiag` file on the database host as the `kingbase` OS user.
- It uses the database's `ksql` client and host utilities. No separate kbdiag service is needed.
- Standalone and repmgr HA environments are supported. Without repmgr, relevant cluster features skip or report unavailable information according to their implementation.
- Query commands and judgment commands have different exit behavior. Read [exit codes](../get-started/#exit-codes) before integrating them into scripts.

## Operating boundaries {#boundaries}

`advisor --fix` generates proposed SQL. `kill` can cancel queries or terminate sessions. `workload` may supplement snapshots under specific conditions. `snapshot` captures incident state and cannot restore a database.

Do not treat the whole toolkit as read-only or as an automatic repair system. See [capabilities](../features/) for individual boundaries and dependencies.

## Next {#next}

[Run your first inspection](../get-started/) · [Explore capabilities](../features/) · [View source](https://github.com/Kevin-wenyu/kbdiag)
