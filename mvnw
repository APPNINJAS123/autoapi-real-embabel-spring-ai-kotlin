#!/bin/sh
set -eu

MAVEN_VERSION=3.9.11
MAVEN_SHA512=bcfe4fe305c962ace56ac7b5fc7a08b87d5abd8b7e89027ab251069faebee516b0ded8961445d6d91ec1985dfe30f8153268843c89aa392733d1a3ec956c9978
AUTOAPI_TEMP_ROOT=${RUNNER_TEMP:-${TMPDIR:-/tmp}}
MAVEN_ROOT="$AUTOAPI_TEMP_ROOT/autoapi-apache-maven-$MAVEN_VERSION"
MAVEN_HOME="$MAVEN_ROOT/apache-maven-$MAVEN_VERSION"

if test ! -x "$MAVEN_HOME/bin/mvn"; then
  mkdir -p "$MAVEN_ROOT"
  archive="$MAVEN_ROOT/apache-maven-$MAVEN_VERSION-bin.tar.gz"
  curl --fail --location --proto '=https' --tlsv1.2 --retry 3 \
    "https://archive.apache.org/dist/maven/maven-3/$MAVEN_VERSION/binaries/apache-maven-$MAVEN_VERSION-bin.tar.gz" \
    --output "$archive"
  printf '%s  %s\n' "$MAVEN_SHA512" "$archive" | sha512sum --check --strict
  tar -xzf "$archive" -C "$MAVEN_ROOT"
fi

exec "$MAVEN_HOME/bin/mvn" "$@"
