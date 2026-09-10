# AutoAPI acceptance mirror provenance

This private mirror preserves the full Git history and Apache-2.0 license of
`embabel/embabel-agent` at immutable upstream revision
`dec1e3970ba1f1e028a51ae5e198c8ee57310dc6`.

## Source-preserving actual-consumer overlay

The original normalization at `6730800c9010bc288a90a43c64567838fce8e96a`
compiled independent sample contracts. That historical check did **not** prove
that the actual model-edited customer files compiled. Those samples remain in
history, but neither is a source input to the current acceptance build.

The stronger isolated proof module copies these two **complete actual files**,
without filtering or rewriting, into its generated-source directory:

- `embabel-agent-openai/src/main/kotlin/com/embabel/agent/openai/OpenAiCompatibleModelFactory.kt`
- `embabel-agent-autoconfigure/models/embabel-agent-dockermodels-autoconfigure/src/main/kotlin/com/embabel/agent/config/models/docker/DockerLocalModelsConfig.kt`

Both application files remain byte-identical to the upstream revision at this
baseline. The verifier pins their original SHA-256 hashes, checks that compiler
inputs equal the checked-out bytes, requires their output classes, and performs
two temporary negative compiler probes. Each probe adds a type error to one
copied actual file and must be rejected. No model patch or migration is supplied
by the test overlay.

The proof POM now actively defaults to the exact historical SDK `1.1.7`, instead
of defaulting to the `2.0.0-M8` target behind an inactive baseline profile. This
is a test-only dependency normalization: the upstream reactor uses unpublished
`2.0.0-SNAPSHOT` parents, so this is **not a complete Embabel reactor build**.
Released Apache-2.0 Embabel API/BYOK `0.4.0` artifacts supply unrelated framework
types; their `RetryProperties` source is byte-identical to the upstream source
(`a3de4010a79ff9b27b163a05fd220dd812def9fd8405360af7f5f73bbd80d6df`).
No fake Embabel or Spring AI implementation is substituted. Unused MCP starter
and vector-store dependencies are excluded from this two-consumer boundary.

An explicit Spring AI BOM selects every resolved Spring AI artifact at exactly
the chosen old/target version. The verifier rejects mixed versions and duplicate
SDK artifacts, checks all six actual SDK JARs against their pinned official
Maven Central SHA-256 hashes, and records those resolved artifact identities.
Framework/Boot BOMs select `6.2.18`/`3.5.14` for the old SDK and
`7.0.7`/`4.1.0-RC1` for the target. The target Boot version matches the official
Spring AI `v2.0.0-M8` source POM, avoiding a downgrade of its Micrometer APIs.
The target includes the real Jackson 3 Kotlin module required to deserialize
the unchanged Docker configuration's Kotlin response classes under Spring 7.
The target preparation/validation argument activates this framework profile;
the verifier separately requires the checked-in SDK property to equal the
target, so an unchanged old manifest cannot pass using a command-line override.
Before Maven runs, a canonical SHA-256 guard permits only that one exact SDK
property value to change. Compiler inputs, plugin/test configuration, unrelated
dependencies, and every other manifest byte must remain as reviewed. The product
must run the same `target --manifest-only` guard before target preparation or
validation, then `target --compiled` after `clean verify`.
Java remains exact Temurin `21.0.8+9`; actual Embabel inline functions require
JVM target 21. Maven remains `3.9.11`, Kotlin `2.2.20`.

Three JUnit tests invoke the actual factory/configuration entry points with real
Spring AI clients against a loopback-only HTTP server. They check chat output,
model names, credentials, custom headers, embedding values/dimensions, and Docker
model discovery/registration and requests. Test credentials are intentionally
invalid placeholders. No external model or Docker service is contacted. These
checks do not claim complete framework startup, BYOK error handling, streaming,
every custom endpoint option, or the full upstream test suite.

The reviewed workflow checks out the exact PR head with no persisted credential,
uses only a read-only workflow token and no repository secrets, restricts PR
changes to the two consumers plus the exact isolated dependency manifest, and
performs online then offline compile/tests. Its baseline dispatch preserves
the upstream source/license and verifies the exact overlay allowlist. All
inherited workflows remain disabled in repository settings. A green baseline
is readiness evidence only, not a Part A + Part B migration result.
