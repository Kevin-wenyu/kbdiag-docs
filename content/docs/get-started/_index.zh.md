---
title: "第一次巡检"
description: "完成安装、连接配置、健康检查和结果解释。"
weight: 30
---

本页带你完成 `status` 和 `check`，再决定是否需要深查。命令在 **KingbaseES 主机**执行，网站构建环境不需要安装数据库。

## 1. 准备环境 {#requirements}

- KingbaseES V8R6+ 实例处于运行状态。
- 可以切换到 `kingbase` 系统用户，并使用数据库自带的 `ksql`。
- 已确认数据库端口、数据库名和数据库账号；账号需要具备所查系统视图的访问权限。
- repmgr 仅用于相关集群能力，单机巡检不要求安装它。

## 2. 安装工具 {#install}

先切换系统用户：

```bash
sudo -i -u kingbase
```

再下载单文件：

```bash
curl -fsSL https://raw.githubusercontent.com/Kevin-wenyu/kbdiag/main/dist/kbdiag \
  -o ~/kbdiag
chmod +x ~/kbdiag
~/kbdiag --version
```

若主机不能访问 GitHub，可在可联网机器下载仓库中的 `dist/kbdiag`，拷贝为数据库主机的 `~/kbdiag`，再赋予执行权限。已有同名文件时，下载会覆盖它；更新前可先备份。

## 3. 确认目标实例 {#connection}

默认端口是 `54321`，数据库是 `test`，数据库用户是 `system`。自动探测目录并不意味着自动识别所有连接参数。先运行：

```bash
~/kbdiag instances
~/kbdiag status
```

同机多实例时，先依据 `instances` 的输出确定目标端口及路径。需要自定义时，编辑 `~/.kbdiagrc`，将下面示例值改成实际值：

```bash
KB_PORT=54321
KB_DB=test
KB_SUPERUSER=system
KB_BIN_DIR=/实际安装目录/bin
KB_DATA_DIR=/实际数据目录
```

保存后重试 `~/kbdiag status`。若已有 `.kbdiagrc`，修改对应条目即可。该文件会作为 Shell 配置加载。

**连接失败时先处理连接问题：** 检查进程、端口、账号认证、目录和权限，不要把无法读取数据解释成正常。`check` 的数据库连通性检查失败会返回 `2`。

## 4. 执行健康检查 {#run-check}

```bash
~/kbdiag check
check_rc=$?
printf 'check exit code: %s\n' "$check_rc"
```

应紧接命令保存 `$?`，否则后续命令会覆盖它。按需查看更多信息：

```bash
~/kbdiag check -v
~/kbdiag check --os
```

`-v` 展开部分底层数据；`--os` 添加操作系统符合性检查。检查结果反映当次采样与当前阈值，不能代表所有时间的状态。

## 5. 解释退出码 {#exit-codes}

| `check` 退出码 | 意义 | 下一步 |
|---|---|---|
| `0` | 本次检查未触发 WARN / FAIL | 保留结果；业务仍异常时继续检查相关维度 |
| `1` | 存在告警 | 查看告警项目，结合业务与阈值判断 |
| `2` | 存在 FAIL 或数据库连通性失败 | 先确认失败项目与连接状态，再继续处理 |

这张表针对 `check`。不要套用到所有命令；多数查数据命令需要 `--exit-code` 才按检查发现返回健康判定，参数或运行错误也可能返回非零值。

[看一段标注为示意的结果解读](reading-results/)

## 6. 根据发现继续检查 {#next-check}

| 当前发现 | 下一条命令 | 关注什么 |
|---|---|---|
| 有锁等待 | `~/kbdiag locks wait` | 等待与阻塞信息 |
| 当前有慢查询 | `~/kbdiag perf slow` | 会话、耗时和 SQL |
| 复制相关告警 | `~/kbdiag replication` | 当前节点角色与复制状态 |
| 空间相关告警 | `~/kbdiag space` | 磁盘和数据库对象占用 |
| 多项异常需要关联 | `~/kbdiag diagnose` | 诊断证据、建议与复核路径 |

若要生成交接文件，可选择一个新文件名：

```bash
~/kbdiag report inspection.md
```

报告写入当前目录。查看报告中的 WARN / FAIL 与明细；报告命令本身也可能因发现问题返回非零值。

## 完成标准 {#done}

你已经确认目标实例、能够运行 `status` 和 `check`、理解检查退出码，并能根据一条发现找到下一条命令。

[了解全部功能](../features/) · [查阅命令参数](../reference/)
