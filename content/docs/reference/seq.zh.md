---
title: "seq：序列"
description: "当前库的序列，按用掉的比例排；取不出下一个值时报 FAIL。"
weight: 210
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。FAIL 的例子由注入脚本造出来：它建了 `public.kbdiag_inj_seq`（`maxvalue 3`），再用 `nextval` 把它用完。数值只属于本次采样。

## 用法

```text
kbdiag seq [--limit N] [--json]
```

| 参数 | 作用 |
|---|---|
| `--limit N` | 最多显示 N 个序列；默认 20，`0` 表示全部 |
| `--json` | 输出 JSON |

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同，看的是当前连接的库。`--limit` 只裁列表，判定覆盖所有序列。

## 主库

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

- 序列按用掉的比例排序。`last` 是最后分配出去的值，`limit` 是它往哪边数到头（自己的 `MAXVALUE`，递减的序列是 `MINVALUE`），`used` 是用掉的比例，`left` 是还剩多少个值。计算是精确的（`math/big`）：bigint 序列跨满 int64，普通相减会溢出。
- 从没调用过、或者 `setval(..., false)` 之后的序列没有 last 值：显示成 `no value yet`，值是 `-`。
- 只判一件事：`seq.exhausted`（FAIL），即 `nextval` 已经报错。只是快用完的序列只展示，不报：多快算快没有客观线。会循环的序列不算用完，会写成 `cycles`（实验环境没采到）。

## 备库

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

备库上的序列值是 WAL 里的副本，主库每次预写 32 个，所以备库可能读到“到头了”而主库还有值。文本说明了这点（`up to 32 values ahead of the primary`），备库不判：要到主库上跑 `seq`。上面的 `last` 确实比主库的大。

## 没有权限时

`kbdiag_ro`（没有监控角色，走 `127.0.0.1`）：

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

- `?` 是这个账号读不了的 `last_value`（序列上没有 SELECT 权限），所以 `used` 和 `left` 算不出。SQL 按 oid 判权限，序列中途被删掉不会让整条 probe 失败。14 个看不到的行记在 `redacted` 里，提示给序列授予 `SELECT`：`sys_monitor` 不覆盖序列。
- 值是 `-` 的两行是从没调用过的序列（`no value yet`）：它和权限不够造成的 NULL 不是一回事，kbdiag 把两者分开。
- 结论是 UNKNOWN，因为没能看到这些值。

## 用完的序列

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

- `seq.exhausted` 是 FAIL：`nextval` 已经报错，用它的插入已经失败。线就是序列自己的上限，所以没有参数。
- `fix` 按是什么挡住了来给。这里序列停在自己的 `MAXVALUE` 3，比 `integer` 允许的小，所以建议把它调高。序列已经到了类型的边界时：int 或 smallint 改成 bigint（先改列，要重写表），bigint 只能换键。bigint 序列配 int 列、列先溢出的错配，这里不检测。

同一个库在备库上：

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

同样有 `100.00%` 这一行，备库仍然是 OK，因为它不判序列。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 2 | FAIL：有序列取不出下一个值 |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
