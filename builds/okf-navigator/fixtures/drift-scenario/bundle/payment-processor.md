---
type: Module
title: payment_processor.py
description: charge() -- processes a payment.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2026-11-28T00:00:00Z
---
# payment_processor.py

Documented at the time this bundle was written: the only real consumer
is checkout_flow.py.

## Consumers

- [checkout-flow.md](./checkout-flow.md) -- imports `charge` directly.
