---
title: "vacuum：死元组和 autovacuum"
description: "哪些表死元组多、autovacuum 会不会去清、现在有没有 vacuum 在跑。"
weight: 100
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。WARN 的例子由注入脚本造出来：它建了表 `public.kbdiag_inj_dead`，设为 `autovacuum_enabled=off`，插入 10000 行再删掉 5000 行，所以表里有 5000 个没人会清的死元组。数值只属于本次采样。

## 用法

```text
kbdiag vacuum [--limit N] [--json]
```

| 参数 | 作用 |
|---|---|
| `--limit N` | 最多显示 N 张表；默认 20，`0` 表示全部 |
| `--json` | 输出 JSON |

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。`--limit` 只裁表的列表，判定覆盖所有表。`vacuum` 看的是当前连接的库（默认 `test`）。

## 主库，正常

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

- `settings` 显示 `autovacuum` 和 `track_counts` 开没开、worker 数和 naptime，以及触发线公式（`threshold` 加上比例系数乘 `reltuples`）。
- `running` 列出正在跑的 VACUUM 和进度（进度细节见 [`progress`]({{< relref "/docs/reference/progress" >}})）。这里没有。
- `tables` 按死元组数排序。`threshold` 是这张表的 autovacuum 触发线，算法和服务器一样（用 float4，表上的 `reloptions` 会覆盖全局值）。`due` 表示死元组是否过了这条线。`autovacuum` 是这张表自己的开关。
- 列表按死元组数排序，最上面的行都是 0，所以没有表过线。每张表的 `last autovacuum never` 只说明统计重置以来 autovacuum 没轮到过它们。

## 备库

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

表统计是节点本地的，备库上全是 0，autovacuum 也不在备库上跑，所以 `running` 和 `tables` 是 `not_applicable`，设置照样展示。要看 vacuum 到主库上跑。

## 没人会清的表

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

- finding 是 `vacuum.table_disabled`：这张表有 5000 个死元组，超过触发线 2050，但表自己设了 `autovacuum_enabled=off`，autovacuum 永远不会清它。表里 `due` 是 `yes`，`autovacuum` 是 `off`。
- 它是 WARN：死元组以后会造成膨胀，但现在什么都没坏。`fix` 是对这张表跑 `VACUUM`（名字需要时按 `quote_ident` 加引号）；跑完死元组还在，说明有东西压着视界，两条 `verify`（`kbdiag txn`、`kbdiag slots`）就是去找它。
- autovacuum 开着、只是过了线的表不报。那是 autovacuum 的正常队列，每个 naptime 轮一次；“等太久”需要一条时间线，而它没有客观的值。只在表里标 `due`。
- 这条命令的另一个 finding `vacuum.disabled`（WARN）在实验环境里没有造出来，下面按源码写：`autovacuum` 或 `track_counts` 关了，除了防回卷的 vacuum 以外，没有表会被自动清理。`fix` 是 `ALTER SYSTEM SET <那个开关> = on`，再 reload。
- `track_counts` 关着时表的 probe 是 `skipped`：计数器停了，旧值不能当成现在的。

同一张表在 [`table`]({{< relref "/docs/reference/table" >}}) 命令里怎么显示，见那一页。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
