VERSION=$(shell python -c 'from qotm import qotm; print(qotm.__version__)')

all: docker-image

docker-image: check-registry
	docker build -t $(DOCKER_REGISTRY)/qotm:$(VERSION) .
	docker push $(DOCKER_REGISTRY)/qotm:$(VERSION)

check-registry:
	@if [ -z "$(DOCKER_REGISTRY)" ]; then \
		echo "DOCKER_REGISTRY must be set" >&2; \
		exit 1; \
	fi
