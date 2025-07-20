IMAGE=pdf1a:dev
PROJECT_ROOT:=$(shell pwd)

build:
	docker build --platform=linux/amd64 -t $(IMAGE) .

run:
	mkdir -p input output
	docker run --rm -v "$(PROJECT_ROOT)/input:/app/input" -v "$(PROJECT_ROOT)/output:/app/output" --network none $(IMAGE)

shell:
	docker run --rm -it -v "$(PROJECT_ROOT)/input:/app/input" -v "$(PROJECT_ROOT)/output:/app/output" --network none $(IMAGE) /bin/bash
