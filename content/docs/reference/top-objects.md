---
title: "top-objects: largest tables and indexes"
description: "The largest tables (heap, indexes, TOAST) and indexes of this database."
weight: 150
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. Nothing was injected. Values belong to this capture only.

## Usage

```text
kbdiag top-objects [--limit N] [--json]
```

| Option | Effect |
|---|---|
| `--limit N` | Show at most N rows per list; default 20, `0` for all |
| `--json` | Print JSON |

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}) and it looks at the database you are connected to. This command only shows; it has no findings.

## Primary

```bash
~/kbdiag top-objects
echo EXIT_CODE=$?
```

```text
top-objects  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:57+08:00)

tables in test: 207, largest first  (total = heap + indexes + TOAST)
  table                       kind   total    heap     indexes  toast       rows (est.)
  public.orders               table  170 MB   62 MB    108 MB   -           1000000
  public.flight_psg_new_info  table  107 MB   64 MB    43 MB    -           1000000
  public.kbdiag_test          table  71 MB    43 MB    28 MB    8192 bytes  645750
  public.t_perf_test          table  8968 kB  6752 kB  2216 kB  -           100000
  pg_catalog._proc            table  4624 kB  1480 kB  712 kB   2432 kB     4650
  pg_catalog._dep             table  3816 kB  1160 kB  2656 kB  -           18518
  pg_catalog._att             table  3560 kB  2056 kB  1504 kB  -           11678
  pg_catalog._rewrite         table  2320 kB  664 kB   88 kB    1568 kB     576
  pg_catalog._desc            table  1616 kB  1296 kB  312 kB   8192 bytes  4923
  pg_catalog._stat            table  728 kB   520 kB   48 kB    160 kB      633
  pg_catalog._rel             table  640 kB   352 kB   288 kB   -           1244
  pg_catalog._typ             table  464 kB   272 kB   184 kB   8192 bytes  1304
  pg_catalog._op              table  328 kB   216 kB   112 kB   -           1062
  pg_catalog._amop            table  288 kB   112 kB   176 kB   -           1266
  pg_catalog._pkg             table  248 kB   64 kB    32 kB    152 kB      6
  pg_catalog._con             table  184 kB   80 kB    96 kB    8192 bytes  136
  pg_catalog._ind             table  176 kB   112 kB   64 kB    -           353
  pg_catalog._initprivs       table  168 kB   112 kB   48 kB    8192 bytes  777
  pg_catalog._amproc          table  160 kB   72 kB    88 kB    -           641
  pg_catalog._trigger         table  144 kB   64 kB    72 kB    8192 bytes  192
  ... 187 more not shown (--limit 0 shows all)

indexes in test: 271, largest first
  index                                     table                size
  public.kbdiag_rev_idx                     orders               56 MB
  public.idx_orders_user_status             orders               30 MB
  public.kbdiag_test_pkey                   kbdiag_test          28 MB
  public.flight_psg_new_info_pkey           flight_psg_new_info  22 MB
  public.idx_homs_flight_psg_new_info_tm    flight_psg_new_info  22 MB
  public.orders_pkey                        orders               22 MB
  public.t_perf_test_pkey                   t_perf_test          2216 kB
  pg_catalog._dep_depender_index            _dep                 1384 kB
  pg_catalog._dep_reference_index           _dep                 1224 kB
  pg_catalog._att_relid_attnam_index        _att                 888 kB
  pg_catalog._proc_proname_args_nsp_index   _proc                576 kB
  pg_catalog._att_relid_attnum_index        _att                 568 kB
  pg_catalog._desc_o_c_o_index              _desc                288 kB
  pg_catalog._proc_oid_index                _proc                136 kB
  pg_catalog._rel_relname_nsp_index         _rel                 104 kB
  pg_catalog._rel_tblspc_relfilenode_index  _rel                 88 kB
  pg_catalog._typ_typname_nsp_index         _typ                 88 kB
  pg_catalog._amop_fam_strat_index          _amop                72 kB
  pg_catalog._op_oprname_l_r_n_index        _op                  72 kB
  pg_catalog._rel_oid_index                 _rel                 72 kB
  ... 251 more not shown (--limit 0 shows all)
EXIT_CODE=0
```

- `tables` ordered by total size. `total` is the heap, indexes and TOAST added together: `total = heap + indexes + toast`. The split answers "is it big because of data, indexes or large columns", and the remedies differ. `heap` is `pg_table_size` minus TOAST, so it includes the free space and visibility maps. A TOAST table and its index are not listed on their own; they count under the parent table.
- Sizes are exact, not `relpages` estimates (the opposite of `freeze`): this command's whole point is "who takes space now", and after a bulk load without ANALYZE `relpages` is stale. The cost is that the size functions take an `AccessShareLock`, so when a table is held by something like VACUUM FULL the whole probe is `skipped` at `lock_timeout` with the reason written out, instead of showing partial results. A table dropped while the query runs reads NULL and is filtered out, so an ETL that creates and drops temporary tables does not fail the probe.
- `rows (est.)` is `reltuples`.
- `indexes` lists the largest indexes with the table they belong to. Size is the whole point, so the usage count is on `kbdiag table <name>`.
- Partitions are not summed up to their parent.
- No judgment: how big is too big has no objective line. So the verdict is OK only when everything was collected; an uncollected probe makes it UNKNOWN.
- The lab shows the bulk of the space in tables created for tests (`orders`, `flight_psg_new_info`, `kbdiag_test`).

## Standby and without privileges

The standby and a `kbdiag_ro` account (no monitoring role, over `127.0.0.1`) return the same rows as the primary in the lab; only the first line differs (role, user, time). Sizes need no privilege, so nothing is hidden. The standby capture is from kes-node2, the `kbdiag_ro` one from kes-node1.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
