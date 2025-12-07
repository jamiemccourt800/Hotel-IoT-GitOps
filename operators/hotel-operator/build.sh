#!/bin/bash
# Build and push hotel operator image

set -e

IMAGE_NAME="dkitdevops/hotel-operator"
VERSION="${1:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${VERSION}"

echo "Building hotel operator image: ${FULL_IMAGE}"

# Build the image
docker build -t "${FULL_IMAGE}" .

echo "Image built successfully!"
echo ""
echo "To push to registry:"
echo "  docker push ${FULL_IMAGE}"
echo ""
echo "To deploy to Kubernetes:"
echo "  kubectl apply -f deployment.yaml"
echo ""
echo "To test locally:"
echo "  docker run --rm ${FULL_IMAGE}"
