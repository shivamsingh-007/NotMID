# AI Model Gateway

Only approved boundary for model providers and managed inference. It is an internal model router, not the public API gateway. It owns provider policy, prompt/model versions, PHI minimization, deadline/admission decisions, token/cost limits and safety enforcement. Provider credentials are scoped to isolated provider worker pools rather than shared with callers or other pools.

The initial local route is an internal vLLM endpoint serving HiMed 8B as an evaluation candidate. Clients cannot choose arbitrary models, and no service calls vLLM or an external provider directly. External routing requires explicit task/facility/purpose/residency/provider eligibility and never occurs merely because local GPUs are saturated. Local and external responses pass through one versioned normalization contract. The gateway preserves manual/degraded paths and makes model replacement possible without changing clinical APIs.
