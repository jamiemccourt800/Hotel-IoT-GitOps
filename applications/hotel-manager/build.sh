#!/bin/bash
# Build hotel-manager Docker image

set -e

IMAGE_NAME="dkitdevops/hotel-manager"
VERSION="${1:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${VERSION}"

echo "Building hotel manager image: ${FULL_IMAGE}"

# Build the image
docker build -t "${FULL_IMAGE}" .

echo ""
echo "Image built successfully!"
echo ""
echo "To push to registry:"
echo "  docker push ${FULL_IMAGE}"
echo ""
echo "To deploy to Kubernetes:"
echo "  kubectl apply -f deployment.yaml"
echo ""
echo "To test locally:"
echo "  docker run -p 5000:5000 ${FULL_IMAGE}"
