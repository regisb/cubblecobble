import os
from time import time
import typing as t

import pyxel

import communication
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

        # Establish connection with server
        # Communicate with server
        self.client_id = ""
        self.socket = communication.create_client_socket()
        self.send_to_server(communication.COMMAND_CONNECT, {})

    def run(self) -> None:
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        # Handle restart command here
        if pyxel.btnp(pyxel.KEY_R):
            # Restart
            self.state = State()

        # Send a ping, just to check back-and-forth delay
        # if self.client_id:
        #     self.send_to_server(
        #         communication.COMMAND_PING, {communication.TIME_KEY: time()}
        #     )

        # Read server data
        self.receive_from_server()

        self.state.update()

    def draw(self) -> None:
        self.state.draw()

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
