# syntax=docker/dockerfile:1

FROM index.docker.io/python:3.8-bullseye AS cli_base


# Build required dependencies
ENV BUILD_DEPS ccache build-essential patchelf jq software-properties-common
# cmake is a run dep because of libopm libopm-simulators-bin
ENV RUN_DEPS cmake mpi-default-bin libc6 libopm-common=2022.10+ds-7 libopm-grid=2022.10+ds-3 libopm-simulators=2022.10+ds-2 libopm-simulators-bin=2022.10+ds-2

# Install OPM repo.
# PPA repository for OPM 2022.04
# Debian Bookworm (next release) repository for all required dependencies
# Reference: https://github.com/OPM/opm-utilities/blob/7e81cf96d604faaec7cfe9e2ce55fac46be0dfe4/docker_opm_user/Dockerfile
# ---
# for mv /etc/apt/trusted.gpg /etc/apt/trusted.gpg.d/ see https://askubuntu.com/a/1408456
RUN touch /etc/apt/sources.list.d/opm-ubuntu-ppa-focal.list && \
    echo "deb http://ftp.de.debian.org/debian bookworm main" | tee -a /etc/apt/sources.list.d/opm-ubuntu-ppa-focal.list && \
    echo "deb https://ppa.launchpadcontent.net/opm/ppa/ubuntu focal main" | tee -a /etc/apt/sources.list.d/opm-ubuntu-ppa-focal.list && \
    echo "deb-src https://ppa.launchpadcontent.net/opm/ppa/ubuntu focal main" | tee -a /etc/apt/sources.list.d/opm-ubuntu-ppa-focal.list && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys A754739BF0A72DEA5125B57E5426DBEF072EF342 && \
    mv /etc/apt/trusted.gpg /etc/apt/trusted.gpg.d/ && \
    SEQ=2 apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y $BUILD_DEPS $RUN_DEPS && \
    apt-get remove -y $BUILD_DEPS && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /var/run/cli

ARG CLI_VERSION

RUN pip install --no-cache-dir proteus-cli==$CLI_VERSION &&  \
    pip install --no-cache origen-ai-ecl==0.2.11 && \
    pip cache purge

RUN \
    wget https://aka.ms/downloadazcopy-v10-linux && \
    tar -xvf ./downloadazcopy-v10-linux && \
    cp ./azcopy_linux_amd64_*/azcopy /usr/bin/

ENTRYPOINT /usr/local/bin/proteus-do

FROM cli_base as cli_development

COPY poetry.lock pyproject.toml ./

RUN pip install --no-cache-dir poetry && poetry install --no-interaction --no-ansi --no-root --no-cache

ENTRYPOINT []
