---
title: "使用手册"
weight: 90
type: docs
cascade:
  type: docs
---

内容来自 [kbdiag README](https://github.com/Kevin-wenyu/kbdiag#readme)，是生成时的快照。

命令页：[`status`]({{< relref "/docs/reference/status" >}}) · [`sessions`]({{< relref "/docs/reference/sessions" >}}) · [`session`]({{< relref "/docs/reference/session" >}}) · [`locks`]({{< relref "/docs/reference/locks" >}}) · [`txn`]({{< relref "/docs/reference/txn" >}}) · [`waits`]({{< relref "/docs/reference/waits" >}}) · [`slots`]({{< relref "/docs/reference/slots" >}}) · [`space`]({{< relref "/docs/reference/space" >}}) · [`freeze`]({{< relref "/docs/reference/freeze" >}}) · [`vacuum`]({{< relref "/docs/reference/vacuum" >}}) · [`archive`]({{< relref "/docs/reference/archive" >}}) · [`params`]({{< relref "/docs/reference/params" >}}) · [`repl`]({{< relref "/docs/reference/repl" >}}) · [`cluster`]({{< relref "/docs/reference/cluster" >}}) · [`top-objects`]({{< relref "/docs/reference/top-objects" >}}) · [`table`]({{< relref "/docs/reference/table" >}}) · [`top`]({{< relref "/docs/reference/top" >}}) · [`progress`]({{< relref "/docs/reference/progress" >}}) · [`checkpoint`]({{< relref "/docs/reference/checkpoint" >}}) · [`wal`]({{< relref "/docs/reference/wal" >}}) · [`seq`]({{< relref "/docs/reference/seq" >}})

KingbaseES 命令行诊断工具。单个静态二进制，直连线协议：不调 `ksql`，不进交互界面。每条命令对运行中的实例做一次只读查询，输出结论、证据和下一步该跑的命令。支持单机和 repmgr 主备集群。

这是用 Go 重写的 kbdiag 2.0，首个发布版本是 `v2.0.0-alpha.1`。shell 版（`v1.x`）已冻结，需要时用 [`v1.0.0`](https://github.com/Kevin-wenyu/kbdiag/releases/tag/v1.0.0)。

## 安装

编译 Linux 静态二进制（Go 版本见 `go.mod`），拷到数据库主机：

```bash
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w -X main.version=$(git describe --tags --match 'v2*' --always)" -o kbdiag ./cmd/kbdiag
scp kbdiag kingbase@db-host:~/kbdiag
```

ARM 主机用 `GOARCH=arm64`。二进制没有运行时依赖。

## 快速开始

```bash
sudo -iu kingbase        # 以数据库 OS 用户运行
~/kbdiag status          # 这是个什么实例
~/kbdiag sessions        # 谁连着，谁 idle in transaction
~/kbdiag locks           # 谁在等锁，被谁挡住
echo $?                  # 0 OK，1 WARN，2 FAIL，3 UNKNOWN
```

## 命令

| 命令 | 看什么 | 参数 |
|---|---|---|
| `status` | 版本、数据目录、端口、角色；主库列出每个备库，备库看上游在不在收 WAL；运行时长、连接数已用/可用、各库大小、数据目录所在磁盘（只在本机运行时有）。普通用户已经连不上报 FAIL，备库没在收 WAL 报 WARN | |
| `sessions` | 连接是谁占的（按用户、库、应用、客户端计数），再列出不是 idle 的客户端会话，事务最长的在前；idle in transaction 过久报 WARN。JSON 总是全部会话 | `--all`、`--limit N`、`--idle-in-txn-warn 秒` |
| `session <pid>` | 一个会话：是谁、在干什么、完整 SQL，在等什么锁、被谁挡住，挡住了谁，持有哪些锁 | `--lock-wait-warn 秒`、`--idle-in-txn-warn 秒` |
| `locks` | 谁挡的人最多、它持有什么锁，再列出每个等锁的会话（等得最久的在前）和直接挡路者；等太久报 WARN | `--limit N`、`--lock-wait-warn 秒` |
| `txn` | 最老的 xid 压着 vacuum、是谁压的，开着的事务，两阶段事务；过久报 WARN | `--limit N`、`--xact-warn 秒`、`--prepared-warn 秒` |
| `waits` | 在干活的会话在等什么，按等待事件和状态汇总，人多的在前；idle 会话和后台进程只计数 | |
| `slots` | 复制槽，未激活的和保留 WAL 最多的排前面；未激活报 WARN | |
| `space` | 空间账：数据目录、WAL、表空间所在的文件系统（只在本机运行时有），WAL 大小对照 `max_wal_size` 和 `wal_keep_segments`，各库和表空间大小。数据目录或 WAL 所在文件系统的可用空间不够一个 WAL 段时 FAIL，其余只展示 | |
| `freeze` | 各库离事务号回卷还有多远，当前库最老的表；超过 `autovacuum_freeze_max_age` 报 WARN，到了拒绝分配新事务号的停止线报 FAIL | `--limit N` |
| `vacuum` | 死元组最多的表和各自的 autovacuum 触发线，正在跑的 vacuum；没人会清时报 WARN（autovacuum 或 track_counts 关了，或表级关了 autovacuum 又过了线）。只在主库上有表统计 | `--limit N` |
| `archive` | 归档是不是在正常工作：设置、最后一次成功和失败、等着归档的 WAL；最后一次尝试失败时报 WARN | |
| `params` | 哪些参数不是默认值、在哪设的（文件和行号）；改了但要重启才生效的每个报 WARN | |
| `repl` | 从本节点看复制：主库看同步设置和每个备库落后多少；备库看上游、接收和回放。同步备库不够数、回放暂停、备库没在收 WAL 时报 WARN；延迟只展示，不判 | |
| `cluster` | repmgr 眼里的集群（节点、角色、上游、最近事件），和本节点对照；两个主库、inactive 节点、repmgr 记错的角色、没挂上来的备库报 WARN。没给 `-d` 时连 `esrep` 库 | |
| `top-objects` | 当前库最大的表（堆、索引、TOAST 分列）和最大的索引。只展示 | `--limit N` |
| `table <name>` | 一张表：大小、行数、vacuum 和 analyze、冻结年龄、访问、索引；用 freeze、vacuum 的规则判。名字按 SQL 规则（不带引号的折成小写）；找不到是 UNKNOWN | |
| `top` | `sys_stat_statements` 的累计 Top SQL（自上次重置以来），带每条占全部执行时间的比例；没在收集时明说。只展示 | `--limit N`、`--by time/mean/calls/io/temp` |
| `progress` | 正在跑的 VACUUM、CREATE INDEX、CLUSTER / VACUUM FULL、CHECKPOINT 到哪了。只展示 | |
| `checkpoint` | 最近一次 checkpoint，定时和被请求的各多少，脏页是谁写的（checkpointer、bgwriter、后端），相关参数。只展示 | |
| `wal` | WAL 写到哪了、`sys_wal` 多大，以及是什么让它留着：`max_wal_size`、`wal_keep_segments`、每个槽、等着归档的文件。只展示 | |
| `seq` | 当前库的序列，按用掉的比例排；取不出下一个值时报 FAIL | `--limit N` |

默认阈值：idle in transaction 300 秒，等锁 10 秒，事务 300 秒，两阶段事务 900 秒，都报 WARN。`--limit` 只影响显示，判定始终覆盖全部行。

## 连接

| 参数 | 默认值 |
|---|---|
| `--host` | `/tmp`（本地 socket `/tmp/.s.KINGBASE.54321`）；写主机名或 IP 走 TCP |
| `-p, --port` | `54321` |
| `-d, --dbname` | `test` |
| `-U, --user` | `system` |
| `--timeout` | 每条查询 `10s` |
| `--json` | 输出 JSON |

密码从 `PGPASSWORD` 或 `~/.pgpass` 取。连接是只读事务并设了 `lock_timeout`，kbdiag 不改任何东西；建议的处理语句（如 `ROLLBACK PREPARED`）只打印，不执行。

## 输出

```text
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-26T19:41:41+08:00)

[WARN] lock.waiting  session 803890 has waited 14s for AccessShareLock on public.kbdiag_inj_lock, blocked by 803881
  verify: kbdiag session 803881  # what the blocking session is doing

blockers: 1
  pid     blocks  holds
  803881  1       public.kbdiag_inj_lock AccessExclusiveLock

waiting: 1
  pid     object                  wants            waited  blocked by
  803890  public.kbdiag_inj_lock  AccessShareLock  14s     803881
```

- 第一行：命令、结论和上下文（版本、角色、用户@位置、采集时间）。
- finding：编号、症状（英文，工具输出全部是英文）、下一步（`verify` 看什么或 `fix` 怎么处理）。
- 数据：按阅读排版，大小和时长换成易读单位；`-` 表示空值，`?` 表示当前账号看不到。`--json` 给每个探针的原始表（字节、秒），字段名稳定。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN |
| 2 | FAIL |
| 3 | UNKNOWN：有东西没采到或看不到，所以不说 OK |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

## 权限

以 `system` 走本地 socket 能看到全部信息。没有监控角色的账号看不到别人会话的状态、时间和 SQL；kbdiag 把这些字段列进 `redacted`，结论给 UNKNOWN 而不是 OK；看得到的部分已经是 WARN 或 FAIL 时照报 WARN 或 FAIL。授予 `sys_monitor` 后解除。备库上两阶段事务是 `not_applicable`（到主库跑 `txn`），不影响结论。

## 运行要求

- KingbaseES V8R6（在 V008R006C009B0014 上测试）
- Linux amd64 或 arm64
- repmgr 可选
