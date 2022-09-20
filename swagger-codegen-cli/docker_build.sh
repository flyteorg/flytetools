set -e

echo ""
echo "------------------------------------"
echo "          DOCKER BUILD"
echo "------------------------------------"
echo ""

GIT_SHA=$(git rev-parse HEAD)
RELEASE_SEMVER=$(git describe --tags --exact-match "$GIT_SHA" 2>/dev/null) || true

TAGS="$IMAGE_NAME:latest"
PUSH_ARG=""

if [ -n "$REGISTRY" ]; then
  # Do not push if there are unstaged git changes
  CHANGED=$(git status --porcelain)
  if [ -n "$CHANGED" ]; then
    echo "Please commit git changes before pushing to a registry"
    exit 1
  fi

  if [ -n "${DOCKER_REGISTRY_PASSWORD}" ]; then
    docker login --username="$DOCKER_REGISTRY_USERNAME" --password="$DOCKER_REGISTRY_PASSWORD"
  fi

  SHA_IMAGE_TAG="${REGISTRY}/${IMAGE_NAME}:${GIT_SHA}"
  TAGS="$TAGS,$SHA_IMAGE_TAG"
  PUSH_ARG="--push"

  if [ -n "$RELEASE_SEMVER" ]; then
    SEMVER_IMAGE_TAG="${REGISTRY}/${IMAGE_NAME}:${RELEASE_SEMVER}"
    TAGS="$TAGS,$SEMVER_IMAGE_TAG"
  fi
fi

docker buildx create --name swagger-codegen-cli-builder --driver docker-container --bootstrap --use
docker buildx build --platform=linux/amd64,linux/arm64 -t $TAGS $PUSH_ARG .
docker buildx rm swagger-codegen-cli-builder

echo "Built images"
if [ -n "$PUSH_ARG" ]; then
  echo "Pushed images to repository '${REGISTRY}' with tags '$TAGS'"
fi
