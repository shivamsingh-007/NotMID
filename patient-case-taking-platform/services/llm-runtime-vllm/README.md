# vLLM Runtime

Private GPU inference runtime behind the AI model gateway. It initially hosts an evaluated HiMed 8B candidate and exposes no public or product-facing endpoint.

Owns model loading, tensor/quantization configuration, batching, GPU resource limits, health probes and inference metrics. It does not own prompts, clinical workflow, authorization or safety decisions.
