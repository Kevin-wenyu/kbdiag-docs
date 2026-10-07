---
title: "freeze: wraparound distance"
description: "How far each database is from transaction ID wraparound, and the oldest tables of this one."
weight: 90
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. Both nodes were healthy and nothing was injected, so every example is OK. The WARN and FAIL cases were not produced in the lab (see the last section). Values belong to this capture only.

## Usage

```text
kbdiag freeze [--limit N] [--json]
```

| Option | Effect |
|---|---|
| `--limit N` | Show at most N tables; default 20, `0` for all |
| `--json` | Print JSON |

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}). `--limit` only trims the table list; the findings always cover every database and every table.

## Healthy primary

```bash
~/kbdiag freeze
echo EXIT_CODE=$?
```

```text
freeze  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:54+08:00)

limits
  autovacuum_freeze_max_age            200000000
  autovacuum_multixact_freeze_max_age  400000000
  xid stop limit                       2146483647  (new transaction IDs are refused)

databases: 7
  name       xid age  of freeze max  mxid age  xids left
  esrep      5672     0%             0         2146477975
  kingbase   5672     0%             0         2146477975
  mydb       5672     0%             0         2146477975
  security   5672     0%             0         2146477975
  template0  5672     0%             0         2146477975
  template1  5672     0%             0         2146477975
  test       5672     0%             0         2146477975

tables in test: 288, oldest first
  relation                                    kind   xid age  mxid age  heap (est.)
  information_schema.sql_features             table  5672     0         56 kB
  information_schema.sql_implementation_info  table  5672     0         8192 bytes
  information_schema.sql_languages            table  5672     0         8192 bytes
  information_schema.sql_packages             table  5672     0         8192 bytes
  information_schema.sql_parts                table  5672     0         8192 bytes
  information_schema.sql_sizing               table  5672     0         8192 bytes
  information_schema.sql_sizing_profiles      table  5672     0         0 bytes
  pg_catalog._agg                             table  5672     0         24 kB
  pg_catalog._am                              table  5672     0         8192 bytes
  pg_catalog._amop                            table  5672     0         80 kB
  pg_catalog._amproc                          table  5672     0         40 kB
  pg_catalog._anonpolicy                      table  5672     0         0 bytes
  pg_catalog._att                             table  5672     0         2024 kB
  pg_catalog._attdef                          table  5672     0         24 kB
  pg_catalog._audit_blocklog                  table  5672     0         0 bytes
  pg_catalog._audit_userlog                   table  5672     0         0 bytes
  pg_catalog._authid                          table  5672     0         8192 bytes
  pg_catalog._authmem                         table  5672     0         8192 bytes
  pg_catalog._cast                            table  5672     0         24 kB
  pg_catalog._ce_col                          table  5672     0         0 bytes
  ... 268 more not shown (--limit 0 shows all)
EXIT_CODE=0
```

- `limits` shows the two lines kbdiag compares against, both taken from the server: `autovacuum_freeze_max_age` (WARN line: autovacuum must start freezing by force here) and the stop limit (FAIL line: the server refuses to hand out new transaction IDs, so write transactions fail). The stop limit is a constant of the PG12 kernel, 1 million xids before the wraparound point (2^31 - 1); for multixacts it is 100. kbdiag does not invent a threshold of its own.
- `databases` is one row per database: `xid age` and `mxid age` are the age of its oldest unfrozen xid and multixact, `of freeze max` is the xid age as a percentage of `autovacuum_freeze_max_age`, and `xids left` is how many more transaction IDs can be handed out before the stop limit.
- The verdict is judged per database. A database is as old as its oldest table, so reporting every table would repeat one problem dozens of times. `tables` is shown only for the database you are connected to, oldest first; use `kbdiag -d <database> freeze` for another one.
- `heap (est.)` is `relpages x block_size`, an estimate. The exact size functions take a lock on every table, and during a rescue (VACUUM FULL, TRUNCATE are common then) they would make the whole probe wait until `lock_timeout` and fail.
- Tables whose `relfrozenxid` is 0 (such as `_kingbase_loginfo`) are left out: `age(0)` reads as 2147483647 and would raise a false FAIL.
- On the standby the ages are replicated and equal the primary's (the captured output on kes-node2 shows the same 5672 for every database). A VACUUM to fix a finding must still be run on the primary.

Options as the binary prints them:

```bash
~/kbdiag freeze --help
echo EXIT_CODE=$?
```

```text
How far each database is from transaction ID wraparound; the oldest tables of this one

Usage:
  kbdiag freeze [flags]

Flags:
  -h, --help        help for freeze
      --limit int   max rows to show, 0 for all (findings still cover every row) (default 20)

Global Flags:
  -d, --dbname string      database to connect to (default "test")
      --host string        server host, or socket directory (default /tmp)
      --json               print the report as JSON
  -p, --port int           server port (default 54321)
      --timeout duration   statement timeout for each query (default 10s)
  -U, --user string        database user (password from PGPASSWORD or ~/.pgpass) (default "system")
EXIT_CODE=0
```

## WARN and FAIL: not produced in the lab

Neither finding was produced, because it would take pushing the transaction counter to hundreds of millions of xids. Taken from the source, not captured, both with the id `freeze.database_age` (and `freeze.table_age` on `kbdiag table`):

- WARN: a database's xid age is at or above `autovacuum_freeze_max_age`, or its multixact age is at or above `autovacuum_multixact_freeze_max_age`. The anti-wraparound autovacuum is due or cannot finish.
- FAIL: the xid age is within 1 million of wraparound (or the multixact age within 100). The server refuses new transaction IDs, so writes fail.
- Next steps point to `kbdiag txn` and `kbdiag slots` (what holds the horizon back), to `kbdiag -d <database> freeze` for the other databases, and to `VACUUM (FREEZE)` run on the primary.
- If the limits could not be read, a FAIL can still be judged (the stop limit is a constant); below it the verdict is UNKNOWN.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: past `autovacuum_freeze_max_age` (not produced in the lab) |
| 2 | FAIL: at the stop limit (not produced in the lab) |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
