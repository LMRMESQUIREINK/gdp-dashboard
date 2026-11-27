---
type: Service
title: Authentication Service
verified:
  - { by: human:secteam@acme, at: 2026-05-01T00:00:00Z }
stale_after: 2027-01-01T00:00:00Z
---
# Authentication Service
Issues and validates session tokens for all customer-facing apps.
Token lifetime is governed by [Token Policy](./token-policy.md).
Consumed directly by the [API Gateway](./api-gateway.md).
