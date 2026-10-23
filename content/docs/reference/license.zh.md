---
title: "license：KES 授权"
description: "授权还剩几天、授权文件里写了什么；剩 30 天以内报 WARN，到期报 FAIL。"
weight: 220
---

采集于 2026-10-23（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `5efa1fc` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。没有注入故障。两台实验机都是永久授权，所以下面的实采结果都是 OK；WARN 和 FAIL 的例子取自单元测试的夹具，不是实采（见下文）。数值只属于本次采样。

## 用法

```text
kbdiag license [--json]
```

| 参数 | 作用 |
|---|---|
| `--json` | 输出 JSON |

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。没有阈值参数：30 天这条线是服务器自己定的。

## 为什么要这条命令

KES 只在实例启动时校验授权。授权到期不会让正在运行的实例停下，查询照常，问题要到下次重启才暴露：启动报 `license file expired`，起不来。计划内的维护重启或故障切换，正是最不想碰上这件事的时候。`license` 用 `get_license_validdays()` 读出剩余天数，日常巡检就能提前发现。

## 主库

```bash
~/kbdiag license
echo EXIT_CODE=$?
```

```text
license  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-23T13:57:00+08:00)

license
  left             permanent
  file             /home/kingbase/cluster/install/kingbase/bin/../../license.dat
  product          KingbaseES V8
  edition          SALES-企业版 V8R6
  version          V008R006C
  produced on      2021-10-13
  validity         0
  floating base    off (counts from the production date)
  mac              00:00:00:00:00:00
  max connections  0
  KES checks the license only when the instance starts
EXIT_CODE=0
```

- `left` 来自 `get_license_validdays()`：`-2` 是永久授权（`permanent`），其他负数表示已过期，否则是剩余天数。
- 其余各行来自 `get_license_info()`：`file` 是实例加载的授权文件，然后依次是产品名、细分版本模板、版本号、生产日期、有效期间、有效期从生产日期算还是从加载那天算（`floating base`）、绑定的 MAC 地址、最大连接数。授权里标为禁用的字段显示 `-`。
- `validity 0`、全零的 MAC 和 `max connections 0` 按 KES 返回的原样展示。这里的 `0` 是什么意思没有文档说明；这份永久授权三项都是 0。
- 授权里的用户名称、项目名称和序列号不展示：诊断用不到，又是客户信息。文件路径照样展示，因为要知道实例读的是哪份 `license.dat`；路径里可能带客户的目录名，把输出贴到别处时注意。

## 备库

```bash
~/kbdiag license
echo EXIT_CODE=$?
```

```text
license  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-23T13:57:29+08:00)

license
  left             permanent
  file             /home/kingbase/cluster/install/kingbase/bin/../../license.dat
  product          KingbaseES V8
  edition          SALES-企业版 V8R6
  version          V008R006C
  produced on      2021-10-13
  validity         0
  floating base    off (counts from the production date)
  mac              00:00:00:00:00:00
  max connections  0
  KES checks the license only when the instance starts
EXIT_CODE=0
```

备库按同样的规则判。每个节点各有一份 `license.dat`，备库升主以后也要靠自己的授权才能再启动，所以每个节点都要跑 `license`。

## 没有权限时

`kbdiag_ro`（没有监控角色，走 `127.0.0.1`）：

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro license
echo EXIT_CODE=$?
```

除了首行是 `kbdiag_ro@remote`，输出和上面主库的完全相同，退出码 0；备库上也一样。两个函数 PUBLIC 都能执行，不需要授予任何角色。

## JSON

```bash
~/kbdiag --json license
```

```json
{
  "command": "license",
  "verdict": "OK",
  "context": {
    "version": "KingbaseES V008R006C009B0014",
    "role": "primary",
    "location": "local",
    "user": "system",
    "database": "test",
    "collected_at": "2026-10-23T13:57:30+08:00"
  },
  "data": {
    "license.info": {
      "status": "ok",
      "reason": null,
      "columns": [
        "valid_days",
        "file",
        "product",
        "edition",
        "product_version",
        "produced_on",
        "validity_period",
        "floating_base",
        "mac",
        "max_connections"
      ],
      "rows": [
        [
          -2,
          "/home/kingbase/cluster/install/kingbase/bin/../../license.dat",
          "KingbaseES V8",
          "SALES-企业版 V8R6",
          "V008R006C",
          "2021-10-13",
          "0",
          false,
          "00:00:00:00:00:00",
          "0"
        ]
      ],
      "truncated": 0
    }
  },
  "findings": [],
  "redacted": []
}
```

`valid_days` 保留原始数值（这里是 `-2`）。定时巡检只看退出码就够了：1 表示该续了，2 表示下次重启前必须换好。

## 快到期和已到期

取自单元测试的夹具（`license_expiring` 和 `license_expired`），不是实采：两台实验机都是永久授权，快到期的授权要找厂商出。判定本身只是一次整数比较，单元测试覆盖了边界（`-2`、`-1`、`0`、`1`、`30`、`31`、极值、NULL）。

```text
license  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T21:20:09+08:00)

[WARN] license.expiring  the license expires in 12 days: the instance keeps running, but after that it will not start again
  fix: SELECT sys_reload_license('<new license.dat>')  # ask the vendor's sales for a new license now, then load it; or sys_ctl reload_license <file> (V8R6) / sys_ctl -D <data> reload_license -L <file> (V9); the KES FAQ says no restart is needed, not tried by kbdiag: check with the verify step
  verify: SELECT get_license_validdays()  # after the new license.dat is in place: -2 is permanent, else the days left

license
  left             12 days
  ...
```

```text
license  FAIL  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T21:20:09+08:00)

[FAIL] license.expired  the license has expired: the instance keeps running, but it will not start again after a restart
  fix: SELECT sys_reload_license('<new license.dat>')  # do not restart this instance before the new license is loaded; the license itself comes from the vendor's sales; or sys_ctl reload_license <file> (V8R6) / sys_ctl -D <data> reload_license -L <file> (V9); the KES FAQ says no restart is needed, not tried by kbdiag: check with the verify step
  verify: SELECT get_license_validdays()  # after the new license.dat is in place: -2 is permanent, else the days left

license
  left             expired (-1)
  ...
```

- `license.expiring`（WARN）：剩 0 到 30 天。线是服务器自己的：到期前 30 天，KES 在登录时提示 `License file will expire in 30 days`。
- `license.expired`（FAIL）：`-2` 以外的任何负数。KES 社区说明 `-1` 表示已过期，也有人报告过其他负数；kbdiag 把不认识的负数当成过期，不报 OK。实例还在跑，但下次启动注定失败，所以是 FAIL。
- `get_license_validdays()` 返回 NULL 时，`left` 一行写明原因，结论是 UNKNOWN。
- fix 用 `sys_reload_license()` 加载新授权，V8R6 和 V9 都有这个函数。`sys_ctl` 的写法分版本（V8R6C9 的 `--help` 是 `sys_ctl reload_license LICENSE_FILE`，V9 FAQ 是 `sys_ctl -D … reload_license -L …`），两种都写进了说明。KES FAQ 说不用重启；实验环境没试过，换完用 `verify` 的查询核对。kbdiag 自己从不加载授权：它是只读的，授权也由厂商出，不是数据库能修的。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：授权 30 天内到期 |
| 2 | FAIL：授权已到期，实例再启动就起不来 |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
