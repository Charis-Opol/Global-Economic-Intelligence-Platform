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
