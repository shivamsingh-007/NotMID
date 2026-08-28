# AI Model Gateway

Only approved boundary for model providers and managed inference. Owns credentials, provider routing, prompt/model versions, PHI minimization, timeouts, cost limits and safety policy enforcement.

The initial local route is an internal vLLM endpoint serving HiMed 8B as an evaluation candidate. Clients cannot choose arbitrary models, and no service calls vLLM directly. The gateway must preserve a manual/degraded path and make model replacement possible without changing clinical APIs.
