# Safe Rollback Procedure

## Preconditions

Rollback is appropriate when the incident began shortly after a deployment and multiple evidence sources point to the changed service. Confirm that the previous version is known stable and that database migrations are backward compatible.

## Steps

Record approval from the on-call engineer. Roll back the affected service to the previous stable version. Monitor latency, error rate, payment failure rate, and database pool usage for at least 10 minutes.

## Follow-Up

Create a follow-up issue for the risky change. Add a regression test for the incident condition. Update the runbook if the mitigation path was unclear.
