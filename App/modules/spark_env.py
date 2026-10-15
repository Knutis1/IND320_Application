"""
Spark environment helper for the IND320 project (Windows).

Why this file exists:
  On Windows, PySpark needs two things that are easy to get wrong:
    1. JAVA_HOME pointing at a real JDK 11/17 folder (Spark 3.5 does not support Java 21+).
    2. HADOOP_HOME pointing at a folder containing bin\\winutils.exe and bin\\hadoop.dll.
  Instead of relying on system environment variables (which differ between the
  terminal, VS Code and the notebook kernel), this module finds them itself and
  sets them for the current process only.

Usage in a notebook or script:
    from spark_env import get_spark
    spark = get_spark()
"""

import glob
import os
import subprocess
import sys

# Folders where JDK installers usually put things, newest patterns first.
# Java 17 is preferred, then 11. Spark 3.5 does not support Java 21+.
JDK_PATTERNS = [
    r"C:\Program Files\Eclipse Adoptium\jdk-17*",
    r"C:\Program Files\Java\jdk-17*",
    r"C:\Program Files\Microsoft\jdk-17*",
    r"C:\Program Files\Amazon Corretto\jdk17*",
    r"C:\Program Files\Zulu\zulu-17*",
    r"C:\Program Files\Eclipse Adoptium\jdk-11*",
    r"C:\Program Files\Java\jdk-11*",
    r"C:\Program Files (x86)\Eclipse Adoptium\jdk-17*",
]

# Folders that may hold winutils.exe / hadoop.dll
HADOOP_CANDIDATES = [
    r"C:\hadoop",
    r"C:\winutils",
    os.path.join(os.path.expanduser("~"), "hadoop"),
]


def _is_jdk(path):
    """A usable JDK folder contains bin\\java.exe."""
    return bool(path) and os.path.isfile(os.path.join(path, "bin", "java.exe"))


def find_java_home():
    """Return a usable JDK folder, or None. Checks JAVA_HOME first, then disk."""
    current = os.environ.get("JAVA_HOME", "").strip().strip('"')
    if _is_jdk(current):
        return current

    for pattern in JDK_PATTERNS:
        # reverse=True so the newest patch version wins (jdk-17.0.16 before jdk-17.0.9)
        for candidate in sorted(glob.glob(pattern), reverse=True):
            if _is_jdk(candidate):
                return candidate
    return None


def find_hadoop_home():
    """Return a folder containing bin\\winutils.exe, or None."""
    current = os.environ.get("HADOOP_HOME", "").strip().strip('"')
    candidates = [current] + HADOOP_CANDIDATES
    for candidate in candidates:
        if candidate and os.path.isfile(os.path.join(candidate, "bin", "winutils.exe")):
            return candidate
    return None


def configure_env(verbose=True):
    """
    Set JAVA_HOME, HADOOP_HOME, PATH and the PySpark python variables for THIS
    process. Nothing is written to the Windows system settings, so this cannot
    break anything outside the running kernel.
    """
    java_home = find_java_home()
    if java_home is None:
        raise RuntimeError(
            "No Java 11/17 JDK found. Install Temurin JDK 17 from adoptium.net, "
            "then run this again."
        )

    hadoop_home = find_hadoop_home()
    if hadoop_home is None:
        raise RuntimeError(
            "winutils.exe not found. Expected C:\\hadoop\\bin\\winutils.exe "
            "(download winutils.exe and hadoop.dll from the cdarlint/winutils "
            "repo, folder hadoop-3.3.5/bin)."
        )

    os.environ["JAVA_HOME"] = java_home
    os.environ["HADOOP_HOME"] = hadoop_home

    # Put both bin folders first on PATH so Spark finds java.exe and winutils.exe
    extra_path = os.path.join(java_home, "bin") + os.pathsep + \
                 os.path.join(hadoop_home, "bin")
    os.environ["PATH"] = extra_path + os.pathsep + os.environ.get("PATH", "")

    # Make sure Spark uses the same Python as this process (the .venv one)
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    # Keep Spark on localhost; avoids slow or failing hostname lookups on Windows
    os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"

    if verbose:
        print("JAVA_HOME   :", java_home)
        print("HADOOP_HOME :", hadoop_home)
        version = subprocess.run(
            [os.path.join(java_home, "bin", "java.exe"), "-version"],
            capture_output=True, text=True,
        ).stderr.strip().splitlines()
        print("Java        :", version[0] if version else "unknown")

    return java_home, hadoop_home


def get_spark(app_name="IND320", cassandra_host="127.0.0.1",
              cassandra_port="9042", with_cassandra=True, verbose=True):
    """
    Configure the environment and return a SparkSession.

    with_cassandra=False gives a plain Spark session with no connector download,
    which is useful when checking whether Spark itself works.
    """
    configure_env(verbose=verbose)

    from pyspark.sql import SparkSession  # imported after the env is set

    builder = (SparkSession.builder
               .appName(app_name)
               .master("local[*]")
               .config("spark.driver.host", "127.0.0.1")
               .config("spark.driver.bindAddress", "127.0.0.1")
               # keeps the startup log short
               .config("spark.ui.showConsoleProgress", "true"))

    if with_cassandra:
        builder = (builder
                   # downloaded once into C:\Users\<you>\.ivy2, cached afterwards
                   .config("spark.jars.packages",
                           "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1")
                   .config("spark.sql.extensions",
                           "com.datastax.spark.connector.CassandraSparkExtensions")
                   .config("spark.cassandra.connection.host", cassandra_host)
                   .config("spark.cassandra.connection.port", cassandra_port))

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")  # hide the WARN noise
    return spark
