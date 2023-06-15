# syntax=docker/dockerfile:1
FROM origenproteusregistry.azurecr.io/origen.ai/opm_base:2947843500ff46696704988ef19191d331e1a219 as cli_base

WORKDIR /var/run/cli

ARG CLI_VERSION

RUN pip install --no-cache-dir proteus-cli==$CLI_VERSION &&  \
    pip install --no-cache origen-ai-ecl==0.2.11 && \
    pip cache purge

ENTRYPOINT /usr/local/bin/proteus-do

FROM cli_base as cli_development

COPY poetry.lock pyproject.toml ./

RUN pip install --no-cache-dir poetry && poetry install --no-interaction --no-ansi --no-root --no-cache

ENTRYPOINT []
