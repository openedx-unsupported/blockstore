.DEFAULT_GOAL := help

.PHONY: clean help requirements

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo ""
	@echo "These should be run from outside the container:"
	@echo ""
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*? # .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.* # "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "These should be run from blockstore-shell:"
	@echo ""
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.* ## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'
	@echo ""

VIRTUAL_ENV?=/blockstore/venv
PYTHON_VERSION=3.8
VENV_BIN=${VIRTUAL_ENV}/bin

# Blockstore Docker configuration
BLOCKSTORE_PROJECT_NAME?=blockstore${PYTHON_VERSION}
BLOCKSTORE_DOCKER_COMPOSE_OPTS=-p ${BLOCKSTORE_PROJECT_NAME} -f docker-compose-${PYTHON_VERSION}.yml

# Blockstore test server Docker configuration
BLOCKSTORE_TESTSERVER_PROJECT_NAME?=blockstore-testserver${PYTHON_VERSION}
BLOCKSTORE_TESTSERVER_DOCKER_COMPOSE_OPTS=-p ${BLOCKSTORE_TESTSERVER_PROJECT_NAME} -f docker-compose-testserver-${PYTHON_VERSION}.yml

# Open edX Docker configuration
OPENEDX_PROJECT_NAME?=devstack

dev.build:  # Build Blockstore container
	docker-compose ${BLOCKSTORE_DOCKER_COMPOSE_OPTS} build --no-cache

dev.up:  # Start Blockstore container
	docker-compose ${BLOCKSTORE_DOCKER_COMPOSE_OPTS} up -d

dev.provision:  # Provision Blockstore service
	docker exec -t edx.${OPENEDX_PROJECT_NAME}.mysql57 /bin/bash -c 'mysql -uroot <<< "create database if not exists blockstore_db;"'
	docker-compose ${BLOCKSTORE_DOCKER_COMPOSE_OPTS} exec blockstore /bin/bash -c 'source ~/.bashrc && make requirements && make migrate'

dev.run: dev.up  # Run the service in the foreground
	docker-compose ${BLOCKSTORE_DOCKER_COMPOSE_OPTS} exec blockstore /blockstore/venv/bin/python /blockstore/app/manage.py runserver 0.0.0.0:18250

dev.run-detached: dev.up  # Run the service in the background
	docker-compose ${BLOCKSTORE_DOCKER_COMPOSE_OPTS} exec -d blockstore /blockstore/venv/bin/python /blockstore/app/manage.py runserver 0.0.0.0:18250

stop:  # Stop Blockstore container
	docker-compose ${BLOCKSTORE_DOCKER_COMPOSE_OPTS} stop

pull:  # Update docker images that this depends on.
	docker pull ubuntu:20.04

destroy:  # Remove Blockstore container, network and volumes. Destructive.
	docker-compose ${BLOCKSTORE_DOCKER_COMPOSE_OPTS} down -v

blockstore-shell:  # Open a shell on the running Blockstore container
	docker-compose ${BLOCKSTORE_DOCKER_COMPOSE_OPTS} exec -e COLUMNS="`tput cols`" -e LINES="`tput lines`" blockstore /bin/bash

clean: ## Remove all generated files
	find . -name '*.pyc' -delete
	${VENV_BIN}/coverage erase
	rm -f diff-cover.html

requirements: ## Install requirements for development
	# We can't add this to requirements. It changes the way pip itself works.
	${VENV_BIN}/pip install -U pip wheel
	${VENV_BIN}/pip install -r requirements/local.txt --exists-action w

requirements-test: ## Install requirements for testing
	${VENV_BIN}/pip install -U pip wheel
	${VENV_BIN}/pip install -r requirements/test.txt --exists-action w

production-requirements:
	${VENV_BIN}/pip install -U pip wheel
	${VENV_BIN}/pip install -r requirements/production.txt --exists-action w

migrate: ## Apply database migrations
	${VENV_BIN}/python manage.py migrate --no-input

runserver:  ## Run django development server
	${VENV_BIN}/python manage.py runserver 0.0.0.0:18250

static:  ## Collect static files
	${VENV_BIN}/python manage.py collectstatic --noinput

test: clean ## Run tests and generate coverage report
	${VENV_BIN}/coverage run ./manage.py test blockstore --settings=blockstore.settings.test
	${VENV_BIN}/coverage html
	${VENV_BIN}/coverage xml
	${VENV_BIN}/diff-cover coverage.xml --html-report diff-cover.html --compare-branch origin/master

easyserver: dev.up dev.provision  # Start and provision a Blockstore container and run the server until CTRL-C, then stop it
	# Now run blockstore until the user hits CTRL-C:
	docker-compose ${BLOCKSTORE_DOCKER_COMPOSE_OPTS} exec blockstore /blockstore/venv/bin/python /blockstore/app/manage.py runserver 0.0.0.0:18250
	# Then stop the container:
	docker-compose ${BLOCKSTORE_DOCKER_COMPOSE_OPTS} stop

testserver:  # Run an isolated ephemeral instance of Blockstore for use by edx-platform tests
	docker-compose ${BLOCKSTORE_TESTSERVER_DOCKER_COMPOSE_OPTS} up -d
	docker exec -t edx.${OPENEDX_PROJECT_NAME}.mysql57 /bin/bash -c 'mysql -uroot <<< "create database if not exists blockstore_test_db;"'
	docker-compose ${BLOCKSTORE_TESTSERVER_DOCKER_COMPOSE_OPTS} exec blockstore /bin/bash -c 'source ~/.bashrc && make requirements && make migrate && ./manage.py shell < provision-testserver-data.py'
	# Now run blockstore until the user hits CTRL-C:
	docker-compose ${BLOCKSTORE_TESTSERVER_DOCKER_COMPOSE_OPTS} exec blockstore /blockstore/venv/bin/python /blockstore/app/manage.py runserver 0.0.0.0:18251
	# And destroy everything except the virtualenv volume (which we want to reuse to save time):
	docker-compose ${BLOCKSTORE_TESTSERVER_DOCKER_COMPOSE_OPTS} down
	docker exec -t edx.${OPENEDX_PROJECT_NAME}.mysql57 /bin/bash -c 'mysql -uroot <<< "drop database blockstore_test_db;"'

html_coverage: ## Generate HTML coverage report
	${VENV_BIN}/coverage html

quality: ## Run quality checks
	${VENV_BIN}/pycodestyle --config=pycodestyle blockstore *.py
	${VENV_BIN}/pylint --django-settings-module=blockstore.settings.test --rcfile=pylintrc blockstore *.py

validate: test quality ## Run tests and quality checks

docker_build:
	docker build . -f Dockerfile-${PYTHON_VERSION} -t openedx/blockstore
	docker build . -f Dockerfile-${PYTHON_VERSION} -t openedx/blockstore:latest-newrelic

docker_tag: docker_build
	docker tag openedx/blockstore openedx/blockstore:${GITHUB_SHA}
	docker tag openedx/blockstore:latest-newrelic openedx/blockstore:${GITHUB_SHA}-newrelic

docker_auth:
	echo "$$DOCKERHUB_PASSWORD" | docker login -u "$$DOCKERHUB_USERNAME" --password-stdin

docker_push: docker_tag docker_auth ## push to docker hub
	docker push 'openedx/blockstore:latest'
	docker push "openedx/blockstore:${GITHUB_SHA}"
	docker push 'openedx/blockstore:latest-newrelic'
	docker push "openedx/blockstore:${GITHUB_SHA}-newrelic"

COMMON_CONSTRAINTS_TXT=requirements/common_constraints.txt
.PHONY: $(COMMON_CONSTRAINTS_TXT)
$(COMMON_CONSTRAINTS_TXT):
	wget -O "$(@)" https://raw.githubusercontent.com/edx/edx-lint/master/edx_lint/files/common_constraints.txt || touch "$(@)"

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: $(COMMON_CONSTRAINTS_TXT)	## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	sed 's/Django<2.3//g' requirements/common_constraints.txt > requirements/common_constraints.tmp
	mv requirements/common_constraints.tmp requirements/common_constraints.txt
	sed 's/pyjwt\[crypto\]<2.0.0//g' requirements/common_constraints.txt > requirements/common_constraints.tmp
	mv requirements/common_constraints.tmp requirements/common_constraints.txt
	sed 's/social-auth-core<4.0.3//g' requirements/common_constraints.txt > requirements/common_constraints.tmp
	mv requirements/common_constraints.tmp requirements/common_constraints.txt
	sed 's/edx-auth-backends<4.0.0//g' requirements/common_constraints.txt > requirements/common_constraints.tmp
	mv requirements/common_constraints.tmp requirements/common_constraints.txt
	pip install -q -r requirements/pip-tools.txt
	pip-compile --upgrade -o requirements/pip-tools.txt requirements/pip-tools.in
	pip-compile --upgrade -o requirements/base.txt requirements/base.in
	pip-compile --upgrade -o requirements/docs.txt requirements/docs.in
	pip-compile --upgrade -o requirements/test.txt requirements/test.in
	pip-compile --upgrade -o requirements/production.txt requirements/production.in
	pip-compile --upgrade -o requirements/local.txt requirements/local.in
