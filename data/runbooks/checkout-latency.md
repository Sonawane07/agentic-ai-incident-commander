# Checkout API Latency Runbook

## Symptoms

Checkout latency incidents usually show elevated `p95_latency_ms`, increased checkout error rate, and customer reports of delayed order confirmation. Check whether throughput increased; if throughput is stable, prioritize dependency waits, database pool saturation, and recent code changes.

## Investigation

Compare alert start time with deployments in the previous 30 minutes. Inspect logs for timeout signatures such as `PAYMENT_AUTH_TIMEOUT`, `DB_POOL_EXHAUSTED`, and order reservation rollback. Review traces for waits in payment authorization, inventory reservation, and order persistence.

## Mitigation

If latency started after a deployment and evidence points to the checkout service, prefer rollback to the previous stable version. If database pool usage is above 90 percent, temporarily scale the pool only after confirming the database can accept more connections.
