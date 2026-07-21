FROM apache/spark:3.5.3

USER root
# jobs/ will hold the PySpark ETL scripts written in Day 1, Step 8
COPY jobs /opt/spark-jobs

# ETL jobs read/write s3a://bronze and s3a://silver (MinIO) via common.py's
# build_spark_session(), but the base image ships with no S3A connector at
# all - `s3a://` would fail with "No FileSystem for scheme" without these.
# Version pinned to match this image's own bundled hadoop-client-*-3.3.4.jar
# exactly - hadoop-aws is version-sensitive to the Hadoop it's paired with,
# and aws-java-sdk-bundle 1.12.262 is the version hadoop-aws 3.3.4 itself
# depends on.
RUN curl -fsSL -o /opt/spark/jars/hadoop-aws-3.3.4.jar \
      https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -fsSL -o /opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar \
      https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar
