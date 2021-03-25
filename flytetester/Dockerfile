FROM ubuntu:focal

WORKDIR /root
ENV VENV /root/venv
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONPATH /root

RUN : \
    && apt-get update \
    && apt install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa

RUN : \
    && apt-get update \
    && apt-get install -y python3.8 python3-pip python3-venv make build-essential libssl-dev curl vim

# This is necessary for opencv to work
RUN apt-get update && apt-get install -y libsm6 libxext6 libxrender-dev ffmpeg

# Install the AWS cli separately to prevent issues with boto being written over
RUN pip3 install awscli

# Virtual environment
RUN python3.8 -m venv ${VENV}
RUN ${VENV}/bin/pip install wheel

# Install Python dependencies
COPY ./requirements.txt /root
RUN ${VENV}/bin/pip install -r /root/requirements.txt

# Copy the actual code
COPY . /root

# Copy over the helper script that the SDK relies on
RUN cp ${VENV}/bin/flytekit_venv /usr/local/bin/flytekit_venv
RUN chmod a+x /usr/local/bin/flytekit_venv

ARG DOCKER_IMAGE

# Environment variables we want to bake into the image
# These are configuration options that can also be specified in a file.  See flytekit.config as an examples

# This tag is supplied by the build script and will be used to determine the version
# when registering tasks, workflows, and launch plans
ENV FLYTE_INTERNAL_IMAGE "$DOCKER_IMAGE"

RUN mkdir /opt/go
WORKDIR /opt/go
RUN curl -s https://raw.githubusercontent.com/flyteorg/flytectl/master/install.sh | bash
WORKDIR /root
ENV PATH="/opt/go/bin:$PATH"