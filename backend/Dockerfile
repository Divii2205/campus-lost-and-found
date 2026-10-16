FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# security updates for the base OS packages (keeps the Trivy gate green)
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# pip and setuptools are only needed to install; removing them drops the HIGH CVEs Trivy found
# in their bundled libraries (urllib3, msgpack, setuptools) from the runtime image
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m pip uninstall -y pip setuptools wheel

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# run as a non-root user
RUN useradd --create-home --uid 10001 appuser
USER 10001

EXPOSE 8000
# apply database migrations, then start the API
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
