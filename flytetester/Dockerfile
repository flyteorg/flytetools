FROM ubuntu:bionic

WORKDIR /root
ENV VENV /root/venv
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONPATH /root

RUN : \
    && apt-get update && apt-get install -y python3.6 python3.6-venv python3.6-dev make build-essential libssl-dev python3-venv python3-pip curl

# This is necessary for opencv to work
RUN apt-get update && apt-get install -y libsm6 libxext6 libxrender-dev

# Install the AWS cli separately to prevent issues with boto being written over
RUN pip3 install awscli

# Virtual environment
RUN python3.6 -m venv ${VENV}
RUN ${VENV}/bin/pip install wheel

# Install Python dependencies
# TODO: Remove the pin of pip. In July-Aug 2019, it seemed like the latest version of pip had issues pulling from private
#       Python repositories. Pinning to an older version until the issue can be investigated (even though this image
#       doesn't depend on private repositories).
RUN ${VENV}/bin/pip install pip==19.0.3
COPY ./requirements.txt /root
RUN ${VENV}/bin/pip install -r /root/requirements.txt

# Copy the actual code
COPY . /root

# Copy over the helper script that the SDK relies on
RUN cp ${VENV}/bin/flytekit_venv /usr/local/bin/flytekit_venv
RUN chmod a+x /usr/local/bin/flytekit_venv

ARG tag

# Environment variables we want to bake into the image
# These are configuration options that can also be specified in a file.  See flytekit.config as an examples

# This tag is supplied by the build script and will be used to determine the version
# when registering tasks, workflows, and launch plans
ENV FLYTE_INTERNAL_IMAGE $tag
