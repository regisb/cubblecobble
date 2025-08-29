.DEFAULT_GOAL := run

##### Run

run:
	./game.py

##### Tests

test: test-ruff test-types test-format ## Run all tests

test-types: ## Run mypy
	mypy --ignore-missing-imports --implicit-reexport --strict ./game.py

test-ruff: ## Run static checks with ruff
	ruff check ./game.py

test-format: ## Run formatting checks
	black --check ./game.py

format: ## Format code
	black ./game.py

ESCAPE = ^[
help: ## Print this help
	@grep -E '^([a-zA-Z_-]+:.*?## .*|######* .+)$$' Makefile \
			| sed 's/######* \(.*\)/@               $(ESCAPE)[1;31m\1$(ESCAPE)[0m/g' | tr '@' '\n' \
			| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-30s\033[0m %s\n", $$1, $$2}'
