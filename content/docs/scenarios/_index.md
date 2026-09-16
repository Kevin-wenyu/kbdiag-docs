---
title: "Troubleshooting scenarios"
description: "Move from symptoms to evidence and verify the outcome."
weight: 40
---

Confirm the target instance before choosing a workflow. Examples use isolated lab sessions; reproducing the workload in production is unnecessary.

- [Running slow SQL](slow-sql/): find a PID and distinguish deliberate waits from execution issues.
- [Lock waits](lock-waits/): verify waiting and blocking sessions before handling transactions.
- [Real health check]({{< relref "/docs/get-started/reading-results" >}}): understand warnings and exit codes.
