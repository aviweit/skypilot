DOCKER_IMAGE_OWNER = 'sky'
DOCKER_IMAGE_NAME = 'laptop-base'
DOCKER_IMAGE_TAG = 'latest'

.PHONY: base
all: base laptop

base:
	docker build -t ${DOCKER_IMAGE_OWNER}/${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} -f Dockerfile_laptop.base ..

# TODO: remove hard coded /home..
laptop: base
	docker build -t ${DOCKER_IMAGE_OWNER}/laptop:${DOCKER_IMAGE_TAG} -f Dockerfile_laptop /home/weit
