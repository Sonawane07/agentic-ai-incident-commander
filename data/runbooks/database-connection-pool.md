# Database Connection Pool Saturation Runbook

## Symptoms

Database connection pool saturation appears when pool usage exceeds 90 percent, query wait time increases, and application logs show `DB_POOL_EXHAUSTED`. Customer-facing latency can rise even when CPU and memory remain normal.

## Investigation

Check whether a deployment increased request concurrency, retry fanout, or transaction duration. Compare pool usage with throughput. Stable throughput with rising pool usage often means code is holding connections longer or creating overlapping work.

## Mitigation

First reduce the source of connection pressure, usually by rolling back a risky deployment or disabling the feature flag that increased concurrency. Scaling the pool can be a temporary mitigation, but it should be approved and monitored.
