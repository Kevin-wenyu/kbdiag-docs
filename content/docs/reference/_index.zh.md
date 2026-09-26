---
title: "使用手册"
weight: 90
type: docs
cascade:
  type: docs
---

内容来自 [kbdiag README](https://github.com/Kevin-wenyu/kbdiag#readme)，是生成时的快照。

命令页：[`status`]({{< relref "/docs/reference/status" >}}) · [`sessions`]({{< relref "/docs/reference/sessions" >}}) · [`session`]({{< relref "/docs/reference/session" >}}) · [`locks`]({{< relref "/docs/reference/locks" >}}) · [`txn`]({{< relref "/docs/reference/txn" >}}) · [`waits`]({{< relref "/docs/reference/waits" >}}) · [`slots`]({{< relref "/docs/reference/slots" >}})

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
| `status` | 版本、角色、运行时长、连接数、复制上下游、各库大小、磁盘；连接占满时 FAIL，备库没在收 WAL 时 WARN | — |
| `sessions` | 全部会话；idle in transaction 过久报 WARN | `--active`、`--limit N`、`--idle-in-txn-warn 秒` |
| `session <pid>` | 一个会话：活动、持有的锁、挡住谁或被谁挡住 | `--lock-wait-warn 秒`、`--idle-in-txn-warn 秒` |
| `locks` | 锁等待和直接挡路者；等太久报 WARN | `--limit N`、`--lock-wait-warn 秒` |
| `txn` | 开着的事务和两阶段事务；过久报 WARN/FAIL | `--limit N`、`--xact-warn 秒`、`--xact-fail 秒`、`--prepared-fail 秒` |
| `waits` | 按等待事件和状态汇总会话 | |
| `slots` | 复制槽；未激活报 FAIL | |

默认阈值：idle in transaction 300 秒，等锁 10 秒，事务 300 秒 WARN、1800 秒 FAIL，两阶段事务 900 秒 FAIL。`--limit` 只影响显示，判定始终覆盖全部行。

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
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:38:53+08:00)

[WARN] lock.waiting  会话 364818 等 public.kbdiag_inj_lock 的 AccessShareLock 已 14 秒，被 364809 挡住
  verify: kbdiag session 364809  # 看挡路的会话在干什么

lock.list: 2 rows
pid     locktype  relation                mode                 granted  wait_s  blocked_by
364809  relation  public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
364818  relation  public.kbdiag_inj_lock  AccessShareLock      false    13.8    [364809]
```

- 第一行：命令、结论和上下文（版本、角色、用户@位置、采集时间）。
- finding：编号、症状、下一步（`verify` 看什么或 `fix` 怎么处理）。
- 数据：每个探针一张表，`-` 表示空值。`--json` 内容相同，字段名稳定。

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
