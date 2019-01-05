.DEFAULT_GOAL := help

.PHONY: clean help requirements

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo ""
	@echo "These should be run from outside the container:"
	@echo ""
	@echo "  dev.up                    Start Blockstore container"
	@echo "  dev.provision             Provision Blockstore service"
	@echo "  stop                      Stop Blockstore container"
	@echo "  down                      Remove Blockstore container and network. Destructive."
	@echo "  blockstore-shell          Run a shell on Blockstore container."
	@echo ""
	@echo "These should be run from blockstore-shell:"
	@echo ""
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'
	@echo ""

VIRTUAL_ENV?=/blockstore/venv
VENV_BIN=${VIRTUAL_ENV}/bin

dev.up:
	docker-compose --project-name blockstore -f docker-compose.yml up -d

dev.provision:
	docker exec -t edx.devstack.mysql /bin/bash -c 'mysql -uroot <<< "create database if not exists blockstore_db;"'
	docker exec -t edx.devstack.blockstore /bin/bash -c 'source ~/.bashrc && make requirements && make migrate'

stop:
	docker-compose --project-name blockstore -f docker-compose.yml stop

down:
	docker-compose --project-name blockstore -f docker-compose.yml down

blockstore-shell:
	docker exec -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -it edx.devstack.blockstore /bin/bash

clean: ## Remove all generated files
	find . -name '*.pyc' -delete
	${VENV_BIN}/coverage erase
	rm -f diff-cover.html

requirements: ## Install requirements for development
	${VENV_BIN}/pip install -qr requirements/local.txt --exists-action w

requirements-test: ## Install requirements for testing
	${VENV_BIN}/pip install -qr requirements/test.txt --exists-action w

production-requirements:
	pip install -r requirements/production.txt --exists-action w

migrate: ## Apply database migrations
	${VENV_BIN}/python manage.py migrate --no-input

runserver:  ## Run django development server
	${VENV_BIN}/python manage.py runserver 0.0.0.0:18250

static:  ## Collect static files
	${VENV_BIN}/python manage.py collectstatic --noinput

test: clean ## Run tests and generate coverage report
	${VENV_BIN}/coverage run ./manage.py test blockstore tagstore --settings=blockstore.settings.test
	${VENV_BIN}/coverage html
	${VENV_BIN}/coverage xml
	${VENV_BIN}/diff-cover coverage.xml --html-report diff-cover.html

html_coverage: ## Generate HTML coverage report
	${VENV_BIN}/coverage html

quality: ## Run quality checks
	${VENV_BIN}/pycodestyle --config=pycodestyle blockstore tagstore *.py
	${VENV_BIN}/pylint --rcfile=pylintrc blockstore tagstore *.py
	${VENV_BIN}/mypy --config-file tagstore/mypy.ini tagstore

validate: test quality ## Run tests and quality checks
