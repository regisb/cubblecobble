.DEFAULT_GOAL := play

##### Run

play: ## Run game client
	./everybodyjump/main.py

serve: ## Run game server
	./everybodyjump/main.py serve

##### Build/Package

package: ## Bundle game as pyxapp file
	pyxel package ./everybodyjump everybodyjump/main.py

html: package ## Bundle game as html file
	pyxel app2html *.pyxapp

executable: package ## Bundle game as executable file
	pyxel app2exe *.pyxapp

##### Tests

test: test-ruff test-types test-format ## Run all tests

test-types: ## Run mypy
	mypy --ignore-missing-imports --implicit-reexport --strict ./everybodyjump/

# TODO ruff is not catching incorrect arguments passed to function in other modules...
test-ruff: ## Run static checks with ruff
	ruff check ./everybodyjump

test-format: ## Run formatting checks
	black --check ./everybodyjump

format: ## Format code
	black ./everybodyjump

ESCAPE = ^[
help: ## Print this help
	@grep -E '^([a-zA-Z_-]+:.*?## .*|######* .+)$$' Makefile \
			| sed 's/######* \(.*\)/@               $(ESCAPE)[1;31m\1$(ESCAPE)[0m/g' | tr '@' '\n' \
			| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-30s\033[0m %s\n", $$1, $$2}'
