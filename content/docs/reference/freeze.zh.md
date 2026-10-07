---
title: "freeze：事务号回卷距离"
description: "各库离事务号回卷还有多远，以及当前库最老的表。"
weight: 90
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。两个节点都是正常状态，没有注入故障，所以例子全是 OK。WARN 和 FAIL 在实验环境里没有造出来（见最后一节）。数值只属于本次采样。

## 用法

```text
kbdiag freeze [--limit N] [--json]
```

| 参数 | 作用 |
|---|---|
| `--limit N` | 最多显示 N 张表；默认 20，`0` 表示全部 |
| `--json` | 输出 JSON |

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。`--limit` 只裁表的列表，判定始终覆盖所有库和所有表。

## 主库，正常

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

- `limits` 是 kbdiag 用来比较的两条线，都来自服务器：`autovacuum_freeze_max_age`（WARN 线：到这里 autovacuum 就必须强制冻结）和停止线（FAIL 线：服务器拒绝分配新的事务号，写事务会失败）。停止线是 PG12 内核的常数，xid 是回卷点（2^31 - 1）之前 100 万，multixact 是 100。kbdiag 没有自己编阈值。
- `databases` 一库一行：`xid age`、`mxid age` 是这个库最老的未冻结 xid 和 multixact 的年龄，`of freeze max` 是 xid 年龄占 `autovacuum_freeze_max_age` 的百分比，`xids left` 是离停止线还能再分配多少个事务号。
- 判定按库做。库的年龄就是它最老的表，逐表出 finding 会把同一个问题报几十遍。`tables` 只列当前连接的库，最老的在前；要看别的库用 `kbdiag -d <库名> freeze`。
- `heap (est.)` 是 `relpages x block_size` 的估算。精确的大小函数要给每张表加锁，而救回卷时常有 VACUUM FULL、TRUNCATE，整条 probe 会卡到 `lock_timeout` 失败。
- `relfrozenxid` 为 0 的表（比如 `_kingbase_loginfo`）不列：`age(0)` 会读成 2147483647，会误报 FAIL。
- 备库上的年龄是复制过来的，和主库一样（kes-node2 上的实采输出，每个库都是 5672）。要修的话，VACUUM 仍然要到主库上跑。

二进制自己打印的参数说明：

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

## WARN 和 FAIL：实验环境没有造出来

两种 finding 都没有造出来，因为要把事务计数推到几亿个 xid。下面按源码写，不是实采；id 都是 `freeze.database_age`（`kbdiag table` 里是 `freeze.table_age`）：

- WARN：某个库的 xid 年龄达到 `autovacuum_freeze_max_age`，或 multixact 年龄达到 `autovacuum_multixact_freeze_max_age`。防回卷的 autovacuum 该跑了，或者跑不完。
- FAIL：xid 年龄离回卷点不到 100 万（multixact 不到 100）。服务器拒绝分配新的事务号，写操作失败。
- 下一步指向 `kbdiag txn`、`kbdiag slots`（谁压着视界）、别的库用 `kbdiag -d <库名> freeze`，以及在主库上跑的 `VACUUM (FREEZE)`。
- 读不到参数时，FAIL 仍然能判（停止线是常数）；年龄在停止线以下就是 UNKNOWN。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：超过 `autovacuum_freeze_max_age`（实验环境没造出来） |
| 2 | FAIL：到了停止线（实验环境没造出来） |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
