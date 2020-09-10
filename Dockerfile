# Dockerfile

FROM python:3.8.5-alpine3.12

ENV VIRTUAL_ENV=/blockstore/venv

RUN apk update && apk upgrade
RUN apk add bash bash-completion build-base git perl mariadb-dev libffi-dev

RUN python3.8 -m venv $VIRTUAL_ENV

RUN echo 'cd /blockstore/app/' >> ~/.bashrc
RUN echo 'export PATH=$VIRTUAL_ENV/bin:$PATH' >> ~/.bashrc
