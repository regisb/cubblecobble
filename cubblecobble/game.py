import os
from time import time
import typing as t

import pyxel

import communication
import constants


def run() -> None:
    """
    Run a client instance, which will try to connect to a server.
    """
    game = Game()
    game.run()


class State:
    def __init__(self) -> None:
        self.x: int = constants.LEVEL_SIZE_PIXELS // 2 - constants.PLAYER_SIZE
        self.y: int = constants.LEVEL_SIZE_PIXELS // 2 - constants.PLAYER_SIZE
        self.vx: int = 0
        self.vy: int = 0


class Game:
    TILE_EMPTY = (0, 0)
    TILE_WALL = (1, 0)
    TILE_PLAYER = (0, 1)
    LEVELS_TILEMAP = 0

    def __init__(self) -> None:
        pyxel.init(
            constants.LEVEL_SIZE_PIXELS,
            constants.LEVEL_SIZE_PIXELS,
            title="Cubble Cobble - Briançon Code Club Game Jam Zero 2025",
            fps=constants.FPS,
        )
        self.state = State()

        # Load assets
        pyxel.load(os.path.join(os.path.dirname(__file__), "assets.pyxres"))

        # Communicate with server
        self.client_id = ""
        self.socket = communication.create_client_socket()
        self.send_to_server(communication.COMMAND_CONNECT, {})

    def run(self) -> None:
        pyxel.run(self.update, self.draw)

    def receive_from_server(self) -> None:
        while True:
            message, _address = communication.receive(self.socket)
            if not message:
                return
            command, data = communication.parse_command(message)

            # TODO handle different commands here
            if command == communication.COMMAND_CONNECT:
                client_id = data.get(communication.CLIENT_ID_KEY)
                if not client_id:
                    raise ValueError(
                        f"Received invalid client ID from server: {client_id}"
                    )
                self.client_id = client_id
                print(f"INFO received client ID from server: {self.client_id}")
            elif command == communication.COMMAND_PING:
                start_time = data[communication.TIME_KEY]
                dt = time() - start_time
                print(f"INFO back and forth ping delay: {dt*1000} ms ({1/dt} FPS)")

    def send_to_server(self, command: str, data: dict[str, t.Any]) -> None:
        if self.client_id:
            data[communication.CLIENT_ID_KEY] = self.client_id
        communication.send_command(self.socket, command, data)

    def update(self) -> None:
        # Send a ping, just to check back-and-forth delay
        # if self.client_id:
        #     self.send_to_server(
        #         communication.COMMAND_PING, {communication.TIME_KEY: time()}
        #     )

        # Read server data
        self.receive_from_server()

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
            self.state.vy -= constants.PLAYER_JUMP_SPEED

        # Limit speed
        self.state.vy = min(self.state.vy, constants.PLAYER_MAX_FALL_SPEED)

        # Move
        # (the ... * 1 part is to represent the fact that we count a dt=1 for each frame)
        self.state.x += self.state.vx * 1
        self.state.y += self.state.vy * 1

        # Portal
        self.state.x %= constants.LEVEL_SIZE_PIXELS
        self.state.y %= constants.LEVEL_SIZE_PIXELS

    def draw(self) -> None:
        # Level
        pyxel.bltm(
            0,
            0,
            self.LEVELS_TILEMAP,
            0,
            0,
            constants.LEVEL_SIZE_PIXELS,
            constants.LEVEL_SIZE_PIXELS,
        )

        # Player
        draw_player(self.state.x, self.state.y)
        # Manage overlap
        if self.state.x >= constants.LEVEL_SIZE_PIXELS - constants.PLAYER_SIZE:
            draw_player(self.state.x - constants.LEVEL_SIZE_PIXELS, self.state.y)
        if self.state.y >= constants.LEVEL_SIZE_PIXELS - constants.PLAYER_SIZE:
            draw_player(self.state.x, self.state.y - constants.LEVEL_SIZE_PIXELS)

    # def is_wall(self, x: int, y: int) -> bool:
    #     return pyxel.tilemaps[self.LEVELS_TILEMAP].pget(x, y) == self.TILE_WALL


def draw_player(x: int, y: int) -> None:
    pyxel.rect(
        x,
        y,
        constants.PLAYER_SIZE,
        constants.PLAYER_SIZE,
        constants.WHITE,
    )


def truncate(value: int, bound_min: int, bound_max: int) -> int:
    if value < bound_min:
        return bound_min
    if value > bound_max:
        return bound_max
    return value
