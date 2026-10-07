---
title: "top-objects：最大的表和索引"
description: "当前库最大的表（堆、索引、TOAST 分列）和最大的索引。"
weight: 150
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。没有注入故障。数值只属于本次采样。

## 用法

```text
kbdiag top-objects [--limit N] [--json]
```

| 参数 | 作用 |
|---|---|
| `--limit N` | 每个列表最多显示 N 行；默认 20，`0` 表示全部 |
| `--json` | 输出 JSON |

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同，看的是当前连接的库。这条命令只展示，没有 finding。

## 主库

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

- `tables` 按总大小排序。`total` 是堆、索引、TOAST 加起来：`total = heap + indexes + toast`。拆开是因为大是因为数据、索引还是大字段，处理办法不同。`heap` 是 `pg_table_size` 减去 TOAST，所以含 FSM 和 VM。TOAST 表和它的索引不单列，算在父表里。
- 大小是精确值，不是 `relpages` 估算（和 `freeze` 相反）：这条命令就是回答“现在谁占了空间”，批量导入后没 ANALYZE 的话 `relpages` 是旧的。代价是大小函数要加 `AccessShareLock`，所以表被 VACUUM FULL 这类操作锁住时，整条 probe 会在 `lock_timeout` 上 `skipped` 并写明原因，而不是给出部分结果。查询期间被删掉的表读成 NULL 并被过滤掉，所以 ETL 反复建删临时表不会让 probe 失败。
- `rows (est.)` 是 `reltuples`。
- `indexes` 列出最大的索引和它所属的表。这里只看大小，使用次数去看 `kbdiag table <表名>`。
- 分区不会按父表汇总。
- 没有判定：多大算大没有客观线。所以都采到了才是 OK，有 probe 没采到就是 UNKNOWN。
- 实验环境里空间主要在测试用的表上（`orders`、`flight_psg_new_info`、`kbdiag_test`）。

## 备库和没有权限时

实验环境里，备库和 `kbdiag_ro` 账号（没有监控角色，走 `127.0.0.1`）返回的行和主库一致，只有第一行（角色、用户、时间）不同。大小不需要权限，所以什么都没被遮蔽。备库的采集在 kes-node2 上，`kbdiag_ro` 的在 kes-node1 上。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
