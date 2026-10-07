---
title: "table：一张表"
description: "一张表：大小、行数、vacuum 和 analyze、冻结年龄、访问、索引。"
weight: 160
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。两个例子由注入脚本造出来：`public.kbdiag_inj_dead`（设了 `autovacuum_enabled=off`，插入 10000 行、删除 5000 行）和 `public.kbdiag_inj_tbl`（插入 20000 行、删除 5000 行，带主键和另一个索引）。数值只属于本次采样。

## 用法

```text
kbdiag table <name> [--json]
```

`<name>` 按 SQL 规则解析：用 `to_regclass`（参数绑定），不带引号的名字折成小写，按 `search_path` 找，和在 `ksql` 里写的一致。要大写就像 SQL 里那样加引号：`'"Name"'`。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同，看的是当前连接的库（别的库用 `-d`）。

名字是空的是用法错误（退出码 64）。找不到是 UNKNOWN（3），不是用法错误，因为表可能在别的库里。

## 主库上的一张表

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

- `size` 是精确值，拆成堆、索引、TOAST，定义和 `top-objects` 相同，所以同一张表两处数字一致。解析名字不加锁，大小是单独的 probe：有人拿 VACUUM FULL 之类锁着这张表时，只会丢掉大小（等到 `lock_timeout`），其余照常显示，文本会指向 `kbdiag locks`。
- `rows` 里估算值（`reltuples`）旁边是统计里的活元组和死元组。`xid age` 是冻结年龄，对照 `autovacuum_freeze_max_age`。
- `vacuum and analyze`：死元组对照 autovacuum 触发线，最近手工和自动的 vacuum、analyze 各多久前、几次，以及上次 analyze 之后的修改数。
- `access since the statistics reset`：扫描、读写的行数、块缓存命中，命中率保留一位小数，几次读盘不会被四舍五入成 100%。
- `indexes` 有大小、扫描次数、是不是主键和定义。
- 判定复用别的命令的规则，没有新规则：年龄对照和 `freeze` 同样的两条线（finding id 是 `freeze.table_age`），表级关了 autovacuum 又过线是 `vacuum.table_disabled`。这里两条都没触发，所以是 OK。

## 同一张表在备库上

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

表统计是节点本地的，所以 `statistics` 是 `not_applicable`，索引扫描次数是 `-`（NULL，不是 0）。大小、行数估算和年龄是复制来的，照样显示，年龄照样判。

## 表级关了 autovacuum

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

- finding 和 `kbdiag vacuum` 对这张表报的是同一条：`vacuum.table_disabled`，`fix` 也一样。`reloptions` 里能看到原因 `autovacuum_enabled=off`，文本写 `due (autovacuum is off for this table)`。
- `modified since analyze` 是 5000，和删掉的 5000 行对得上。

## 过了线但 autovacuum 开着

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

5000 个死元组对着 4050 的触发线，所以写 `due`，但这张表 autovacuum 开着，下一轮 autovacuum 会处理它：没有 finding，结论 OK。

## 表不存在

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

第一行是 stderr，说明不带引号的名字会折成小写，以及用 `-d` 选别的库。退出码 3（UNKNOWN），报告正文只有 `table: not found`。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：`freeze.table_age` 超过 `autovacuum_freeze_max_age`，或 `vacuum.table_disabled`（关了 autovacuum 又过了线） |
| 2 | FAIL：`freeze.table_age` 到了停止线（实验环境没造出来） |
| 3 | UNKNOWN：有数据没采到，或者表找不到 |
| 64 | 参数错误，包括名字为空 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
