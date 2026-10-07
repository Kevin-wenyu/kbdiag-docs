---
title: "table: one table"
description: "One table: size, rows, vacuum and analyze, freeze age, access, indexes."
weight: 160
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. Two WARN/OK examples were created by injection scripts: `public.kbdiag_inj_dead` (table with `autovacuum_enabled=off`, 10000 rows inserted and 5000 deleted) and `public.kbdiag_inj_tbl` (20000 rows inserted, 5000 deleted, with a primary key and a second index). Values belong to this capture only.

## Usage

```text
kbdiag table <name> [--json]
```

`<name>` follows SQL rules: it is resolved with `to_regclass` (as a bound parameter), so an unquoted name folds to lower case and is found through the `search_path`, the same as in `ksql`. Quote it as in SQL for upper case: `'"Name"'`. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}) and it looks at the database you are connected to (use `-d` for another).

An empty name is a usage error (exit code 64). A name that cannot be found is UNKNOWN (3), not a usage error, because the table may live in another database.

## A table on the primary

```bash
~/kbdiag table orders
echo EXIT_CODE=$?
```

```text
table  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:57+08:00)

public.orders  (table)
  size        170 MB  (heap 62 MB, indexes 108 MB, no TOAST)
  rows        1000000 estimated; 1000000 live, 0 dead
  xid age     994  (autovacuum_freeze_max_age 200000000)
  mxid age    0
  reloptions  -

vacuum and analyze
  dead tuples             0, autovacuum threshold 200050
  last vacuum             9d 1h ago  (2 times)
  last autovacuum         never  (0 times)
  last analyze            9d 1h ago  (2 times)
  last autoanalyze        never  (0 times)
  modified since analyze  0

access since the statistics reset
  seq scans     21  (10000000 rows read)
  index scans   0  (0 rows fetched)
  rows written  0 inserted, 0 updated (0 HOT), 0 deleted
  heap blocks   23694 read, 108762 hit (82.1% hit)
  index blocks  6635 read, 10 hit (0.1% hit)

indexes: 3
  name                    size   scans  kind         definition
  idx_orders_user_status  30 MB  0      -            CREATE INDEX idx_orders_user_status ON public.orders USING btree (user_id, status)
  kbdiag_rev_idx          56 MB  0      -            CREATE INDEX kbdiag_rev_idx ON public.orders USING btree (md5((id)::text))
  orders_pkey             22 MB  0      primary key  CREATE UNIQUE INDEX orders_pkey ON public.orders USING btree (id)
EXIT_CODE=0
```

- `size` is exact and split into heap, indexes and TOAST. It uses the same definition as `top-objects`, so the same table shows the same numbers on both. Resolving the name takes no lock, and the size is its own probe: if someone holds the table with VACUUM FULL, only the size is lost (after `lock_timeout`), the rest still shows, and the text points you to `kbdiag locks`.
- `rows` has the estimate (`reltuples`) beside the live and dead tuples from the statistics. `xid age` is the freeze age against `autovacuum_freeze_max_age`.
- `vacuum and analyze`: dead tuples against the autovacuum trigger line, the last manual and automatic vacuum and analyze with their counts, and the changes since the last analyze.
- `access since the statistics reset`: scans, rows read and written, and block cache hits, one decimal place so that a few disk reads are not rounded to 100%.
- `indexes` has size, scan count, whether it is the primary key, and the definition.
- The judgment is the same as in the other commands, not a new rule: the age against the same two lines as `freeze` (finding id `freeze.table_age`), and a table with autovacuum off that is past its line as `vacuum.table_disabled`. Neither fires here, so it is OK.

## The same table on the standby

```bash
~/kbdiag table orders
echo EXIT_CODE=$?
```

```text
table  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:04+08:00)

public.orders  (table)
  size        170 MB  (heap 62 MB, indexes 108 MB, no TOAST)
  rows        1000000 estimated
  xid age     994  (autovacuum_freeze_max_age 200000000)
  mxid age    0
  reloptions  -

statistics: not_applicable  (standby: table statistics are local to each node and stay 0 here; run on the primary)

indexes: 3
  name                    size   scans  kind         definition
  idx_orders_user_status  30 MB  -      -            CREATE INDEX idx_orders_user_status ON public.orders USING btree (user_id, status)
  kbdiag_rev_idx          56 MB  -      -            CREATE INDEX kbdiag_rev_idx ON public.orders USING btree (md5((id)::text))
  orders_pkey             22 MB  -      primary key  CREATE UNIQUE INDEX orders_pkey ON public.orders USING btree (id)
EXIT_CODE=0
```

Table statistics are local to each node, so `statistics` is `not_applicable` and the index scan counts are `-` (NULL, not 0). The size, row estimate and age are replicated and still shown, and the age is still judged.

## A table with autovacuum off

```bash
~/kbdiag table kbdiag_inj_dead
echo EXIT_CODE=$?
```

```text
table  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:13+08:00)

[WARN] vacuum.table_disabled  table public.kbdiag_inj_dead has 5000 dead tuples, past its autovacuum threshold 2050, but autovacuum is off for it (autovacuum_enabled=off): nothing will clean it
  fix: VACUUM public.kbdiag_inj_dead  # connected to database test; turn autovacuum back on with ALTER TABLE ... RESET (autovacuum_enabled) unless it was turned off on purpose

public.kbdiag_inj_dead  (table)
  size        712 kB  (heap 704 kB, indexes 0 bytes, TOAST 8192 bytes)
  rows        10000 estimated; 5000 live, 5000 dead
  xid age     4  (autovacuum_freeze_max_age 200000000)
  mxid age    0
  reloptions  autovacuum_enabled=off

vacuum and analyze
  dead tuples             5000, autovacuum threshold 2050: due (autovacuum is off for this table)
  last vacuum             never  (0 times)
  last autovacuum         never  (0 times)
  last analyze            1s ago  (1 time)
  last autoanalyze        never  (0 times)
  modified since analyze  5000

access since the statistics reset
  seq scans     1  (10000 rows read)
  index scans   -
  rows written  10000 inserted, 0 updated (0 HOT), 5000 deleted
  heap blocks   87 read, 15335 hit (99.4% hit)
  index blocks  -

indexes: 0
EXIT_CODE=1
```

- The finding is the same one `kbdiag vacuum` raises for this table: `vacuum.table_disabled`, with the same `fix`. `reloptions` shows the cause, `autovacuum_enabled=off`, and the text says `due (autovacuum is off for this table)`.
- `modified since analyze` is 5000, matching the 5000 deleted rows.

## A table past its line with autovacuum on

```bash
~/kbdiag table kbdiag_inj_tbl
echo EXIT_CODE=$?
```

```text
table  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:18+08:00)

public.kbdiag_inj_tbl  (table)
  size        2504 kB  (heap 1520 kB, indexes 976 kB, TOAST 8192 bytes)
  rows        20000 estimated; 15000 live, 5000 dead
  xid age     5  (autovacuum_freeze_max_age 200000000)
  mxid age    0
  reloptions  -

vacuum and analyze
  dead tuples             5000, autovacuum threshold 4050: due
  last vacuum             never  (0 times)
  last autovacuum         never  (0 times)
  last analyze            1s ago  (1 time)
  last autoanalyze        never  (0 times)
  modified since analyze  5000

access since the statistics reset
  seq scans     3  (20000 rows read)
  index scans   0  (0 rows fetched)
  rows written  20000 inserted, 0 updated (0 HOT), 5000 deleted
  heap blocks   189 read, 25743 hit (99.2% hit)
  index blocks  122 read, 79374 hit (99.8% hit)

indexes: 2
  name                 size    scans  kind         definition
  kbdiag_inj_tbl_n     520 kB  0      -            CREATE INDEX kbdiag_inj_tbl_n ON public.kbdiag_inj_tbl USING btree (n)
  kbdiag_inj_tbl_pkey  456 kB  0      primary key  CREATE UNIQUE INDEX kbdiag_inj_tbl_pkey ON public.kbdiag_inj_tbl USING btree (id)
EXIT_CODE=0
```

5000 dead tuples against a threshold of 4050, so it says `due`, but autovacuum is on for this table, so the next autovacuum round will take it: no finding, verdict OK.

## A table that does not exist

```bash
~/kbdiag table no_such_table
echo EXIT_CODE=$?
```

```text
kbdiag: no table "no_such_table" in database "test" (unquoted names fold to lower case; quote them as in SQL: '"Name"'; use -d for another database)
table  UNKNOWN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:19+08:00)

table: not found
EXIT_CODE=3
```

The first line is stderr. It says that unquoted names fold to lower case and that `-d` selects another database. Exit code 3 (UNKNOWN), and the report body only has `table: not found`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: `freeze.table_age` past `autovacuum_freeze_max_age`, or `vacuum.table_disabled` (autovacuum off and past its line) |
| 2 | FAIL: `freeze.table_age` at the stop limit (not produced in the lab) |
| 3 | UNKNOWN: data not collected, or the table was not found |
| 64 | Usage error, including an empty name |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
