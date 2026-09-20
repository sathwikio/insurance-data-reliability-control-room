#!/Users/sathwik/Documents/Projects/insurance-opencode/.venv/bin/python
"""Python replacement for the bash spark-submit wrapper (sandbox/pwfix).

Why: the stock script goes through /bin/bash, which is a hardened-runtime
binary on macOS, and the kernel strips DYLD_* env vars from it. This sandbox
needs DYLD_INSERT_LIBRARIES (passwd interposer) to reach the JVM so Hadoop's
UnixLoginModule does not crash.

This faithfully reproduces bin/spark-class: run the Spark launcher JVM,
read its NUL-separated output, and exec the driver command it prints.
"""
import os
import shlex
import subprocess
import sys

SPARK_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        sys.stderr.write("ERROR: JAVA_HOME is not set.\n")
        return 1
    runner = os.path.join(java_home, "bin", "java")

    env = dict(os.environ)
    env["SPARK_HOME"] = SPARK_HOME
    if "SPARK_SCALA_VERSION" not in env:
        for name in sorted(os.listdir(os.path.join(SPARK_HOME, "jars"))):
            if name.startswith("spark-core_"):
                env["SPARK_SCALA_VERSION"] = name.split("spark-core_")[1].split("-")[0]
                break

    launcher_opts = shlex.split(os.environ.get("SPARK_SUBMIT_OPTS", ""))
    classpath = os.path.join(SPARK_HOME, "jars", "*")
    cmd = [runner, "-Xmx128m", *launcher_opts, "-cp", classpath,
           "org.apache.spark.launcher.Main", "org.apache.spark.deploy.SparkSubmit",
           *sys.argv[1:]]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, env=env)
    out = proc.stdout.decode("utf-8", "surrogateescape")
    final = [a.strip("\r\n") for a in out.split("\0") if a.strip("\r\n")]
    if not final:
        sys.stderr.write("ERROR: Spark launcher produced no command.\n")
        return 1
    os.execve(final[0], final, env)
    return 0


if __name__ == "__main__":
    sys.exit(main())
