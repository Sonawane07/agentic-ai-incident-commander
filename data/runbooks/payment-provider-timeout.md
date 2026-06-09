# Payment Provider Timeout Runbook

## Symptoms

Payment provider timeout incidents show increased authorization failures, retry attempts, and customer-facing payment errors. Provider-side incidents usually include elevated adapter latency or provider health warnings.

## Investigation

Check payment adapter logs and provider status. If provider latency remains normal while checkout logs show caller-side timeout, investigate retry fanout, checkout request deadlines, and database waits before declaring a provider outage.

## Mitigation

If provider health is degraded, fail over to the secondary provider after approval. If provider health is normal, avoid failover and investigate checkout-side behavior first.
