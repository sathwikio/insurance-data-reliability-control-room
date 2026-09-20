#!/bin/zsh
# Environment bootstrap for running PySpark in this sandbox.
#
# This sandbox has two quirks that require workarounds:
#   1. System DNS resolution (getaddrinfo) is broken; direct DNS queries work.
#      A sitecustomize DNS shim handles Python-level fetches (see sandbox/dns/).
#   2. No passwd entry exists for the current user, which crashes Hadoop's
#      UnixLoginModule. A small dylib interposes getpwuid/getpwuid_r
#      (sandbox/pwfix/libpwfix.dylib). /bin/bash strips DYLD_* env vars,
#      so the venv's pyspark spark-submit wrapper is a Python script that
#      execs java directly (installed by sandbox/install.sh).
#
# Usage:  source env.sh

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

export JAVA_HOME="${JAVA_HOME:-/private/var/folders/6_/p5_rz5650tx4swwm7bt668n40000gn/T/opencode/jdk/jdk-17.0.20.1+1/Contents/Home}"
export DYLD_INSERT_LIBRARIES="$PROJECT_ROOT/sandbox/pwfix/libpwfix.dylib"
export PYSPARK_PYTHON="$PROJECT_ROOT/.venv/bin/python"
export PYSPARK_DRIVER_PYTHON="$PROJECT_ROOT/.venv/bin/python"
export SPARK_LOCAL_IP=127.0.0.1

alias vpython="$PROJECT_ROOT/.venv/bin/python"
