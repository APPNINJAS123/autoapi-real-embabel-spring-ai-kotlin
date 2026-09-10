#!/usr/bin/env python3
import pathlib
import sys
import hashlib
import json
import os
import stat
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

root = pathlib.Path(__file__).resolve().parents[1]
paths = [
    root / "embabel-agent-openai/src/main/kotlin/com/embabel/agent/openai/OpenAiCompatibleModelFactory.kt",
    root / "embabel-agent-autoconfigure/models/embabel-agent-dockermodels-autoconfigure/src/main/kotlin/com/embabel/agent/config/models/docker/DockerLocalModelsConfig.kt",
]
arguments = sys.argv[1:]
mode = arguments.pop(0) if arguments and not arguments[0].startswith("--") else "target"
if mode not in {"baseline", "target"}:
    raise SystemExit("usage: verify-autoapi-spring-ai-m8.py baseline|target [--manifest-only] [--compiled] [--negative]")
if any(argument not in {"--manifest-only", "--compiled", "--negative"} for argument in arguments):
    raise SystemExit("unknown verification argument")
version = "1.1.7" if mode == "baseline" else "2.0.0-M8"
pom_path = root / "autoapi-kotlin-proof/pom.xml"
pom_stat = pom_path.lstat()
if not stat.S_ISREG(pom_stat.st_mode) or not 0 < pom_stat.st_size <= 65536:
    raise SystemExit("proof POM must be a bounded regular non-symlink file")
pom_bytes = pom_path.read_bytes()
version_property = f"<spring-ai.version>{version}</spring-ai.version>".encode()
if pom_bytes.count(version_property) != 1:
    raise SystemExit("expected exactly one reviewed SDK version property in a regular proof POM")
canonical_pom = pom_bytes.replace(version_property, b"<spring-ai.version>AUTOAPI_REVIEWED_SDK_VERSION</spring-ai.version>")
if hashlib.sha256(canonical_pom).hexdigest() != "88c8b06f3280ecc30207f17684cdf5fb3560162b5fb0361623ec89ec1dac7d79":
    raise SystemExit("proof POM changed outside the single reviewed SDK version property")
pom = ET.fromstring(pom_bytes)
namespace = {"m": "http://maven.apache.org/POM/4.0.0"}
if pom.findtext("m:properties/m:spring-ai.version", namespaces=namespace) != version:
    raise SystemExit(f"checked-in proof POM must activate exact SDK {version}")
if "--manifest-only" in arguments:
    if arguments != ["--manifest-only"]:
        raise SystemExit("manifest-only cannot be combined with source/compiled verification flags")
    print(f"verified immutable consumer-build POM with exact SDK {version}")
    raise SystemExit(0)

sources = [path.read_text() for path in paths]
joined = "\n".join(sources)
if mode == "baseline":
    expected = [
        "6147bf70715066c63cb06a09399d3e29cf391827481dad9fc617c032c79de055",
        "6668a8d84d5c24e4abe12ee03081008b82bc4ee11f127df6aecee046291a8eaa",
    ]
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
        "customHeaders(httpHeaders)",
        "OpenAiEmbeddingModel(",
        "openAiClient,",
        "observationRegistry",
    ]:
        if token not in factory:
            raise SystemExit(f"factory migration contract missing: {token}")

if "--compiled" in arguments:
    proof = root / "autoapi-kotlin-proof/target"
    receipts = []
    for source in paths:
        package_path = pathlib.Path(str(source).split("/src/main/kotlin/", 1)[1])
        staged = proof / "actual-consumers" / package_path
        compiled = proof / "classes" / package_path.with_suffix(".class")
        if staged.is_symlink() or staged.read_bytes() != source.read_bytes() or not compiled.is_file():
            raise SystemExit(f"actual consumer was not copied byte-for-byte and compiled: {source.name}")
        receipts.append({"path": str(source.relative_to(root)), "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                         "compiledClassSha256": hashlib.sha256(compiled.read_bytes()).hexdigest()})
    staged_files = sorted(path.relative_to(proof / "actual-consumers").as_posix()
                          for path in (proof / "actual-consumers").rglob("*.kt"))
    if len(staged_files) != 2:
        raise SystemExit("only the two reviewed actual consumers may be compiled")
    suite = ET.parse(proof / "surefire-reports/TEST-com.embabel.autoapi.ActualConsumerTest.xml").getroot()
    if int(suite.attrib["tests"]) != 3 or any(int(suite.attrib[key]) for key in ["failures", "errors", "skipped"]):
        raise SystemExit("all three real consumer loopback tests must pass without skips")
    classpath = (proof / "consumer-classpath.txt").read_text().strip().split(os.pathsep)
    sdk_jars = []
    # Immutable Maven Central JAR bytes downloaded while reviewing this overlay.
    expected_sdk = {
        "1.1.7": {
            "spring-ai-openai": "38df0789a4a889c580a8868347b38c18580669ea17f89d12d6c530154b59e277",
            "spring-ai-model": "0e0ed0aab5e83c966260ac2afe1272a902a7a6b9b7006fbbb85d75ac29257ce5",
            "spring-ai-commons": "63cda77ea187d429a2cd5448916ea546aebac99521c700204aa9a194037fb40c",
            "spring-ai-template-st": "b155bf17174edfc89c1df54dddcb7c2b7bc2b84cffc197fd98937c9f8151d5f0",
            "spring-ai-client-chat": "ad71a11f65e2caf7f6cc7232f483bb57ded97a87a4d20c7abc7dfea0cbeeed6f",
            "spring-ai-retry": "5725b8187558fa0f02be8cb4142f29f62638ae2d1f37b0fbd759d837b588a7e1",
        },
        "2.0.0-M8": {
            "spring-ai-openai": "dd956118d84a12b7742979adc2fc67fd398fd72dde759e1980f8ae84036f3a62",
            "spring-ai-model": "5f28b1afe6b7cbf72c85e90c1d736024f8ea6e94189ecca62b79f1e2623b778b",
            "spring-ai-commons": "8e5ad4328e0b0a0c5e50b869b273eb11219202cf00fb22d6e8217f24dd040889",
            "spring-ai-template-st": "491f312eaf235178214b5bfefd2517614ba527301f753597b9ba5b3a2ab306aa",
            "spring-ai-client-chat": "1e0fdfb68557e49933d439d2678d422adfecd7cd874eac44420cc06fd73b9194",
            "spring-ai-retry": "c11e8f1ee8ba4775db7d33a3f6aecd04d3dfde16deddcac3c08ecd5b68640749",
        },
    }
    artifact_names = set()
    for entry in classpath:
        jar = pathlib.Path(entry)
        if "/org/springframework/ai/" not in jar.as_posix():
            continue
        artifact = jar.parent.parent.name
        if jar.parent.name != version or artifact in artifact_names or jar.is_symlink():
            raise SystemExit("mixed-version or duplicate Spring AI SDK classpath")
        artifact_names.add(artifact)
        digest = hashlib.sha256(jar.read_bytes()).hexdigest()
        sdk_jars.append({"artifact": artifact, "version": version, "sha256": digest})
        if digest != expected_sdk[version].get(artifact):
            raise SystemExit(f"resolved Spring AI JAR does not match immutable official artifact: {artifact}")
    if artifact_names != set(expected_sdk[version]):
        raise SystemExit("real SDK classpath differs from the six reviewed SDK artifacts")
    print(json.dumps({"scope": "two-actual-kotlin-consumers-not-whole-embabel-reactor", "mode": mode,
                      "sources": receipts, "realSdkJars": sorted(sdk_jars, key=lambda item: item["artifact"]),
                      "loopbackTests": 3}, sort_keys=True))

if "--negative" in arguments:
    for source in paths:
        with tempfile.TemporaryDirectory(prefix="autoapi-kotlin-negative-") as temporary:
            probe = pathlib.Path(temporary)
            for original in [*paths, root / "autoapi-kotlin-proof/pom.xml", root / "mvnw"]:
                destination = probe / original.relative_to(root)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, destination)
            mutated = probe / source.relative_to(root)
            mutated.write_bytes(mutated.read_bytes() + b'\nprivate val autoapiNegativeCompile: Int = "must not compile"\n')
            result = subprocess.run(["./mvnw", "-o", "-B", f"-Dspring-ai.version={version}", "-f", "autoapi-kotlin-proof/pom.xml", "clean", "compile"],
                                    cwd=probe, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
            if result.returncode == 0 or source.name not in result.stdout or "[ERROR]" not in result.stdout:
                raise SystemExit(f"negative compiler probe did not reject actual {source.name}")
            print(f"negative actual-consumer compiler probe rejected {source.name}")

print(f"verified Spring AI OpenAI {mode} contract")
