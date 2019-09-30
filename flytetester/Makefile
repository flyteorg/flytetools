PROJECT=flytetester
DOMAIN=development

serialize:
	pyflyte -p ${PROJECT} -d ${DOMAIN} serialize workflows

register:
	pyflyte -p ${PROJECT} -d ${DOMAIN} register workflows

execute:
	pyflyte -p ${PROJECT} -d ${DOMAIN} lp execute app-workflows-work-one-python-task-w-f

.PHONY: end2end
end2end_test:
	flytekit_venv end2end/run.sh
