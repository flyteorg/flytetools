export IMAGE_NAME=flytetester
VERSION=$(shell ./version.sh)
PROJECT=flytetester
DOMAIN=development

serialize:
	pyflyte -p ${PROJECT} -d ${DOMAIN} serialize workflows

register_staging:
	pyflyte -p ${PROJECT} -d ${DOMAIN} -c staging.config register workflows

execute:
	pyflyte -p ${PROJECT} -d ${DOMAIN} lp execute app-workflows-work-one-python-task-w-f

.PHONY: register_staging_in_container
register_staging_in_container:
	pyflyte -p ${PROJECT} -d ${DOMAIN} --config /app/staging.config register workflows


.PHONY: register_staging
register_staging: docker_push
	docker run docker.io/lyft/${IMAGE_NAME}:${VERSION} /opt/flytekit_venv make register_staging_in_container


.PHONY: register_production_in_container
register_production_in_container:
	pyflyte -p ${PROJECT} -d ${DOMAIN} --config /app/production.config register workflows


.PHONY: register_production
register_production: docker_push
	docker run docker.io/lyft/${IMAGE_NAME}:${VERSION} /opt/flytekit_venv make register_production_in_container

.PHONY: end2end
end2end_test:
	flytekit_venv end2end/run.sh

.PHONY: docker_build
docker_build:
	scripts/docker_build.sh

.PHONY: docker_push
docker_push:
	REGISTRY=docker.io/lyft scripts/docker_build.sh

.PHONY: docker_build_push
docker_build_push:
	docker_build
	docker_push
