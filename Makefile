.PHONY: swagger-codegen-cli
swagger-codegen-cli:
	@docker build -f swagger-codegen-cli/Dockerfile --tag docker.io/lyft/flytetools:swagger-codegen-cli swagger-codegen-cli

