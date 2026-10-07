---
title: "seq: sequences"
description: "Sequences of this database by how much of their range is used; FAIL when one is exhausted."
weight: 210
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. The FAIL example was created by an injection script: it created `public.kbdiag_inj_seq` with `maxvalue 3` and used it up with `nextval`. Values belong to this capture only.

## Usage

```text
kbdiag seq [--limit N] [--json]
```

| Option | Effect |
|---|---|
| `--limit N` | Show at most N sequences; default 20, `0` for all |
| `--json` | Print JSON |

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}) and it looks at the database you are connected to. `--limit` only trims the list; the finding covers every sequence.

## Primary

```bash
~/kbdiag seq
echo EXIT_CODE=$?
```

```text
seq  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:00+08:00)

sequences in test: 16, most used first
  sequence                                type     last     limit                used   left
  public.kbdiag_test_id_seq               integer  1311000  2147483647           0.06%  2.15e+09
  kdb_schedule.kdb_jobclass_jclid_seq     integer  5        2147483647           0.00%  2.15e+09
  perf.kwr_snapshots_snap_id_seq          integer  2        2147483647           0.00%  2.15e+09
  public.flight_psg_new_info_id_seq       bigint   1000000  9223372036854775807  0.00%  9.22e+18
  public.orders_id_seq                    bigint   1000000  9223372036854775807  0.00%  9.22e+18
  public.t_perf_test_id_seq               bigint   100000   9223372036854775807  0.00%  9.22e+18
  sysmac.sysmac_policy_oid_seq            bigint   1        9223372036854775807  0.00%  9.22e+18
  kdb_schedule.kdb_action_acid_seq        integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_exception_jexid_seq    integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_job_action_jaid_seq    integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_joblog_jlgid_seq       integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_jobsteplog_jslid_seq   integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_schedule_job_sjid_seq  integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_schedule_scid_seq      integer  -        2147483647           -      no value yet
  sys_catalog.global_chain_seq            bigint   -        9223372036854775807  -      no value yet
  sys_hm.hm_run_t_run_id_seq              integer  -        2147483647           -      no value yet
EXIT_CODE=0
```

- The sequences are ordered by how much of their range is used. `last` is the last value handed out, `limit` the end of the range it counts toward (its own `MAXVALUE`, or `MINVALUE` for a descending one), `used` the share, `left` how many values remain. The arithmetic is exact (`math/big`), since a bigint sequence spans the whole int64 range and plain subtraction would overflow.
- A sequence that has never been called, or was reset with `setval(..., false)`, has no last value: it is shown as `no value yet`, with `-`.
- Only one thing is judged: `seq.exhausted` (FAIL), when `nextval` already fails. A sequence that merely runs low is shown, not reported: how low is too low has no objective line. A sequence that cycles does not count as used up; it would be written as `cycles` (not captured in the lab).

## Standby

```bash
~/kbdiag seq
echo EXIT_CODE=$?
```

```text
seq  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:07+08:00)

sequences in test: 16, most used first
  on a standby a sequence reads up to 32 values ahead of the primary (and is not judged): run on the primary
  sequence                                type     last     limit                used   left
  public.kbdiag_test_id_seq               integer  1311029  2147483647           0.06%  2.15e+09
  kdb_schedule.kdb_jobclass_jclid_seq     integer  33       2147483647           0.00%  2.15e+09
  perf.kwr_snapshots_snap_id_seq          integer  33       2147483647           0.00%  2.15e+09
  public.flight_psg_new_info_id_seq       bigint   1000032  9223372036854775807  0.00%  9.22e+18
  public.orders_id_seq                    bigint   1000032  9223372036854775807  0.00%  9.22e+18
  public.t_perf_test_id_seq               bigint   100023   9223372036854775807  0.00%  9.22e+18
  sysmac.sysmac_policy_oid_seq            bigint   1        9223372036854775807  0.00%  9.22e+18
  kdb_schedule.kdb_action_acid_seq        integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_exception_jexid_seq    integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_job_action_jaid_seq    integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_joblog_jlgid_seq       integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_jobsteplog_jslid_seq   integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_schedule_job_sjid_seq  integer  -        2147483647           -      no value yet
  kdb_schedule.kdb_schedule_scid_seq      integer  -        2147483647           -      no value yet
  sys_catalog.global_chain_seq            bigint   -        9223372036854775807  -      no value yet
  sys_hm.hm_run_t_run_id_seq              integer  -        2147483647           -      no value yet
EXIT_CODE=0
```

A standby's sequence value is the copy in the WAL, and the primary writes 32 values ahead each time, so a standby can read "at the end" while the primary still has values. The text says so (`up to 32 values ahead of the primary`), and the standby is not judged: run `seq` on the primary. The `last` values above are indeed larger than the primary's.

## Without privileges

`kbdiag_ro` (no monitoring role, over `127.0.0.1`):

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro seq
echo EXIT_CODE=$?
```

```text
seq  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-10-07T17:21:08+08:00)

sequences in test: 16, most used first
  sequence                                type     last  limit                used  left
  kdb_schedule.kdb_action_acid_seq        integer  ?     2147483647           ?     ?
  kdb_schedule.kdb_exception_jexid_seq    integer  ?     2147483647           ?     ?
  kdb_schedule.kdb_job_action_jaid_seq    integer  ?     2147483647           ?     ?
  kdb_schedule.kdb_jobclass_jclid_seq     integer  ?     2147483647           ?     ?
  kdb_schedule.kdb_joblog_jlgid_seq       integer  ?     2147483647           ?     ?
  kdb_schedule.kdb_jobsteplog_jslid_seq   integer  ?     2147483647           ?     ?
  kdb_schedule.kdb_schedule_job_sjid_seq  integer  ?     2147483647           ?     ?
  kdb_schedule.kdb_schedule_scid_seq      integer  ?     2147483647           ?     ?
  perf.kwr_snapshots_snap_id_seq          integer  ?     2147483647           ?     ?
  public.flight_psg_new_info_id_seq       bigint   ?     9223372036854775807  ?     ?
  public.kbdiag_test_id_seq               integer  ?     2147483647           ?     ?
  public.orders_id_seq                    bigint   ?     9223372036854775807  ?     ?
  public.t_perf_test_id_seq               bigint   ?     9223372036854775807  ?     ?
  sys_catalog.global_chain_seq            bigint   -     9223372036854775807  -     no value yet
  sys_hm.hm_run_t_run_id_seq              integer  -     2147483647           -     no value yet
  sysmac.sysmac_policy_oid_seq            bigint   ?     9223372036854775807  ?     ?
redacted: 14 rows of seq.list hide last_value (insufficient_privilege; grant SELECT on the sequences (sys_monitor does not cover them))
EXIT_CODE=3
```

- `?` is a `last_value` this account may not read (no SELECT on the sequence), so `used` and `left` cannot be computed. The SQL checks the privilege by oid, so a sequence dropped meanwhile does not fail the whole probe. The 14 hidden rows are in `redacted`, with the advice to grant `SELECT` on the sequences: `sys_monitor` does not cover them.
- The two rows with `-` are sequences never called (`no value yet`): that is not the same NULL as a privilege gap, and kbdiag keeps the two apart.
- The verdict is UNKNOWN, because it could not see the values.

## An exhausted sequence

```bash
~/kbdiag seq
echo EXIT_CODE=$?
```

```text
seq  FAIL  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:20+08:00)

[FAIL] seq.exhausted  sequence public.kbdiag_inj_seq (integer) is at 3, its limit is 3: nextval fails, so inserts that use it fail
  fix: ALTER SEQUENCE public.kbdiag_inj_seq MAXVALUE <higher>  # it stops at its MAXVALUE, short of what its type allows

sequences in test: 17, most used first
  sequence                                type     last     limit                used     left
  public.kbdiag_inj_seq                   integer  3        3                    100.00%  0
  public.kbdiag_test_id_seq               integer  1311000  2147483647           0.06%    2.15e+09
  kdb_schedule.kdb_jobclass_jclid_seq     integer  5        2147483647           0.00%    2.15e+09
  perf.kwr_snapshots_snap_id_seq          integer  2        2147483647           0.00%    2.15e+09
  public.flight_psg_new_info_id_seq       bigint   1000000  9223372036854775807  0.00%    9.22e+18
  public.orders_id_seq                    bigint   1000000  9223372036854775807  0.00%    9.22e+18
  public.t_perf_test_id_seq               bigint   100000   9223372036854775807  0.00%    9.22e+18
  sysmac.sysmac_policy_oid_seq            bigint   1        9223372036854775807  0.00%    9.22e+18
  kdb_schedule.kdb_action_acid_seq        integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_exception_jexid_seq    integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_job_action_jaid_seq    integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_joblog_jlgid_seq       integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_jobsteplog_jslid_seq   integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_schedule_job_sjid_seq  integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_schedule_scid_seq      integer  -        2147483647           -        no value yet
  sys_catalog.global_chain_seq            bigint   -        9223372036854775807  -        no value yet
  sys_hm.hm_run_t_run_id_seq              integer  -        2147483647           -        no value yet
EXIT_CODE=2
```

- `seq.exhausted` is a FAIL: `nextval` fails, so inserts that use it already fail. The line is the sequence's own limit, so there is no option for it.
- The `fix` depends on what blocks it. Here the sequence stops at its own `MAXVALUE` 3, short of what `integer` allows, so it raises that. When the sequence is at the limit of its type, an int or smallint becomes bigint (change the column first; this rewrites the table), and a bigint has no remedy but a new key. A sequence with a mismatched bigint sequence on an int column, where the column overflows first, is not detected.

The same database on the standby:

```bash
~/kbdiag seq
echo EXIT_CODE=$?
```

```text
seq  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:21+08:00)

sequences in test: 17, most used first
  on a standby a sequence reads up to 32 values ahead of the primary (and is not judged): run on the primary
  sequence                                type     last     limit                used     left
  public.kbdiag_inj_seq                   integer  3        3                    100.00%  0
  public.kbdiag_test_id_seq               integer  1311029  2147483647           0.06%    2.15e+09
  kdb_schedule.kdb_jobclass_jclid_seq     integer  33       2147483647           0.00%    2.15e+09
  perf.kwr_snapshots_snap_id_seq          integer  33       2147483647           0.00%    2.15e+09
  public.flight_psg_new_info_id_seq       bigint   1000032  9223372036854775807  0.00%    9.22e+18
  public.orders_id_seq                    bigint   1000032  9223372036854775807  0.00%    9.22e+18
  public.t_perf_test_id_seq               bigint   100023   9223372036854775807  0.00%    9.22e+18
  sysmac.sysmac_policy_oid_seq            bigint   1        9223372036854775807  0.00%    9.22e+18
  kdb_schedule.kdb_action_acid_seq        integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_exception_jexid_seq    integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_job_action_jaid_seq    integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_joblog_jlgid_seq       integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_jobsteplog_jslid_seq   integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_schedule_job_sjid_seq  integer  -        2147483647           -        no value yet
  kdb_schedule.kdb_schedule_scid_seq      integer  -        2147483647           -        no value yet
  sys_catalog.global_chain_seq            bigint   -        9223372036854775807  -        no value yet
  sys_hm.hm_run_t_run_id_seq              integer  -        2147483647           -        no value yet
EXIT_CODE=0
```

Same `100.00%` row, and the standby still says OK because it does not judge sequences.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 2 | FAIL: a sequence cannot hand out another value |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
