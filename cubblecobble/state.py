import os
import pyxel

import constants


def initialize(
    title: str = "Cubble Cobble - Briançon Code Club Game Jam Zero 2025",
) -> None:
    """
    Initialize pyxel state.

    We do need pyxel on the server because we need to load tilemaps.
    """
    pyxel.init(
        constants.LEVEL_SIZE_PIXELS,
        constants.LEVEL_SIZE_PIXELS,
        title=title,
        fps=constants.FPS,
        # Note that the scaling factor is fucked up https://github.com/kitao/pyxel/issues/591
    )

    # Load assets
    pyxel.load(os.path.join(os.path.dirname(__file__), "assets.pyxres"))


class Commands:
    LEFT = 0
    RIGHT = 1
    JUMP = 2


class State:
    TILE_EMPTY = (0, 0)
    TILE_WALL = (1, 0)
    TILE_PLAYER = (0, 1)
    LEVELS_TILEMAP = 0
    PLAYER_SIZE: int = constants.PLAYER_SIZE

    def __init__(self) -> None:
        self.x: int = constants.LEVEL_SIZE_PIXELS // 2 - self.PLAYER_SIZE
        self.y: int = constants.LEVEL_SIZE_PIXELS // 2 - self.PLAYER_SIZE
        self.vx: int = 0
        self.vy: int = 0

    def as_json(self) -> dict[str, int]:
        """
        TODO is a dict really the best representation? Why not a list?
        """
        return {
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
        }

    def from_json(self, data: dict[str, int]) -> "State":
        self.x = data["x"]
        self.y = data["y"]
        self.vx = data["vx"]
        self.vy = data["vy"]
        return self

    @property
    def x2(self) -> int:
        return self.x + self.PLAYER_SIZE - 1

    @property
    def y2(self) -> int:
        return self.y + self.PLAYER_SIZE - 1

    def update(self, inputs: list[int]) -> None:
        ############# Collect forces
        fx = 0
        fy = 0

        # Move left-right
        if Commands.LEFT in inputs:
            fx -= constants.PLAYER_SPEED
        elif Commands.RIGHT in inputs:
            fx += constants.PLAYER_SPEED
        else:
            # When no input, apply braking force
            fx = -self.vx

        # Fall
        fy += constants.GRAVITY * constants.PLAYER_WEIGHT

        # Jump
        if Commands.JUMP in inputs:
            fy -= constants.PLAYER_JUMP_SPEED

        ############# Compute speeds
        self.vx += fx * 1
        self.vy += fy * 1

        # Limit speed
        self.vy = min(self.vy, constants.PLAYER_MAX_FALL_SPEED)
        self.vx = truncate(self.vx, -constants.PLAYER_SPEED, constants.PLAYER_SPEED)

        ############# Handle collisions
        # Ground
        if self.vy > 0:
            if self.is_wall(self.x, self.y2 + 1) or self.is_wall(self.x2, self.y2 + 1):
                self.vy = 0
        # Ceiling
        if self.vy < 0:
            if self.is_wall(self.x, self.y - 1) or self.is_wall(self.x2, self.y - 1):
                self.vy = 0
        # Walls
        if self.vx < 0:
            if self.is_wall(self.x - 1, self.y) or self.is_wall(self.x - 1, self.y2):
                self.vx = 0
        if self.vx > 0:
            if self.is_wall(self.x2 + 1, self.y) or self.is_wall(self.x2 + 1, self.y2):
                self.vx = 0

        ############# Move
        # (the ... * 1 part is to represent the fact that we count a dt=1 for each frame)
        self.x += self.vx * 1
        self.y += self.vy * 1

        # Get out of walls
        # top wall
        if (self.is_wall(self.x, self.y) and self.is_wall(self.x, self.y - 1)) or (
            self.is_wall(self.x2, self.y)
            and self.is_wall(
                self.x2,
                self.y - 1,
            )
        ):
            self.y = ((self.y // constants.TILE_SIZE) + 1) * constants.TILE_SIZE
        # bottom wall
        if (self.is_wall(self.x, self.y2) and self.is_wall(self.x, self.y2 + 1)) or (
            self.is_wall(self.x2, self.y)
            and self.is_wall(
                self.x2,
                self.y2 + 1,
            )
        ):
            self.y = ((self.y // constants.TILE_SIZE) - 1) * constants.TILE_SIZE

        # Portal
        self.x %= constants.LEVEL_SIZE_PIXELS
        self.y %= constants.LEVEL_SIZE_PIXELS

    def draw_level(self) -> None:
        pyxel.bltm(
            0,
            0,
            self.LEVELS_TILEMAP,
            0,
            0,
            constants.LEVEL_SIZE_PIXELS,
            constants.LEVEL_SIZE_PIXELS,
        )

    def draw_player(self) -> None:
        u, v = self.TILE_PLAYER
        u *= constants.TILE_SIZE
        v *= constants.TILE_SIZE
        pyxel.blt(self.x, self.y, 0, u, v, self.PLAYER_SIZE, self.PLAYER_SIZE)

        # Manage overlap
        if self.x >= constants.LEVEL_SIZE_PIXELS - self.PLAYER_SIZE:
            pyxel.blt(
                self.x - constants.LEVEL_SIZE_PIXELS,
                self.y,
                0,
                u,
                v,
                self.PLAYER_SIZE,
                self.PLAYER_SIZE,
            )
        if self.y >= constants.LEVEL_SIZE_PIXELS - self.PLAYER_SIZE:
            pyxel.blt(
                self.x,
                self.y - constants.LEVEL_SIZE_PIXELS,
                0,
                u,
                v,
                self.PLAYER_SIZE,
                self.PLAYER_SIZE,
            )

    def is_wall(self, x: int, y: int) -> bool:
        """
        Note that we don't need to bother about trimming arguments to the level size,
        this function performs the modulo operation itself.
        """
        x_tile = (x % constants.LEVEL_SIZE_PIXELS) // constants.TILE_SIZE
        y_tile = (y % constants.LEVEL_SIZE_PIXELS) // constants.TILE_SIZE
        # pylint: disable=no-member
        tile_id = pyxel.tilemaps[self.LEVELS_TILEMAP].pget(x_tile, y_tile)
        return tile_id == self.TILE_WALL


def truncate(value: int, bound_min: int, bound_max: int) -> int:
    if value < bound_min:
        return bound_min
    if value > bound_max:
        return bound_max
    return value
