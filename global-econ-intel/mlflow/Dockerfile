FROM python:3.11-slim

RUN pip install --no-cache-dir \
    mlflow==2.16.0 \
    psycopg2-binary==2.9.9 \
    boto3==1.35.0

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
