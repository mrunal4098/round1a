IMAGE=pdf1a:dev
PROJECT_ROOT := $(PWD)

build:
	docker build --platform=linux/amd64 -t $(IMAGE) .

run:
	mkdir -p input output
	MSYS_NO_PATHCONV=1 docker run --rm -v "$(PROJECT_ROOT)/input:/app/input" -v "$(PROJECT_ROOT)/output:/app/output" --network none $(IMAGE)

shell:
	MSYS_NO_PATHCONV=1 docker run --rm -it -v "$(PROJECT_ROOT)/input:/app/input" -v "$(PROJECT_ROOT)/output:/app/output" --network none $(IMAGE) /bin/bash

perf:
	MSYS_NO_PATHCONV=1 docker run --rm \
		-v "$(PWD)/input:/app/input" \
		-v "$(PWD)/output:/app/output" \
		--network none --entrypoint python $(IMAGE) -m app.perf


run_debug:
	MSYS_NO_PATHCONV=1 DEBUG=1 docker run --rm \
		-v "$(PWD)/input:/app/input" \
		-v "$(PWD)/output:/app/output" \
		--network none $(IMAGE)

validate:
	@for f in output/*.json ; do \
	  [ -f "$$f" ] || continue ; \
	  echo ">> Validating $$f"; \
	  MSYS_NO_PATHCONV=1 docker run --rm \
	    -v "$(PWD)/output:/app/output" \
	    --network none --entrypoint python $(IMAGE) -m app.validate_output /app/output/$$(basename $$f) || exit 1; \
	done

eval:
	MSYS_NO_PATHCONV=1 docker run --rm \
		-v "$(PWD)/ground_truth:/app/ground_truth" \
		-v "$(PWD)/output:/app/output" \
		--network none --entrypoint python $(IMAGE) -m app.eval /app/ground_truth /app/output

