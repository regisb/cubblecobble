# Cubble Cobble

## Usage

    git clone https://github.com/regisb/cubblecobble
    cd cubblecobble
    python -m venv ./.venv
    source .venv/bin/activate
    pip install pyxel
    make play

## Development

Install requirements:

    pip install pyxel

<!-- TODO add requirements to file? -->

Install development requirements:

    pip install mypy pylint black pyinstaller

Bundle to executable file:

    make executable

Note that the generated file will be executable only on the architecture on which it was built.

To point to a specific game server, run:

    GAME_SERVER_HOST=<your IP address> GAME_SERVER_PORT=<server port> make play

## License

This work is licensed under the terms of the [GNU Affero General Public License (AGPL)](./LICENSE.txt).
