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
        self.time = time()
        self.x: float = constants.LEVEL_SIZE_PIXELS // 2 - constants.PLAYER_SIZE
        self.y: float = constants.LEVEL_SIZE_PIXELS // 2 - constants.PLAYER_SIZE
        self.vx: float = 0
        self.vy: float = 0

    def update(self) -> float:
        now = time()
        dt = now - self.time
        # TODO move this to a different method?
        self.time = now
        return dt


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
            fps=30,
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
        # TODO IMPORTANT stop bothering about time. Instead, count everything in frames,
        # because pyxel maintains a constant framerate.
        dt = self.state.update()

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
        self.state.x %= constants.LEVEL_SIZE_PIXELS
        self.state.y += self.state.vy * dt
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
