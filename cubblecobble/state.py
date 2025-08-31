import hashlib
import os
import typing as t

import pyxel

import constants

LEVELS_TILEMAP = 0
PLAYER_SIZE: int = constants.PLAYER_SIZE
TILE_EMPTY = (0, 0)
TILE_PLAYER = (0, 1)
TILE_WALL = (1, 0)


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


class Position:

    def __init__(self) -> None:
        self.x: int = constants.LEVEL_SIZE_PIXELS // 2 - PLAYER_SIZE
        self.y: int = constants.LEVEL_SIZE_PIXELS // 2 - PLAYER_SIZE
        self.vx: int = 0
        self.vy: int = 0

    @property
    def x2(self) -> int:
        return self.x + PLAYER_SIZE - 1

    @property
    def y2(self) -> int:
        return self.y + PLAYER_SIZE - 1

    def to_json(self) -> list[int]:
        return [self.x, self.y, self.vx, self.vy]

    def from_json(self, data: list[int]) -> "Position":
        self.x, self.y, self.vx, self.vy = data
        return self

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
        is_on_ground = False
        if self.is_wall(self.x, self.y2 + 1) or self.is_wall(self.x2, self.y2 + 1):
            is_on_ground = True
        if Commands.JUMP in inputs and is_on_ground:
            fy -= constants.PLAYER_JUMP_SPEED

        ############# Compute speeds
        self.vx += fx * 1
        self.vy += fy * 1

        # Limit speed
        self.vy = truncate(
            self.vy, -constants.PLAYER_JUMP_SPEED, constants.PLAYER_MAX_FALL_SPEED
        )
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
        # side walls
        if (self.is_wall(self.x, self.y) and self.is_wall(self.x - 1, self.y)) or (
            self.is_wall(self.x, self.y2) and self.is_wall(self.x - 1, self.y2)
        ):
            self.x = ((self.x // constants.TILE_SIZE) + 1) * constants.TILE_SIZE
        if (self.is_wall(self.x2, self.y) and self.is_wall(self.x2 - 1, self.y)) or (
            self.is_wall(self.x2, self.y2) and self.is_wall(self.x2 - 1, self.y2)
        ):
            self.x = ((self.x // constants.TILE_SIZE) - 1) * constants.TILE_SIZE

        # Portal
        self.x %= constants.LEVEL_SIZE_PIXELS
        self.y %= constants.LEVEL_SIZE_PIXELS

    def is_wall(self, x: int, y: int) -> bool:
        """
        Note that we don't need to bother about trimming arguments to the level size,
        this function performs the modulo operation itself.
        """
        x_tile = (x % constants.LEVEL_SIZE_PIXELS) // constants.TILE_SIZE
        y_tile = (y % constants.LEVEL_SIZE_PIXELS) // constants.TILE_SIZE
        # pylint: disable=no-member
        tile_id = pyxel.tilemaps[LEVELS_TILEMAP].pget(x_tile, y_tile)
        return tile_id == TILE_WALL

    def draw(self) -> None:
        u, v = TILE_PLAYER
        u *= constants.TILE_SIZE
        v *= constants.TILE_SIZE
        pyxel.blt(self.x, self.y, 0, u, v, PLAYER_SIZE, PLAYER_SIZE)

        # Manage overlap
        if self.x >= constants.LEVEL_SIZE_PIXELS - PLAYER_SIZE:
            pyxel.blt(
                self.x - constants.LEVEL_SIZE_PIXELS,
                self.y,
                0,
                u,
                v,
                PLAYER_SIZE,
                PLAYER_SIZE,
            )
        if self.y >= constants.LEVEL_SIZE_PIXELS - PLAYER_SIZE:
            pyxel.blt(
                self.x,
                self.y - constants.LEVEL_SIZE_PIXELS,
                0,
                u,
                v,
                PLAYER_SIZE,
                PLAYER_SIZE,
            )


class State:

    def __init__(self) -> None:
        self.client_ids: list[str] = []  # note that the client IDs are hashed
        self.inputs: list[list[int]] = []
        self.positions: list[Position] = []

    def to_json(self) -> dict[str, t.Any]:
        return {
            "client_ids": self.client_ids,
            "inputs": self.inputs,
            "positions": [position.to_json() for position in self.positions],
        }

    def from_json(self, data: dict[str, t.Any]) -> "State":
        self.client_ids = data["client_ids"]
        self.inputs = data["inputs"]
        self.positions = [
            Position().from_json(position) for position in data["positions"]
        ]
        return self

    def add_client(self, client_id: str) -> None:
        encoded: str = encode(client_id)
        if encoded in self.client_ids:
            print(f"ERROR player already exists: {client_id}")
            return
        self.client_ids.append(encoded)
        self.inputs.append([])
        self.positions.append(Position())

    def remove_client(self, client_id: str) -> None:
        client_index = self.get_client_index(client_id)
        self.client_ids.pop(client_index)
        self.inputs.pop(client_index)
        self.positions.pop(client_index)

    def draw(self) -> None:
        # Level
        pyxel.bltm(
            0,
            0,
            LEVELS_TILEMAP,
            0,
            0,
            constants.LEVEL_SIZE_PIXELS,
            constants.LEVEL_SIZE_PIXELS,
        )

        # TODO highlight current player
        for position in self.positions:
            position.draw()

    def set_inputs(self, client_id: str, inputs: list[int]) -> None:
        """
        Assign inputs to a player. If the player does not exist, create it.
        """
        client_index = self.get_client_index(client_id)
        self.inputs[client_index] = inputs

    def get_client_index(self, client_id: str) -> int:
        """
        Return -1 if the client was not found
        """
        encoded = encode(client_id)
        for client_index, client_encoded in enumerate(self.client_ids):
            if encoded == client_encoded:
                return client_index
        raise ValueError(f"Client not found: {client_id}. Did you call add_client?")

    def update(self) -> None:
        # Apply some speed to handle player collisions
        bump_speed = 20
        for i, pos1 in enumerate(self.positions):
            for pos2 in self.positions[i + 1 :]:
                # Top
                if (pos2.x <= pos1.x < pos2.x2 and pos2.y <= pos1.y < pos2.y2) or (
                    pos2.x <= pos1.x2 - 1 < pos2.x2 and pos2.y <= pos1.y < pos2.y2
                ):
                    pos1.vy += bump_speed
                    pos2.vy -= bump_speed
                # Bottom
                if (pos2.x <= pos1.x2 < pos2.x2 and pos2.y <= pos1.y2 < pos2.y2) or (
                    pos2.x <= pos1.x2 - 1 < pos2.x2 and pos2.y <= pos1.y2 < pos2.y2
                ):
                    pos1.vy -= bump_speed
                    pos2.vy += bump_speed
                # Side
                if (pos2.y <= pos1.y < pos2.y2 and pos2.x <= pos1.x < pos2.x2) or (
                    pos2.y <= pos1.y2 - 1 < pos2.y2 and pos2.x <= pos1.x < pos2.x2
                ):
                    pos1.vx += bump_speed
                    pos2.vx -= bump_speed
                if (pos2.y <= pos1.y2 < pos2.y2 and pos2.x <= pos1.x2 < pos2.x2) or (
                    pos2.y <= pos1.y2 - 1 < pos2.y2 and pos2.x <= pos1.x2 < pos2.x2
                ):
                    pos1.vx -= bump_speed
                    pos2.vx += bump_speed

        # Manage each player individually
        for position, inputs in zip(self.positions, self.inputs):
            position.update(inputs)
        # Clear inputs
        self.inputs = [[] for _ in range(len(self.client_ids))]


def encode(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def truncate(value: int, bound_min: int, bound_max: int) -> int:
    if value < bound_min:
        return bound_min
    if value > bound_max:
        return bound_max
    return value
