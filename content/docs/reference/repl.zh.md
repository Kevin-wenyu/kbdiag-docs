---
title: "repl：本节点看复制"
description: "从本节点看复制：主库看同步设置和每个备库落后多少；备库看上游、接收和回放。"
weight: 130
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。WARN 的例子由故障注入脚本造出来：它暂停（SIGSTOP）备库的 WAL 接收进程，和 [`slots`]({{< relref "/docs/reference/slots" >}}) 页用的是同一个。数值只属于本次采样。

## 用法

```text
kbdiag repl [--json]
```

没有自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 主库

```bash
~/kbdiag repl
echo EXIT_CODE=$?
```

```text
repl  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:56+08:00)

sync
  synchronous_standby_names  ANY 1( node2)  (any 1 of node2 must confirm)
  synchronous_commit         remote_apply
  synchronous now            1 (node2)

downstreams: 1  (bytes behind this node's current WAL position)
  name   address         state      sync    sent     flushed  replayed  replay lag  last reply
  node2  192.168.105.11  streaming  quorum  0 bytes  0 bytes  0 bytes   0s          1s ago
EXIT_CODE=0
```

- `sync` 显示 `synchronous_standby_names` 和它的含义（`any 1 of node2 must confirm`）、`synchronous_commit`，以及服务器现在把几个备库算作同步的。`sync` 列里的 `quorum` 是服务器自己的 `sync_state`；repmgr 下实测就是 `quorum`，不是 `sync` 或 `async`，所以 kbdiag 不翻译。
- `downstreams` 一个备库一行：发送、刷盘、回放到哪（写成落后本节点当前 WAL 位置的字节数），回放延迟的时间（备库追平且空闲时为空），以及多久前最后一次回复。
- 延迟只展示，不判：服务器上没有客观线。

## 备库

```bash
~/kbdiag repl
echo EXIT_CODE=$?
```

```text
repl  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:03+08:00)

upstream
  status    streaming
  upstream  192.168.105.10:54321
  slot      repmgr_slot_2
  last_msg  3s ago

replay
  received                   0/C9352A80
  replayed                   0/C9352A80  (caught up with what was received)
  last replayed transaction  1m 0s ago
  paused                     no

downstreams: 0
EXIT_CODE=0
```

- `upstream` 和 `kbdiag status` 里的 `inst.upstream` 是同一个 WAL 接收进程视图，`last_msg` 是离主库最后一条消息多久。
- `replay` 对比收到的和回放的。`caught up with what was received` 表示两个位置相等。`last replayed transaction 1m 0s ago` 不是延迟：空闲的主库上它能读到好几个小时而位置完全一致，所以 kbdiag 不把它当成延迟。
- `paused` 是回放有没有被 `sys_wal_replay_pause()` 暂停。

## WAL 接收进程卡住

备库的接收进程被暂停后，备库上报：

```bash
~/kbdiag repl
echo EXIT_CODE=$?
```

```text
repl  WARN  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:22:58+08:00)

[WARN] inst.upstream  the standby's WAL receiver shows streaming, but nothing has come from the primary for 1m 12s, longer than wal_receiver_timeout (30s), after which a working receiver reconnects: it is stuck (stopped or blocked), so it is not receiving WAL: if the primary fails now, no standby can take over
  verify: kbdiag slots  # run on the primary: is this standby's slot inactive?

upstream
  status    streaming
  upstream  192.168.105.10:54321
  slot      repmgr_slot_2
  last_msg  1m 12s ago

replay
  received                   0/CCCC9228
  replayed                   0/CCCC9228  (caught up with what was received)
  last replayed transaction  1m 12s ago
  paused                     no

downstreams: 0
EXIT_CODE=1
```

- finding 是 `inst.upstream`，和 `kbdiag status` 用的是同一条规则：接收进程写 `streaming`，但 `last_msg` 比 `wal_receiver_timeout`（实验环境 30 秒）还老。正常的接收进程在超时的一半时就会向主库要回复，满了就断开重连，所以只有卡住的会越过这条线。没有接收进程、或者状态不是 `streaming` 时，同一条 finding 也会报。
- `received` 和 `replayed` 仍然相等：什么都没来，也就没什么可回放。是最后一条消息的年龄暴露了问题。
- 已知的边界：接收进程在连接开始时就把收到时间设成当时，所以连接慢于超时一半、或时间线切换，可能短暂报一次。不加余量是故意的，因为余量没有客观来源。

同一时刻的主库：

```bash
~/kbdiag repl
echo EXIT_CODE=$?
```

```text
repl  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:22:56+08:00)

sync
  synchronous_standby_names  (none: asynchronous only)
  synchronous_commit         remote_apply

downstreams: 0
EXIT_CODE=0
```

- `downstreams` 里没有备库了（0），`synchronous_standby_names` 现在读成 `(none: asynchronous only)`，注入前是 `ANY 1( node2)`。所以 `repl.sync_short` 没有触发。kbdiag 显示的是服务器当前的值；注入期间这个设置是 repmgr 改的：repmgr.conf 里是 `synchronous='quorum'` 时，备库断开约 2 秒后 repmgrd 会把 `synchronous_standby_names` 清空，降成异步提交，备库重连后再改回来（2026-09-28 实验环境 hamgr.log 里看到的）。这是 repmgr 做的，不是 KingbaseES 内核的行为。所以在这种集群上 `repl.sync_short` 只会在那一两秒里出现，备库丢了之后更常见的是"已经是异步了"，`repl` 显示为 `(none: asynchronous only)`。
- 到主库上跑 [`slots`]({{< relref "/docs/reference/slots" >}}) 看槽变成不活跃，跑 [`cluster`]({{< relref "/docs/reference/cluster" >}}) 看 repmgr 的看法。

## 实验环境没有造出来的 WARN

按源码写，不是实采：

- `repl.replay_paused`（WARN）：备库上回放被暂停（`sys_wal_replay_pause()`）。查询照常，但越落越远，故障切换时得先回放完收到的全部。除非是有意暂停，`fix` 是 `SELECT sys_wal_replay_resume()`。实验环境没有这个注入：在那里暂停回放会卡住主库的所有提交（`synchronous_commit` 是 `remote_apply`）。
- `repl.sync_short`（WARN）：`synchronous_standby_names` 要的备库数比服务器算作同步候选（`sync` 或 `quorum`）的多。文本说提交要么在等，要么已经不等了，同步副本没有保证。它是 WARN 不是 FAIL，因为实验环境里备库断开后同步提交照样过去了（repmgr 已经降成异步，见上）。kbdiag 数服务器给的 `sync_state`，不自己重算候选规则，并且只在 `synchronous_commit` 让提交等备库时才判（这是本连接的值，按角色或按库另设的看不到）。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：没在收 WAL、回放暂停，或同步备库不够数 |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
