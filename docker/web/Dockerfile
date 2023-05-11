FROM registry.lil.tools/library/python:3.9-bullseye
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_SRC=/usr/local/src

RUN apt-get update && apt-get install -y nano postgresql-client

RUN mkdir -p /app/web
WORKDIR /app/web

# pip
COPY web/requirements.txt /app/web
RUN pip install -r requirements.txt \
    && rm requirements.txt

# Install Node
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install -y nodejs

# Install Yarn
RUN npm install -g yarn
