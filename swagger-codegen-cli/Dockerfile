FROM docker.io/maven:3.6.1-jdk-8 AS builder
WORKDIR /tmp
RUN git clone https://github.com/swagger-api/swagger-codegen.git
WORKDIR /tmp/swagger-codegen
# This is the git sha that we worked off of that we know that works.
# TODO: Should this just be master?
RUN git reset --hard dedb5ce36d54495365da9a7d88d1e6e056cfe29f
COPY model.mustache /tmp/swagger-codegen/modules/swagger-codegen/src/main/resources/go/model.mustache
RUN mvn clean package

FROM openjdk:8-jre-alpine
COPY --from=builder /tmp/swagger-codegen/modules/swagger-codegen-cli/target/swagger-codegen-cli.jar /opt/swagger-codegen-cli/swagger-codegen-cli.jar
ENTRYPOINT ["java", "-jar", "/opt/swagger-codegen-cli/swagger-codegen-cli.jar"]

CMD ["help"]
