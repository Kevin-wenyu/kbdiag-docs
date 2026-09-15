---
title: "Get started"
weight: 10
type: docs
cascade:
  type: docs
---

Run as the kingbase OS user on a KingbaseES V8R6+ host.

```bash
sudo -i -u kingbase
curl -fsSL https://raw.githubusercontent.com/Kevin-wenyu/kbdiag/main/dist/kbdiag -o ~/kbdiag
chmod +x ~/kbdiag
~/kbdiag status
~/kbdiag check
echo $?
```

`check`: 0 OK, 1 WARN, 2 FAIL.
