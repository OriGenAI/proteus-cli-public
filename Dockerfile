ARG BASIS_IMAGE=gcr.io/proteus-beta/proteus-sampling-runner-basis:0.1b0
ARG PROTECTED_PRIVATE_PATH=./private-protected
FROM $BASIS_IMAGE

COPY ./setup.py .
COPY ./project.py .
COPY ./config.py .
COPY ./logging.ini .
COPY command.py .
COPY setup.py .
COPY lifecycle .
COPY api ./api
COPY common ./common
COPY ./private-protected  ./private
RUN echo ${PROTECTED_PRIVATE_PATH}

ARG DEPLOY_ENV=production
ENV DEPLOYMENT=production

ARG CURRENT_IMAGE=gcr.io/proteus-beta/proteus-sampling-runner:0.1b0
ENV CURRENT_IMAGE=$CURRENT_IMAGE

CMD python command.py run
