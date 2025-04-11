FROM python:3.12.12 AS prod

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.8.2

WORKDIR /server/

COPY pyproject.toml poetry.lock /server/

RUN poetry install --only main

RUN apt-get purge -y && rm -rf /var/lib/apt/lists/*

COPY . /server/