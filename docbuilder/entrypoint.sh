#!/bin/bash

set -e

# activate the virtual environment
. ${VENV}/bin/activate

exec $*
