---
title: "Troubleshooting scenarios"
description: "Move from a symptom to the evidence, then confirm the outcome."
weight: 40
---

Confirm you are on the right instance before following a scenario. The examples come from fault-injection scripts on a lab cluster; you do not need to reproduce them in production.

- [Long-running SQL](slow-sql/): find a statement that has been running for a while and what it waits on.
- [Lock waits](lock-waits/): find who waits, follow the verify line to the blocker, and confirm the waits are gone.
- [Read a real result]({{< relref "/docs/get-started/reading-results" >}}): a WARN in text and JSON, line by line.
