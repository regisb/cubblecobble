#! /usr/bin/env python
# /// script
# dependencies = [
#   "pyxel",
# ]
# ///
from time import time

import pyxel


def main() -> None:
    game = Game()
    game.run()


class Constants:
    # Screen
    SCREEN_WIDTH = 200
    SCREEN_HEIGHT = 200

    # Global properties
    GRAVITY = 9.81

    # Player properties
    PLAYER_SIZE = 10
    PLAYER_SPEED = 80
    PLAYER_WEIGHT = 5
    PLAYER_MAX_SPEED = 150
    PLAYER_JUMP_SPEED = 300

    # Colors
    BLACK = 0
    WHITE = 7


class State:
    def __init__(self) -> None:
        self.time = time()
        self.x: float = Constants.SCREEN_WIDTH // 2 - Constants.PLAYER_SIZE
        self.y: float = Constants.SCREEN_HEIGHT // 2 - Constants.PLAYER_SIZE
        self.vx: float = 0
        self.vy: float = 0

    def update(self) -> float:
        now = time()
        dt = now - self.time
        # TODO move this to a different method?
        self.time = now
        return dt


class Game:

    def __init__(self) -> None:
        pyxel.init(Constants.SCREEN_WIDTH, Constants.SCREEN_HEIGHT)
        self.state = State()

    def run(self) -> None:
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        dt = self.state.update()

        # Move left-right
        if pyxel.btn(pyxel.KEY_LEFT):
            self.state.vx = -Constants.PLAYER_SPEED
        elif pyxel.btn(pyxel.KEY_RIGHT):
            self.state.vx = Constants.PLAYER_SPEED
        else:
            self.state.vx = 0

        # Fall
        self.state.vy += Constants.GRAVITY * Constants.PLAYER_WEIGHT

        # Jump
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.state.vy = -Constants.PLAYER_JUMP_SPEED

        # Limit speed
        self.state.vx = truncate(self.state.vx, -Constants.PLAYER_MAX_SPEED, Constants.PLAYER_MAX_SPEED)
        self.state.vy = truncate(self.state.vy, -Constants.PLAYER_MAX_SPEED, Constants.PLAYER_MAX_SPEED)

        # Move
        self.state.x += self.state.vx * dt
        self.state.x %= Constants.SCREEN_WIDTH
        self.state.y += self.state.vy * dt
        self.state.y %= Constants.SCREEN_HEIGHT

    def draw(self) -> None:
        pyxel.cls(Constants.BLACK)
        draw_player(self.state.x, self.state.y)
        # Manage overlap
        if self.state.x >= Constants.SCREEN_WIDTH - Constants.PLAYER_SIZE:
            draw_player(self.state.x - Constants.SCREEN_WIDTH, self.state.y)
        if self.state.y >= Constants.SCREEN_HEIGHT - Constants.PLAYER_SIZE:
            draw_player(self.state.x, self.state.y - Constants.SCREEN_HEIGHT)


def draw_player(x: float, y: float) -> None:
    pyxel.rect(
        x,
        y,
        Constants.PLAYER_SIZE,
        Constants.PLAYER_SIZE,
        Constants.WHITE,
    )

def truncate(value: float, bound_min: float, bound_max: float) -> float:
    if value < bound_min:
        return bound_min
    if value > bound_max:
        return bound_max
    return value


if __name__ == "__main__":
    main()
