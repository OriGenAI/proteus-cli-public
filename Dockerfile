# This is a simple Dockerfile to use while developing
# It's not suitable for production
#
# It allows you to run both flask and celery if you enabled it
# for flask: docker run --env-file=.flaskenv image flask run
# for celery: docker run --env-file=.flaskenv image celery worker -A proteus.celery_app:app
#
# note that celery will require a running broker and result backend
FROM python:3.8-slim-buster

RUN mkdir /cli
WORKDIR /cli

COPY api/ api/
COPY cli/ cli/
COPY setup.py project.py ./
COPY requirements/ requirements/

RUN pip install -U pip
RUN pip install -e .

ARG DEPLOY_ENV=production
ENV DEPLOYMENT=$DEPLOY_ENV
ENV PYTHON_PATH=.

ENTRYPOINT ["sleep 3600"]
