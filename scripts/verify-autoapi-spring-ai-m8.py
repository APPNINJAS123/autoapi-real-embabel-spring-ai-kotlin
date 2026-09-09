#!/usr/bin/env python3
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1]
paths = [
    root / "embabel-agent-openai/src/main/kotlin/com/embabel/agent/openai/OpenAiCompatibleModelFactory.kt",
    root / "embabel-agent-autoconfigure/models/embabel-agent-dockermodels-autoconfigure/src/main/kotlin/com/embabel/agent/config/models/docker/DockerLocalModelsConfig.kt",
]
mode = sys.argv[1] if len(sys.argv) == 2 else "target"
if mode not in {"baseline", "target"}:
    raise SystemExit("usage: verify-autoapi-spring-ai-m8.py baseline|target")

sources = [path.read_text() for path in paths]
joined = "\n".join(sources)
if mode == "baseline":
    expected = [
        "6147bf70715066c63cb06a09399d3e29cf391827481dad9fc617c032c79de055",
        "6668a8d84d5c24e4abe12ee03081008b82bc4ee11f127df6aecee046291a8eaa",
    ]
    import hashlib
    actual = [hashlib.sha256(source.encode()).hexdigest() for source in sources]
    if actual != expected:
        raise SystemExit("immutable Spring AI 1.1.7 source baseline changed")
else:
    forbidden = [
        "org.springframework.ai.openai.api.OpenAiApi",
        ".openAiApi(",
        ".defaultOptions(",
    ]
    for token in forbidden:
        if token in joined:
            raise SystemExit(f"removed Spring AI 1 API remains: {token}")
    for index, source in enumerate(sources):
        for token in [
            "com.openai.client.OpenAIClient",
            "com.openai.client.okhttp.OpenAIOkHttpClient",
            "OpenAIOkHttpClient.builder()",
            ".openAiClient(",
            ".options(",
            "ObservationRegistry",
        ]:
            if token not in source:
                raise SystemExit(f"source {index + 1} lacks target contract: {token}")
    factory = sources[0]
    for token in [
        ".timeout(Duration.ofMillis(READ_TIMEOUT_MS))",
        'builder.apiKey("no-auth")',
        "builder.apiKey(apiKey)",
        "builder.baseUrl(baseUrl)",
        "builder.putHeader(name, value)",
        ".customHeaders(httpHeaders)",
        "OpenAiEmbeddingModel(",
        "openAiClient,",
        "observationRegistry",
    ]:
        if token not in factory:
            raise SystemExit(f"factory migration contract missing: {token}")

print(f"verified Spring AI OpenAI {mode} contract")
