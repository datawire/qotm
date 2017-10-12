VERSION=$(shell python -c 'from qotm import qotm; print(qotm.__version__)')
DOCKER_PREFIX=$(shell if [ $$DOCKER_REGISTRY = "-" ]; then echo ""; else echo "$$DOCKER_REGISTRY/"; fi)

all: docker-image

version:
	@echo $(VERSION)

docker-image: check-version check-registry
	docker build -t $(DOCKER_PREFIX)qotm:$(VERSION) .

	if [ -n "$(DOCKER_PREFIX)" ]; then \
		docker push $(DOCKER_PREFIX)qotm:$(VERSION); \
	fi

check-version:
	@if [ -z "$(VERSION)" ]; then \
		echo "VERSION not available -- maybe you're trying to use Python 2?" >&2; \
		exit 1; \
	fi

check-registry:
	@if [ -z "$(DOCKER_REGISTRY)" ]; then \
		echo "DOCKER_REGISTRY must be set" >&2; \
		exit 1; \
	fi
