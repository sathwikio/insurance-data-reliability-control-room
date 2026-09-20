#!/bin/zsh
# One-time sandbox setup. Idempotent.
#
# 1. Builds the passwd interposer (sandbox needs it for Hadoop's UnixLoginModule).
# 2. Replaces the venv pyspark spark-submit wrapper with a Python version that
#    avoids /bin/bash, because hardened bash strips DYLD_* env vars and the
#    interposer would never reach the driver JVM.
#
# The JDK and PySpark dependencies are installed out-of-band (see README).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 1. interposer dylib
if [ ! -f "$ROOT/sandbox/pwfix/libpwfix.dylib" ]; then
  clang -dynamiclib -o "$ROOT/sandbox/pwfix/libpwfix.dylib" "$ROOT/sandbox/pwfix/pwfix.c"
fi

# 2. spark-submit wrapper
SPARK_SUBMIT="$ROOT/.venv/lib/python3.12/site-packages/pyspark/bin/spark-submit"
if [ -f "$SPARK_SUBMIT" ] && head -1 "$SPARK_SUBMIT" | grep -q bash; then
  mv "$SPARK_SUBMIT" "$SPARK_SUBMIT.bash.orig"
  sed "s|#!/.*python.*|#!$ROOT/.venv/bin/python|" "$ROOT/sandbox/spark_submit_wrapper.py" > "$SPARK_SUBMIT"
  chmod +x "$SPARK_SUBMIT"
fi

echo "sandbox setup complete"
