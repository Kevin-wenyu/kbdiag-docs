---
title: "cluster：repmgr 眼里的集群"
description: "repmgr 眼里的集群（节点、角色、上游、最近事件），和本节点对照。"
weight: 140
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `d9121e7` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。集群由 repmgr 管理，元数据在 `esrep` 库里。WARN 的例子由故障注入脚本造出来：它暂停（SIGSTOP）备库的 WAL 接收进程，直到备库不再挂在主库上，和 [`slots`]({{< relref "/docs/reference/slots" >}}) 页用的是同一个。数值只属于本次采样。

## 用法

```text
kbdiag cluster [--json]
```

没有自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同，只有一处不同：没给 `-d` 时，`cluster` 连 `esrep` 库，repmgr 的元数据在那里。kbdiag 只占一个连接，不会为它再开第二个。没有 `esrep` 库时退回默认库（不给 69，69 只表示连不上实例）。它不调 repmgr 的二进制，所以 `repmgr cluster show` 里逐个连节点的 `Status` 列做不了。

## 主库

```bash
~/kbdiag cluster
echo EXIT_CODE=$?
```

```text
cluster  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T21:32:29+08:00)

nodes: 2  (repmgr metadata in database esrep)
  id  name   type     upstream  active  priority  location  slot
  1   node1  primary  -         yes     100       default   repmgr_slot_1
  2   node2  standby  node1     yes     100       default   repmgr_slot_2
  this node is node1: repmgr says primary, the database is a primary
  attached here: node2

synchronous
  repmgr.conf                quorum  (/home/kingbase/cluster/install/kingbase/bin/../etc/repmgr.conf)
  synchronous_standby_names  ANY 1( node2)

events: 20  (the latest, at most 20)
  time                 node   event                  ok   details
  2026-10-07 20:54:40  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 20:54:34  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 20:52:33  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 20:52:27  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 20:51:57  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 20:51:51  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 20:37:30  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 20:37:24  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 20:36:53  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 20:36:47  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:23:02  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:23:01  node2  standby_recovery       yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:23:00  node1  node_recovery_success  yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:22:20  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:20:02  node2  standby_recovery       yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:20:01  node1  node_recovery_success  yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:20:01  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:19:18  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:12:14  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 17:12:08  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
EXIT_CODE=0
```

- `nodes` 是 repmgr 的节点表：类型、上游、active、优先级、位置和复制槽。文本标出本节点是哪一个：先问 repmgr 的 `get_local_node_id()`，没有再按 `primary_slot_name`（`repmgr_slot_N`）认。认不出时不做角色对照，结论也不会是 OK。
- `this node is node1: repmgr says primary, the database is a primary` 这一行就是 repmgr 元数据和数据库自己看法的对照。`attached here: node2` 是 repmgr 说跟着本节点的备库里、这里真有 walsender 的那些。
- `events` 是 repmgr 最近 20 条事件。里面的断开、重连是这个实验环境之前几轮测试留下的。
- 节点是不是活着、`repmgrd` 在不在跑，只连一个库是看不到的；到各节点上跑 `kbdiag status`。
- conninfo 不采：可能带密码。
- `synchronous`（只在主库上有）把 repmgr 配的和主库此刻的放在一起看。第一行是本节点 repmgr.conf 里的 `synchronous`：kbdiag 按 `$sys_bindir/../etc/repmgr.conf` 找文件（repmgrd 和 kbha 启动时用的就是这个路径，`sys_bindir` 取自 repmgr 自己的表），文件里的 `node_id` 和 `data_directory` 对得上这个实例才用。第二行是此刻的 `synchronous_standby_names`。只有在数据库主机上运行时才读文件（本地 socket，或者 loopback 且文件就在本机）。远程运行或文件读不到时，这一段写明原因，主库上的结论是 UNKNOWN，即使 repmgr 配的是 `async` 也一样：kbdiag 不知道它配的是什么。

## 备库

```bash
~/kbdiag cluster
echo EXIT_CODE=$?
```

```text
cluster  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:03+08:00)

nodes: 2  (repmgr metadata in database esrep)
  id  name   type     upstream  active  priority  location  slot
  1   node1  primary  -         yes     100       default   repmgr_slot_1
  2   node2  standby  node1     yes     100       default   repmgr_slot_2
  this node is node2: repmgr says standby, the database is a standby

events: 20  (the latest, at most 20)
  time                 node   event                   ok   details
  2026-10-07 17:20:02  node2  standby_recovery        yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:20:01  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:20:01  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:19:18  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:12:14  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 17:12:08  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:01:21  node2  standby_recovery        yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:01:21  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:01:19  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:00:38  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 16:49:31  node1  child_node_new_connect  yes  new standby "node2" (ID: 2) has connected
  2026-10-07 16:49:28  node2  repmgrd_start           yes  monitoring connection to upstream node "node1" (ID: 1)
  2026-10-07 16:49:26  node1  node_recovery_success   yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 16:49:26  node2  node_rejoin             yes  node 2 is now attached to node 1
  2026-10-07 16:48:36  node1  repmgrd_start           yes  monitoring cluster primary "node1" (ID: 1)
  2026-09-29 20:06:21  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 8 seconds
  2026-09-29 20:06:13  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-09-29 19:22:45  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-09-29 19:22:38  node1  child_node_disconnect   yes  standby node "node2" (ID: 2) has disconnected
  2026-09-28 15:42:40  node1  child_node_reconnect    yes  standby node "node2" (ID: 2) has reconnected after 106 seconds
EXIT_CODE=0
```

备库的 repmgr 元数据是从主库复制来的，所以节点表和事件一样，只有对照那一行是它自己的。`cluster.detached` 只在主库上判。

## 显式给了 `-d`

```bash
~/kbdiag -d test cluster
echo EXIT_CODE=$?
```

```text
cluster  UNKNOWN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:11+08:00)

nodes: skipped  (no repmgr schema in database test named by -d; repmgr keeps it in database esrep by default)

events: skipped  (no repmgr schema in database test named by -d; repmgr keeps it in database esrep by default)
EXIT_CODE=3
```

自己给了 `-d`，kbdiag 就信它。`test` 库里没有 repmgr schema，两个 probe 都是 `skipped`，结论是 UNKNOWN（没给 `-d` 时同样的情况是 `not_applicable`：不是 repmgr 集群，或者元数据在别处）。文本说明了 repmgr 默认把数据放在哪个库。

## 备库没挂上来

```bash
~/kbdiag cluster
echo EXIT_CODE=$?
```

```text
cluster  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T21:33:04+08:00)

[WARN] cluster.detached  repmgr lists node2 as an active standby of this node (node1), but no walsender here has that application_name: it is not attached (repmgr cluster show would report it so), unless its conninfo sets another application_name
  verify: kbdiag status  # run on node2: is it up, is it receiving WAL
  verify: kbdiag slots  # whether its slot here is inactive

[WARN] cluster.sync_degraded  repmgr is configured for quorum replication (/home/kingbase/cluster/install/kingbase/bin/../etc/repmgr.conf), but synchronous_standby_names is empty: commits do not wait for any standby, so a failover now can lose committed transactions; repmgrd switched to asynchronous because node2 is not attached; it switches back when it returns
  verify: kbdiag repl  # which standbys stream and what synchronous_standby_names says

nodes: 2  (repmgr metadata in database esrep)
  id  name   type     upstream  active  priority  location  slot
  1   node1  primary  -         yes     100       default   repmgr_slot_1
  2   node2  standby  node1     yes     100       default   repmgr_slot_2
  this node is node1: repmgr says primary, the database is a primary
  not attached here: node2

synchronous
  repmgr.conf                quorum  (/home/kingbase/cluster/install/kingbase/bin/../etc/repmgr.conf)
  synchronous_standby_names  (empty: asynchronous)

events: 20  (the latest, at most 20)
  time                 node   event                  ok   details
  2026-10-07 21:33:03  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 20:54:40  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 20:54:34  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 20:52:33  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 20:52:27  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 20:51:57  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 20:51:51  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 20:37:30  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 20:37:24  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 20:36:53  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
  2026-10-07 20:36:47  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:23:02  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:23:01  node2  standby_recovery       yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:23:00  node1  node_recovery_success  yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:22:20  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:20:02  node2  standby_recovery       yes  reconnected to local node "node2" (ID: 2), marking active
  2026-10-07 17:20:01  node1  node_recovery_success  yes  node "node2" (ID: 2) auto-recovery success
  2026-10-07 17:20:01  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 43 seconds
  2026-10-07 17:19:18  node1  child_node_disconnect  yes  standby node "node2" (ID: 2) has disconnected
  2026-10-07 17:12:14  node1  child_node_reconnect   yes  standby node "node2" (ID: 2) has reconnected after 6 seconds
EXIT_CODE=1
```

- `cluster.detached`（WARN）：repmgr 仍然说 `node2` 是本节点的 active 备库，但这里没有任何 walsender 的 application_name 是它，所以它没挂上来。repmgr 自己也会这样报，除非备库的 conninfo 另设了 `application_name`。文本里 `not attached here: node2` 是同一件事。
- 最新一条事件 `child_node_disconnect`（21:33:03）是 repmgr 自己对同一件事的记录。
- 它是 WARN：业务还没受影响。它是真的挂了还是只是卡住，只有到那个节点上才看得出，所以 `verify` 让你到 `node2` 上跑 `kbdiag status`，在这里跑 `kbdiag slots`。
- `cluster.sync_degraded`（WARN）是它带来的后果：repmgr.conf 写的是 `quorum`，`synchronous_standby_names` 却已经是空的（`synchronous` 段显示 `(empty: asynchronous)`）。这是 repmgrd 在 node2 离开约 2 秒后改的，node2 回来时它再改回去（实验环境的 hamgr.log 里每次都成对出现）。在那之前提交不等任何备库，这时故障切换会丢掉这段时间里提交的事务。它排在原因 `cluster.detached` 后面。
- 放开备库十秒后再跑同一条命令，结果是 OK，名单也回到了 `ANY 1( node2)`。
- 如果备库都挂着、却还报这条，说明 repmgrd 没切回来。备库刚回来的几秒里它还没察觉，这时跑也可能看到；再跑一次还是这样，就查本节点上的 repmgrd 在不在跑（第二条 `verify`）。这种情况只有单元测试覆盖：在实验环境里造它得停掉 repmgrd。

## 实验环境没有造出来的 WARN

按源码写，不是实采。都是 WARN：repmgr 按元数据做切换，不一致是隐患，但业务此刻还没受影响；是不是真脑裂要到各节点上才看得出。

- `cluster.primaries`：repmgr 里有多于一个 active 的 primary。元数据说是脑裂；到每个节点上跑 `kbdiag status`，看哪个已经不在恢复状态。
- `cluster.inactive`：repmgr 把某个节点标成 inactive，算它失败或已移除，所以集群少了一个能接管的节点。
- `cluster.role_mismatch`：repmgr 说本节点是主库（或备库），但数据库是另一种。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
