---
title: "top: cumulative top SQL"
description: "Cumulative top SQL from sys_stat_statements; says so when statements are not being collected."
weight: 170
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. Nothing was injected. In the lab `sys_stat_statements.track` is `none` on both nodes, so statements are not being collected and `top` has no rows to show. This page shows that case, which is what the lab really looks like. The case with statistics on was not captured (see the last section).

## Usage

```text
kbdiag top [--limit N] [--by time|mean|calls|io|temp] [--json]
```

| Option | Effect |
|---|---|
| `--limit N` | Show at most N statements; default 20, `0` for all |
| `--by ORDER` | Sort by `time` (total execution time, the default), `mean` (time per call), `calls`, `io` (blocks read) or `temp` (temp blocks written). It is a sort, not a filter |
| `--json` | Print JSON |

Anything else for `--by` is a usage error (exit code 64). Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## Statements not being collected

```bash
~/kbdiag top
echo EXIT_CODE=$?
```

```text
top  UNKNOWN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:58+08:00)

statements: skipped  (sys_stat_statements.track=none: statements are not being collected; set it to top or all)
EXIT_CODE=3
```

- `skipped` with the reason written out, and the verdict is UNKNOWN: an empty table with an OK would claim "no expensive SQL" when nothing was measured. The standby (kes-node2) prints the same.
- The switch to turn it on is `sys_stat_statements.track` (`top` or `all`). Two other reasons get their own text: the library is not in `shared_preload_libraries` (needs a restart), or the extension is not installed in this database (`CREATE EXTENSION sys_stat_statements`, or use `-d`).
- The view is read from the schema where `sys_extension` says the extension lives, not through the `search_path`: a view of the same name in `public` could otherwise feed kbdiag false numbers.
- This connection's `track=none` does not by itself mean no data (a role or database can set it, and `save=on` keeps old data), so kbdiag reads the view anyway and writes `skipped` only when there is no row at all.

## With statistics on: not captured

Taken from the source, not captured: with statements collected, the output is a table with the columns `total`, `share`, `calls`, `mean`, `rows`, `read`, `temp`, `user`, `database` and `query`, under a header that says the numbers are cumulative since the last reset.

- `share` is the statement's part of all execution time, the direct answer to "where does the database's time go". Which SQL is too expensive has no objective line, so `top` only shows and has no findings.
- The numbers are cumulative since the last statistics reset. This version has no `sys_stat_statements_info`, so the reset time cannot be read, and the header says so. `read` and `temp` are blocks.
- With `track=all`, statements run inside functions count again inside their callers, so the shares add up to more than 100%, and the text says so. With `track=none` and rows present, it says they were collected earlier, or for roles and databases that set `track` themselves.
- Times use the unit that fits the size (0.09 ms, 503 ms, 1.75 s). A query that this account may not see is `?`.
- `top --interval` (the last N seconds) is not part of this version.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK: statements collected |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error, including an invalid `--by` |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
