---
title: "快速开始"
weight: 10
type: docs
cascade:
  type: docs
---

使用 kingbase 系统用户，在 KingbaseES V8R6+ 主机执行。

```bash
sudo -i -u kingbase
curl -fsSL https://raw.githubusercontent.com/Kevin-wenyu/kbdiag/main/dist/kbdiag -o ~/kbdiag
chmod +x ~/kbdiag
~/kbdiag status
~/kbdiag check
echo $?
```

`check`：0 正常，1 告警，2 故障。
