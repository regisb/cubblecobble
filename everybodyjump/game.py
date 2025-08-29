from time import time

import pyxel

import constants


def run() -> None:
    """
    Run a client instance, which will try to connect to a server.
    """
    game = Game()
    game.run()


class State:
    def __init__(self) -> None:
        self.time = time()
        self.x: float = constants.SCREEN_WIDTH // 2 - constants.PLAYER_SIZE
        self.y: float = constants.SCREEN_HEIGHT // 2 - constants.PLAYER_SIZE
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
        pyxel.init(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        self.state = State()

    def run(self) -> None:
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        dt = self.state.update()

        # Move left-right
        if pyxel.btn(pyxel.KEY_LEFT):
            self.state.vx = -constants.PLAYER_SPEED
        elif pyxel.btn(pyxel.KEY_RIGHT):
            self.state.vx = constants.PLAYER_SPEED
        else:
            self.state.vx = 0

        # Fall
        self.state.vy += constants.GRAVITY * constants.PLAYER_WEIGHT

        # Jump
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.state.vy = -constants.PLAYER_JUMP_SPEED

        # Limit speed
        self.state.vx = truncate(
            self.state.vx, -constants.PLAYER_MAX_SPEED, constants.PLAYER_MAX_SPEED
        )
        self.state.vy = truncate(
            self.state.vy, -constants.PLAYER_MAX_SPEED, constants.PLAYER_MAX_SPEED
        )

        # Move
        self.state.x += self.state.vx * dt
        self.state.x %= constants.SCREEN_WIDTH
        self.state.y += self.state.vy * dt
        self.state.y %= constants.SCREEN_HEIGHT

    def draw(self) -> None:
        pyxel.cls(constants.BLACK)
        draw_player(self.state.x, self.state.y)
        # Manage overlap
        if self.state.x >= constants.SCREEN_WIDTH - constants.PLAYER_SIZE:
            draw_player(self.state.x - constants.SCREEN_WIDTH, self.state.y)
        if self.state.y >= constants.SCREEN_HEIGHT - constants.PLAYER_SIZE:
            draw_player(self.state.x, self.state.y - constants.SCREEN_HEIGHT)


def draw_player(x: float, y: float) -> None:
    pyxel.rect(
        x,
        y,
        constants.PLAYER_SIZE,
        constants.PLAYER_SIZE,
        constants.WHITE,
    )


def truncate(value: float, bound_min: float, bound_max: float) -> float:
    if value < bound_min:
        return bound_min
    if value > bound_max:
        return bound_max
    return value
