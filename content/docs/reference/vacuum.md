---
title: "vacuum: dead tuples and autovacuum"
description: "Which tables have the most dead tuples, whether autovacuum will clean them, and what is vacuuming now."
weight: 100
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. The WARN example was created by an injection script: it made table `public.kbdiag_inj_dead` with `autovacuum_enabled=off`, inserted 10000 rows and deleted 5000, so the table holds 5000 dead tuples that nothing will clean. Values belong to this capture only.

## Usage

```text
kbdiag vacuum [--limit N] [--json]
```

| Option | Effect |
|---|---|
| `--limit N` | Show at most N tables; default 20, `0` for all |
| `--json` | Print JSON |

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}). `--limit` only trims the table list; the findings cover every table. `vacuum` looks at the database you are connected to (default `test`).

## Healthy primary

```bash
~/kbdiag vacuum
echo EXIT_CODE=$?
```

```text
vacuum  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:54+08:00)

settings
  autovacuum    on  (3 workers, naptime 1m 0s)
  track_counts  on
  threshold     50 + 0.2 x reltuples

running: 0

tables in test: 98, most dead tuples first
  table                             dead  live  threshold  due  autovacuum  last autovacuum  last vacuum
  sysmac.sysmac_policy              0     0     50.2       -    on          never            never
  sysmac.sysmac_level               0     0     50.8       -    on          never            never
  sysmac.sysmac_compartment         0     0     50         -    on          never            never
  sysmac.sysmac_label               0     0     50.8       -    on          never            never
  sysmac.sysmac_policy_enforcement  0     0     50         -    on          never            never
  sysmac.sysmac_user                0     0     50         -    on          never            never
  sysmac.sysmac_obj                 0     0     50         -    on          never            never
  sysmac.sysmac_column_label        0     0     50         -    on          never            never
  sys_hm.check_type                 0     0     50.4       -    on          never            never
  sys_hm.hm_run_t                   0     0     50         -    on          never            never
  sys_hm.check_param                0     0     50.2       -    on          never            never
  sys.dual                          0     0     50.2       -    on          never            never
  sys_catalog._kingbase_loginfo     0     0     50         -    on          never            never
  public.t1                         0     0     50         -    on          never            never
  public.t_perf_test                0     0     20050      -    on          never            never
  kdb_schedule.kdb_jobagent         0     0     50         -    on          never            never
  kdb_schedule.kdb_jobclass         0     0     50         -    on          never            never
  kdb_schedule.kdb_action           0     0     50         -    on          never            never
  kdb_schedule.kdb_schedule         0     0     50         -    on          never            never
  kdb_schedule.kdb_schedule_job     0     0     50         -    on          never            never
  ... 78 more not shown (--limit 0 shows all)
EXIT_CODE=0
```

- `settings` shows whether `autovacuum` and `track_counts` are on, the workers and naptime, and the trigger formula (`threshold` + scale factor x `reltuples`).
- `running` lists VACUUMs in progress, with how far each has got (see [`progress`]({{< relref "/docs/reference/progress" >}})). None here.
- `tables` is ordered by dead tuples. `threshold` is the autovacuum trigger line for that table, computed the way the server does it (float4, and per-table `reloptions` override the global values). `due` says whether the dead tuples are past that line. `autovacuum` is the table's own switch.
- The list is sorted by dead tuples, and the top rows have 0, so no table is due. `last autovacuum never` on every table only says autovacuum never had to run on these tables since the statistics reset.

## Standby

```bash
~/kbdiag vacuum
echo EXIT_CODE=$?
```

```text
vacuum  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:01+08:00)

settings
  autovacuum    on  (3 workers, naptime 1m 0s)
  track_counts  on
  threshold     50 + 0.2 x reltuples

running: not_applicable  (standby: autovacuum does not run here; run on the primary)

tables in test: not_applicable  (standby: table statistics are local to each node and stay 0 here; run on the primary)
EXIT_CODE=0
```

Table statistics are local to each node and stay 0 on a standby, and autovacuum does not run there, so `running` and `tables` are `not_applicable`. The settings are still shown. Run `vacuum` on the primary.

## A table that nobody will clean

```bash
~/kbdiag vacuum
echo EXIT_CODE=$?
```

```text
vacuum  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:12+08:00)

[WARN] vacuum.table_disabled  table public.kbdiag_inj_dead has 5000 dead tuples, past its autovacuum threshold 2050, but autovacuum is off for it (autovacuum_enabled=off): nothing will clean it
  fix: VACUUM public.kbdiag_inj_dead  # connected to database test; turn autovacuum back on with ALTER TABLE ... RESET (autovacuum_enabled) unless it was turned off on purpose
  verify: kbdiag txn  # if dead tuples remain after VACUUM: the oldest transaction holding back the horizon
  verify: kbdiag slots  # or a replication slot's xmin

settings
  autovacuum    on  (3 workers, naptime 1m 0s)
  track_counts  on
  threshold     50 + 0.2 x reltuples

running: 0

tables in test: 99, most dead tuples first
  table                             dead  live  threshold  due  autovacuum  last autovacuum  last vacuum
  public.kbdiag_inj_dead            5000  5000  2050       yes  off         never            never
  sysmac.sysmac_policy              0     0     50.2       -    on          never            never
  sysmac.sysmac_level               0     0     50.8       -    on          never            never
  sysmac.sysmac_compartment         0     0     50         -    on          never            never
  sysmac.sysmac_label               0     0     50.8       -    on          never            never
  sysmac.sysmac_policy_enforcement  0     0     50         -    on          never            never
  sysmac.sysmac_user                0     0     50         -    on          never            never
  sysmac.sysmac_obj                 0     0     50         -    on          never            never
  sysmac.sysmac_column_label        0     0     50         -    on          never            never
  sys_hm.check_type                 0     0     50.4       -    on          never            never
  sys_hm.hm_run_t                   0     0     50         -    on          never            never
  sys_hm.check_param                0     0     50.2       -    on          never            never
  sys.dual                          0     0     50.2       -    on          never            never
  sys_catalog._kingbase_loginfo     0     0     50         -    on          never            never
  public.t1                         0     0     50         -    on          never            never
  public.t_perf_test                0     0     20050      -    on          never            never
  kdb_schedule.kdb_jobagent         0     0     50         -    on          never            never
  kdb_schedule.kdb_jobclass         0     0     50         -    on          never            never
  kdb_schedule.kdb_action           0     0     50         -    on          never            never
  kdb_schedule.kdb_schedule         0     0     50         -    on          never            never
  ... 79 more not shown (--limit 0 shows all)
EXIT_CODE=1
```

- `vacuum.table_disabled` is the finding: the table has 5000 dead tuples, past its trigger line 2050, but its own `autovacuum_enabled=off`, so autovacuum will never clean it. The `due` column says `yes` and the `autovacuum` column says `off`.
- It is a WARN: the dead tuples cause bloat later but nothing is broken now. The `fix` line is `VACUUM` on that table (names are quoted like `quote_ident` where needed); if the dead tuples are still there afterwards, something holds the horizon back, which is what the two `verify` lines (`kbdiag txn`, `kbdiag slots`) are for.
- A table that is past its line while autovacuum is on is not reported. That is the normal autovacuum queue, handled once every naptime, and "waiting too long" would need a time threshold that has no objective value. It shows as `due` in the table only.
- The other finding of this command, `vacuum.disabled` (WARN), was not produced in the lab: it means `autovacuum` or `track_counts` is off (taken from the source), so no table is vacuumed automatically any more except for the anti-wraparound vacuum. The `fix` is `ALTER SYSTEM SET <the switch> = on` followed by a reload.
- When `track_counts` is off the table probe is `skipped`: the counters are frozen, so old values are not shown as current.

For the same table seen from the [`table`]({{< relref "/docs/reference/table" >}}) command, see its page.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
