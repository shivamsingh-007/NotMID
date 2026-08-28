# AI Model Gateway

Only approved boundary for model providers and managed inference. It is an internal model router, not the public API gateway. It owns provider policy, prompt/model versions, PHI minimization, deadline/admission decisions, token/cost limits and safety enforcement. Provider credentials are scoped to isolated provider worker pools rather than shared with callers or other pools.

The primary route is an internal vLLM endpoint serving HiMed 8B as an evaluation candidate. A separately evaluated smaller local summarizer provides fast degraded summary generation. OpenAI and Claude are isolated external adapters, never direct application dependencies. Clients cannot choose arbitrary models. External routing requires explicit task/facility/purpose/residency/provider eligibility and never occurs merely because local GPUs are saturated. Every route passes through one versioned normalization contract, and the gateway preserves manual/degraded paths.
