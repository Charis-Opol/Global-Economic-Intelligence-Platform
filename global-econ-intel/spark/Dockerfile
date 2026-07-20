FROM apache/spark:3.5.3

USER root
# jobs/ will hold the PySpark ETL scripts written in Day 1, Step 8
COPY jobs /opt/spark-jobs

# SPARK_MODE is set per-service in docker-compose.yml (master | worker)
ENV SPARK_MODE=master
