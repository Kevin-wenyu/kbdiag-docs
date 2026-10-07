---
title: "top：累计 Top SQL"
description: "`sys_stat_statements` 的累计 Top SQL；没在收集时明说。"
weight: 170
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。没有注入故障。实验环境两个节点上 `sys_stat_statements.track` 都是 `none`，没有在收集语句，`top` 没有行可显示。这一页展示的就是这种情况，也是实验环境的真实状态。统计开着的情况没有采到（见最后一节）。

## 用法

```text
kbdiag top [--limit N] [--by time|mean|calls|io|temp] [--json]
```

| 参数 | 作用 |
|---|---|
| `--limit N` | 最多显示 N 条语句；默认 20，`0` 表示全部 |
| `--by ORDER` | 排序方式：`time`（累计执行时间，默认）、`mean`（每次耗时）、`calls`（调用次数）、`io`（读盘块数）、`temp`（写临时文件块数）。它是排序，不是过滤 |
| `--json` | 输出 JSON |

`--by` 给了别的值是用法错误（退出码 64）。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 没在收集语句

```bash
~/kbdiag top
echo EXIT_CODE=$?
```

```text
top  UNKNOWN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:58+08:00)

statements: skipped  (sys_stat_statements.track=none: statements are not being collected; set it to top or all)
EXIT_CODE=3
```

- `skipped` 并写明原因，结论是 UNKNOWN：空表加 OK 等于说“没有昂贵的 SQL”，而实际上什么都没测。备库（kes-node2）上打印的一样。
- 打开它的开关是 `sys_stat_statements.track`（`top` 或 `all`）。另外两种原因有各自的提示：库没加载进 `shared_preload_libraries`（要重启），或者扩展没装在当前库（`CREATE EXTENSION sys_stat_statements`，或者用 `-d`）。
- 视图按 `sys_extension` 找到的 schema 读，不走 `search_path`：否则别人在 `public` 里放一个同名视图，就能让 kbdiag 报假数据。
- 本连接的 `track=none` 不等于没有数据（角色、库可以自己设，`save=on` 也会留着旧数据），所以 kbdiag 照样读视图，一行都没有才写 `skipped`。

## 统计开着时：没有采到

按源码写，不是实采：语句被收集时，输出是一张表，列是 `total`、`share`、`calls`、`mean`、`rows`、`read`、`temp`、`user`、`database`、`query`，表头说明数值是自上次重置以来的累计值。

- `share` 是这条语句占全部执行时间的比例，直接回答“数据库的时间花在哪”。哪条 SQL 算太贵没有客观线，所以 `top` 只展示，没有 finding。
- 数值是自上次统计重置以来的累计值。这个版本没有 `sys_stat_statements_info`，重置时间拿不到，表头直说了这点。`read` 和 `temp` 的单位是块。
- `track=all` 时，函数里执行的语句会在调用它的语句里再算一次，所以比例加起来会超过 100%，文本会说明。`track=none` 但有行时，文本说明这些是之前收集的，或者来自自己设了 `track` 的角色和库。
- 时间按量级换单位（0.09 ms、503 ms、1.75 s）。这个账号看不到的 query 显示 `?`。
- `top --interval`（最近 N 秒）这个版本不做。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK：语句有被收集 |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误，包括 `--by` 的值不对 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
