---
title: "第一次检查"
description: "编译二进制、装到数据库主机、连接实例，读懂结论和退出码。"
weight: 30
---

编译一次 kbdiag，拷到 **KingbaseES 主机**上，跑 `status` 和 `sessions`，再决定哪里需要细看。

## 1. 准备 {#requirements}

- 一个运行中的 KingbaseES V8R6 实例（在 V008R006C009B0014 上测试）。
- 数据库主机上 `kingbase` OS 用户的权限。
- 一台装了 Go（版本见仓库的 `go.mod`）和 git 的机器，用来编译。可以就是你的笔记本；数据库主机上除了这个二进制什么都不用装。

## 2. 编译和安装 {#install}

在编译机上：

```bash
git clone https://github.com/Kevin-wenyu/kbdiag.git
cd kbdiag
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w -X main.version=$(git describe --tags --match 'v2*' --always)" -o kbdiag ./cmd/kbdiag
scp kbdiag kingbase@db-host:~/kbdiag
```

ARM 主机用 `GOARCH=arm64`。产物是一个没有运行时依赖的静态文件，离线主机只要把这个文件拷过去。

在数据库主机上：

```bash
sudo -iu kingbase
chmod +x ~/kbdiag
~/kbdiag --version
```

## 3. 连接 {#connection}

默认走本地 socket `/tmp/.s.KINGBASE.54321`，以 `system` 用户连 `test` 库，和 `ksql test system` 一样。用参数换目标：

| 参数 | 默认值 |
|---|---|
| `--host` | `/tmp`（socket 目录）；写主机名或 IP 走 TCP |
| `-p, --port` | `54321` |
| `-d, --dbname` | `test` |
| `-U, --user` | `system` |
| `--timeout` | 每条查询 `10s` |

密码从 `PGPASSWORD` 或 `~/.pgpass` 取。连不上时 kbdiag 打印错误并以 69 退出；先查端口、socket 目录和 `sys_hba.conf`。

没有监控角色的账号看不到别人会话的状态、时间和 SQL。kbdiag 把这些字段列进 `redacted`，结论给 UNKNOWN 而不是 OK；授予 `sys_monitor` 或者用 `system` 才能看全。

## 4. 跑第一次检查 {#run-check}

```bash
~/kbdiag status
echo "exit code: $?"
~/kbdiag sessions
echo "exit code: $?"
```

`$?` 要紧跟在命令后面读，下一条命令会覆盖它。`status` 告诉你这是个什么实例、基本面是否正常：连接、复制、磁盘；`sessions` 列出所有连着的会话，并对停在 idle in transaction 的会话报警。

## 5. 读懂结论和退出码 {#exit-codes}

每份报告第一行就是结论，退出码说的是同一件事：

| 退出码 | 结论 | 下一步 |
|---|---|---|
| `0` | OK | 这次采样里没有越过阈值的 |
| `1` | WARN | 逐条看 finding，跑它的 `verify` 命令 |
| `2` | FAIL | 同上，而且要更快：已经坏了或马上要坏 |
| `3` | UNKNOWN | 有东西没采到或看不到；查权限和 `redacted` 列表 |
| `64` | 参数错误 | 检查命令和参数 |
| `69` | 连不上 | 先解决连接；这次什么都没看 |

WARN 或 FAIL 的 finding 优先于 UNKNOWN：在看得到的范围里发现了问题，就直接报出来。

[逐行读一个真实结果](reading-results/)

## 6. 顺着证据往下查 {#next-check}

| 看到 | 下一条命令 | 看什么 |
|---|---|---|
| 锁等待 | `~/kbdiag session <挡路者 pid>` | 挡路者在干什么、事务开了多久 |
| idle in transaction | `~/kbdiag session <pid>` | 它持有哪些锁、有没有挡住别人 |
| 老事务或两阶段事务 | `~/kbdiag txn` | 事务时长，两阶段事务的 gid 和 owner |
| 很多会话在等 | `~/kbdiag waits` | 它们等的是不是同一个事件 |
| 连接占满 | `~/kbdiag sessions --limit 0` | 按用户、应用名、客户端地址看有没有扎堆 |
| 未激活的槽 | 在备库上跑 `~/kbdiag sessions` | 备库是否在线、有没有 `walreceiver` |

每条 finding 的 `verify` 行已经给出了对应的那一条。

## 完成标准 {#done}

你已经编译并装好 kbdiag，连上了正确的实例，跑过 `status` 和 `sessions`，也知道它们的退出码是什么意思。

[功能概览](../features/) · [查阅命令参数](../reference/)
