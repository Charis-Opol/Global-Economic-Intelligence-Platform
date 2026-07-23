FROM apache/airflow:2.9.3-python3.11

USER root
# openjdk needed by pyspark - even in client mode submitting to the remote
# spark-master cluster, pyspark bootstraps a local driver JVM first, which
# has no Java of its own otherwise (this is a plain Python base image).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    openjdk-17-jre-headless \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# pip-installed pyspark ships its own jars/ (separate from spark-master/
# spark-worker's apache/spark:3.5.3 image, which already has these two added
# in spark/Dockerfile) and doesn't include the S3A connector by default -
# without it, run_spark_etl's read of s3a://bronze/... fails with
# ClassNotFoundException: org.apache.hadoop.fs.s3a.S3AFileSystem. Version
# pinned to match pyspark 3.5.3's own bundled hadoop-client-*-3.3.4.jar.
RUN PYSPARK_JARS="$(python -c "import pyspark, os; print(os.path.join(os.path.dirname(pyspark.__file__), 'jars'))")" && \
    curl -fsSL -o "$PYSPARK_JARS/hadoop-aws-3.3.4.jar" \
      https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -fsSL -o "$PYSPARK_JARS/aws-java-sdk-bundle-1.12.262.jar" \
      https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar
