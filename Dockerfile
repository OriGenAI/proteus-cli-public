# syntax=docker/dockerfile:1

FROM python:3.8-slim-bookworm AS cli_base

# Build required dependencies
ENV BUILD_DEPS="ccache build-essential patchelf jq software-properties-common gnupg curl wget"
ENV RUN_DEPS="cmake mpi-default-bin libc6 libopm-common=2022.10+ds-7 libopm-grid=2022.10+ds-3 libopm-simulators=2022.10+ds-2 libopm-simulators-bin=2022.10+ds-2"

# Install OPM repo
RUN touch /etc/apt/sources.list.d/opm-ubuntu-ppa-focal.list && \
    echo "deb http://ftp.de.debian.org/debian bookworm main" | tee -a /etc/apt/sources.list.d/opm-ubuntu-ppa-focal.list && \
    echo "deb https://ppa.launchpadcontent.net/opm/ppa/ubuntu focal main" | tee -a /etc/apt/sources.list.d/opm-ubuntu-ppa-focal.list && \
    echo "deb-src https://ppa.launchpadcontent.net/opm/ppa/ubuntu focal main" | tee -a /etc/apt/sources.list.d/opm-ubuntu-ppa-focal.list && \
    apt-get update && \
    apt-get install -y gnupg && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys A754739BF0A72DEA5125B57E5426DBEF072EF342 || \
    apt-get install -y dirmngr && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys A754739BF0A72DEA5125B57E5426DBEF072EF342 && \
    mv /etc/apt/trusted.gpg /etc/apt/trusted.gpg.d/ && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y $BUILD_DEPS $RUN_DEPS && \
    apt-get remove -y $BUILD_DEPS && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /var/run/cli

ARG CLI_VERSION

RUN pip --no-cache-dir install --upgrade pip==23.3
RUN pip install --no-cache-dir proteus-cli==$CLI_VERSION
RUN pip install --no-cache origen-ai-ecl==0.2.11

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Azure Developer CLI
RUN curl -fsSL https://aka.ms/install-azd.sh | bash

RUN wget https://aka.ms/downloadazcopy-v10-linux && \
    tar -xvf ./downloadazcopy-v10-linux && \
    cp ./azcopy_linux_amd64_*/azcopy /usr/bin/

ENTRYPOINT ["/usr/local/bin/proteus-do"]

FROM cli_base as cli_development

COPY poetry.lock pyproject.toml ./
RUN apt-get update && apt-get install -y jq

RUN pip install --no-cache-dir poetry && poetry install --no-interaction --no-ansi --no-root --no-cache

ENV AZD_CONFIG_DIR=/azure_config

ARG tenantId
ARG clientId
ARG clientSecret

RUN az login --service-principal --tenant ${tenantId} --username ${clientId} --password ${clientSecret}

CMD ["sh", "-c", "while true; do sleep 1000; done"]
