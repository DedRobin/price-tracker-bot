FROM python:3.10-slim

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends vim && \
    apt-get install -y iputils-ping
COPY requirements_deploy.txt requirements.txt
COPY . /app

RUN pip install --trusted-host pypi.org --no-cache-dir --upgrade pip && \
    pip install --trusted-host pypi.org --no-cache-dir -r requirements.txt && \
    pip install --trusted-host pypi.org --no-cache-dir python-telegram-bot[webhooks]

WORKDIR /app