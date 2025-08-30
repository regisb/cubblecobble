import os

import pyxel

import constants
from state import State


def run() -> None:
    """
    Run a client instance, which will try to connect to a server.
    """
    game = Game()
    game.run()


class Game:
    def __init__(self) -> None:
        pyxel.init(
            constants.LEVEL_SIZE_PIXELS,
            constants.LEVEL_SIZE_PIXELS,
            title="Cubble Cobble - Briançon Code Club Game Jam Zero 2025",
            fps=constants.FPS,
            # Note that the scaling factor is fucked up https://github.com/kitao/pyxel/issues/591
        )

        # Load assets
        pyxel.load(os.path.join(os.path.dirname(__file__), "assets.pyxres"))

        # Initialize state
        self.state = State()

    def run(self) -> None:
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        # Handle restart command here
        if pyxel.btnp(pyxel.KEY_R):
            # Restart
            self.state = State()

        self.state.update()

    def draw(self) -> None:
        self.state.draw()
