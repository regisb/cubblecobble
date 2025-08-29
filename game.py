#! /usr/bin/env python
# /// script
# dependencies = [
#   "pyxel",
# ]
# ///
# title: Everybody Loves To Jump
# author: Régis Behmo
# desc: My Briançon Game Jam 2025 "multiplayer" entry
# site: https://github.com/regisb/everybodylovestojump
# license: AGPL v3.0
# version: 1.0
import json
import socket
import sys
from time import time
import typing as t
import uuid

import pyxel




def main() -> None:
    if len(sys.argv) == 1 or sys.argv[1] == "play":
        run_client()
    elif sys.argv[1] == "serve":
        run_server()


def run_client() -> None:
    """
    Run a client instance, which will try to connect to a server.
    """
    game = Game()
    game.run()


def run_server() -> None:
    """
    Run a server instance, to which clients will connect.
    """
    server = Server()
    server.run()


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
        self.state.vx = truncate(
            self.state.vx, -Constants.PLAYER_MAX_SPEED, Constants.PLAYER_MAX_SPEED
        )
        self.state.vy = truncate(
            self.state.vy, -Constants.PLAYER_MAX_SPEED, Constants.PLAYER_MAX_SPEED
        )

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


class Server:
    """
    Create a UDP game server for managing game state across multiple clients.
    """

    BUFFER_SIZE = 1024

    def __init__(self) -> None:
        self.clients: dict[uuid.UUID, "Client"] = {}
        self.socket = socket.socket(type=socket.SOCK_DGRAM)  # udp

    def run(self, host: str = "0.0.0.0", port: int = 5260) -> None:
        """
        https://docs.python.org/3/library/socket.html#example
        """
        self.socket.bind((host, port))
        self.socket.setblocking(False)
        print(f"Server listening on {host}:{port}")
        while True:
            try:
                message, address = self.socket.recvfrom(self.BUFFER_SIZE)
            except BlockingIOError:
                # no data
                continue
            self.process(message, address)

    def process(self, data: bytes, address: str) -> None:
        # Parse message
        try:
            decoded = data.decode()
        except UnicodeDecodeError:
            print(f"WARNING cannot decode data of length {len(data)}")
            return
        try:
            parsed = json.loads(decoded)
        except json.JSONDecodeError:
            print(f"WARNING cannot parse JSON from data of length {len(decoded)}")
            return

        # Parse command
        command = parsed.get("c")

        # Connect
        if command == "connect":
            client_id = self.connect(address)
        else:
            # Parse client ID
            client_id = parsed.get("i")

        if client_id not in self.clients:
            print(f"WARNING invalid client ID {client_id}")
            return

        # Update client address
        self.clients[client_id].address = address

        # Parse command
        if parsed.get("c") == "ping":
            self.ping(client_id)

    def send(self, client_id: uuid.UUID, data: dict[str, t.Any]) -> None:
        """
        Send some JSON-formatted data to a client.
        """
        address = self.clients[client_id].address
        self.socket.sendto(json.dumps(data).encode(), address)

    def connect(self, address: str) -> uuid.UUID:
        """
        Connect a new client
        """
        client_id = uuid.uuid4()
        client = Client(address)
        self.clients[client_id] = client
        print(f"INFO connected new client f{client_id} to {address}")
        return client_id

    def ping(self, client_id: uuid.UUID) -> None:
        """
        Respond with just the time, for now.
        """
        # TODO certainly, we want to return more than the time, right?
        self.send(client_id, {"t": time()})


class Client:
    """
    Store client address for the server. Note that the client ID is not stored here.
    """

    def __init__(self, address: str) -> None:
        self.address = address


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
