FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app/src PYTHONUNBUFFERED=1

COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

COPY src/ ./src/

# Bake the cache into the image: the container then has no cold-build step and
# /api/v1/health is green the moment the process is up.
RUN python -m qmems_cache.build_cache --days 10 --test-days 3 --seed 0

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/v1/health').status==200 else 1)"
CMD ["uvicorn", "qmems_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
