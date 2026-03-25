# This command build the SAGE image with the tag latest for both amd64 and arm64 architectures and pushes it to my github repo
# For this you need docker and docker-buildx installed, and docker buildx initiated:
# -> docker buildx create --name mybuilder --use
# -> docker buildx inspect --bootstrap
# To be able to build arm64 images on an amd64 platform, check if it can using:
# -> docker buildx ls
# If arm64 is missing in the list, install it using:
# -> docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/sabino-pereira/sage:latest --push .
