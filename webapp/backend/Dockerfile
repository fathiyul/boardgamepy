FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY webapp/backend/requirements.txt /app/webapp/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/webapp/backend/requirements.txt

COPY src /app/src
COPY examples /app/examples
COPY webapp /app/webapp

EXPOSE 8080
CMD ["sh", "-c", "uvicorn webapp.backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
