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
        self.frame = 0

        # Establish connection with server
        # Communicate with server
        self.client_id = ""
        self.socket = communication.create_client_socket()
        self.send_to_server(communication.COMMAND_CONNECT, {})

    def run(self) -> None:
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        # Handle restart command here
        # TODO remove me? Only server can decide to restart.
        if pyxel.btnp(pyxel.KEY_R):
            # Restart
            self.state = State()

        # Read server data
        self.receive_from_server()

        # Send a ping once per second to check round-trip time (RTT)
        if self.frame % constants.FPS == 0:
            self.send_to_server(
                communication.COMMAND_PING, {communication.TIME_KEY: time()}
            )

        if not self.client_id:
            # Don't do anything until we have received a successful connect from the server
            return

        self.state.update()

    def draw(self) -> None:
        self.state.draw()

    def receive_from_server(self) -> None:
        for message, _address in communication.receive_all(self.socket):
            command, data = communication.parse_command(message)

            # TODO handle different commands here
            if command == communication.COMMAND_CONNECT:
                self.on_connect(data)
            elif command == communication.COMMAND_PING:
                self.on_ping(data)

    def on_connect(self, data: dict[str, t.Any]) -> None:
        client_id = data.get(communication.CLIENT_ID_KEY)
        if not client_id:
            raise ValueError(f"Received invalid client ID from server: {client_id}")
        self.client_id = client_id
        print(f"INFO received client ID from server: {self.client_id}")

    def on_ping(self, data: dict[str, t.Any]) -> None:
        rtt = time() - data[communication.TIME_KEY]
        rtt_frames = rtt / constants.FRAME_DURATION
        if rtt_frames > 10:
            # This might be normal: everything is paused when the window is minimized.
            # So we have to catch up.
            print(f"INFO RTT: {rtt*1000} ms ({rtt_frames} frames)")
        server_frame = data[communication.FRAME_KEY]
        if server_frame > self.frame:
            adjusted_frame = server_frame + int(constants.FPS * rtt / 2) + 1
            print(f"INFO Adjusting client frame from {self.frame} to {adjusted_frame})")
            self.frame = adjusted_frame
        elif server_frame < self.frame - constants.FPS:
            print(f"WARNING more than 1s delay between client and server frame: {self.frame - server_frame} frames")
            # TODO we should probably do something in that case, if it presents itself

    def send_to_server(self, command: str, data: dict[str, t.Any]) -> None:
        if self.client_id:
            data[communication.CLIENT_ID_KEY] = self.client_id
        communication.send_command(self.socket, command, data)
