export IMAGE_NAME=flytetools
VERSION=$(shell ./version.sh)
PROJECT=flytetester
DOMAIN=development

serialize:
	pyflyte -p ${PROJECT} -d ${DOMAIN} serialize workflows

execute:
	pyflyte -p ${PROJECT} -d ${DOMAIN} lp execute app-workflows-work-one-python-task-w-f

.PHONY: register_staging_in_container
register_staging_in_container:
	pyflyte -p ${PROJECT} -d ${DOMAIN} --config /root/staging.config register workflows


.PHONY: register_staging
register_staging: docker_push
	docker run -e FLYTE_CREDENTIALS_CLIENT_ID=${FLYTE_CREDENTIALS_CLIENT_ID} \
	-e FLYTE_CREDENTIALS_CLIENT_SECRET=${FLYTE_CREDENTIALS_CLIENT_SECRET} \
	-e FLYTE_CREDENTIALS_AUTH_MODE=basic -e FLYTE_CREDENTIALS_AUTHORIZATION_METADATA_KEY=flyte-authorization \
	-e FLYTE_CREDENTIALS_SCOPE=svc -e FLYTE_PLATFORM_AUTH=True \
	ghcr.io/flyteorg/${IMAGE_NAME}:${VERSION} /usr/local/bin/flytekit_venv make register_staging_in_container

.PHONY: register_production_in_container
register_production_in_container:
	pyflyte -p ${PROJECT} -d ${DOMAIN} --config /root/production.config register workflows

.PHONY: register_production
register_production: docker_push
	docker run -e FLYTE_CREDENTIALS_CLIENT_ID=${FLYTE_CREDENTIALS_CLIENT_ID} \
	-e FLYTE_CREDENTIALS_CLIENT_SECRET=${FLYTE_CREDENTIALS_CLIENT_SECRET} \
	-e FLYTE_CREDENTIALS_AUTH_MODE=basic -e FLYTE_CREDENTIALS_AUTHORIZATION_METADATA_KEY=flyte-authorization \
	-e FLYTE_CREDENTIALS_SCOPE=svc -e FLYTE_PLATFORM_AUTH=True \
	ghcr.io/flyteorg/${IMAGE_NAME}:${VERSION} /usr/local/bin/flytekit_venv make register_production_in_container

.PHONY: register_production_in_container
register_sandbox_in_container:
	pyflyte --config /root/sandbox.config register -p ${PROJECT} -d ${DOMAIN} workflows

.PHONY: register_sandbox
register_sandbox: docker_push
	docker run ghcr.io/flyteorg/${IMAGE_NAME}:${VERSION} /usr/local/bin/flytekit_venv make register_sandbox_in_container

.PHONY: end2end
end2end_test:
	flytekit_venv end2end/run.sh

.PHONY: docker_build
docker_build:
	scripts/docker_build.sh

.PHONY: docker_push
docker_push:
	REGISTRY=ghcr.io/flyteorg scripts/docker_build.sh

.PHONY: docker_build_push
docker_build_push: docker_build docker_push
	echo "built"