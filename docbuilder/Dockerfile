FROM ubuntu:bionic
RUN apt-get update \
  && apt-get install -y \
       python-virtualenv \
       python3-pip \
       python3-dev \
  && apt-get autoremove \
  && apt-get clean

ENV VENV /venv

RUN virtualenv -p python3.6 ${VENV} \
    && ${VENV}/bin/pip install Sphinx \
    && ${VENV}/bin/pip install sphinx_rtd_theme

# virtual env entrypoint
COPY entrypoint.sh /opt

# activate it by default
ENTRYPOINT ["/opt/entrypoint.sh"]
