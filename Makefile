.DEFAULT_GOAL := play

##### Edit

assets: ## Edit assets
	pyxel edit ./cubblecobble/assets.pyxres

##### Run

play: ## Run game client
	./cubblecobble/main.py

serve: ## Run game server
	./cubblecobble/main.py serve

##### Build/Package

package: ## Bundle game as pyxapp file
	pyxel package ./cubblecobble cubblecobble/main.py
	mkdir -p build/
	mv cubblecobble.pyxapp build/

html: package ## Bundle game as html file
	pyxel app2html build/cubblecobble.pyxapp

executable: package ## Bundle game as executable file
	pyxel app2exe build/cubblecobble.pyxapp

##### Tests

test: test-lint test-types test-format ## Run all tests

test-types: ## Run mypy
	mypy --ignore-missing-imports --implicit-reexport --strict ./cubblecobble/

test-lint: ## Run static linter checks
	pylint ./cubblecobble

test-format: ## Run formatting checks
	black --check ./cubblecobble

format: ## Format code
	black ./cubblecobble

ESCAPE = ^[
help: ## Print this help
	@grep -E '^([a-zA-Z_-]+:.*?## .*|######* .+)$$' Makefile \
			| sed 's/######* \(.*\)/@               $(ESCAPE)[1;31m\1$(ESCAPE)[0m/g' | tr '@' '\n' \
			| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-30s\033[0m %s\n", $$1, $$2}'
