# start from a small official python image
FROM python:3.12-slim

WORKDIR /app
# do not write pyc files and show logs right away
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# install security updates for the base system packages so the trivy check stays green
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# pip and setuptools are only needed to install packages
# removing them takes away the high cves trivy found in their bundled libraries
# these were urllib3 and msgpack and setuptools
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m pip uninstall -y pip setuptools wheel

# copy the migration files and the app code
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# run as a normal user and not as root
RUN useradd --create-home --uid 10001 appuser
USER 10001

EXPOSE 8000
# update the database tables first and then start the api
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
