> ### Move session storage to Postgres in Q1, behind a dual-write flag.

- `K1` **Redis is now the riskiest part of the login path.**
  - `K1.1` Two of the last three login incidents started in Redis.
    - `K1.1.1` Failover dropped every session in the March incident.\
      ↳ *Postmortem PM-212: 41 minutes of forced logouts.*
    - `K1.1.2` Memory eviction logged users out during the June peak.
      - `K1.1.2.1` The maxmemory policy evicts live sessions first.\
        ↳ *allkeys-lru was set in 2021 and never revisited.*
  - `K1.2` Nobody on the team owns Redis operations.\
    ↳ *The last Redis owner left in 2024; the runbook is stale.*
* `K2` **Postgres can carry session load with headroom.**
  - `K2.1` Peak session reads fit the current primary.\
    ↳ *Load test: 9k reads/s at p99 4 ms on the existing instance.*
  - `K2.2` Writes stay small because sessions change rarely.\
    ↳ *Only 3% of requests mutate a session.*
- `K3` **So moving sessions to Postgres removes the risk at lower cost.**
  - `K3.1` One fewer datastore saves about \$14k a year.\
    ↳ *Current Redis cluster invoice, averaged over 12 months.*
  - `K3.2` A dual-write flag makes rollback a config change.\
    ↳ *The flag pattern is already used for the billing migration.*

**Caveats**

- The RFC does not estimate migration engineering effort.
