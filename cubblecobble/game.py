import os
from time import time
import typing as t

import pyxel

import communication
import constants
from state import Commands, State


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

        # Initialize states
        self.state: State = State()
        self.frame = 0

        # Store inputs
        # Each entry is a (frame, inputs) tuple.
        self.inputs: list[tuple[int, list[int]]] = []

        # Establish connection with server
        # Communicate with server
        self.client_id = ""
        self.socket = communication.create_client_socket()
        self.send_command(communication.COMMAND_CONNECT, {})

    def run(self) -> None:
        pyxel.run(self.update, self.draw)


    def update(self) -> None:
        # Handle restart command here
        # TODO remove me? Only server can decide to restart.
        # Also, we could use pyxel.reset() to actually reset.
        # if pyxel.btnp(pyxel.KEY_R):
        #     # Restart
        #     self.state = State()

        # Send a ping once per second to check round-trip time (RTT)
        if self.frame % constants.FPS == 0:
            self.send_command(
                communication.COMMAND_PING, {communication.TIME_KEY: time()}
            )

        # Don't do anything until we have received a successful connect from the server
        if self.client_id:
            ############# Collect keys pressed as inputs
            inputs = []
            if pyxel.btn(pyxel.KEY_LEFT):
                inputs.append(Commands.LEFT)
            if pyxel.btn(pyxel.KEY_RIGHT):
                inputs.append(Commands.RIGHT)
            if pyxel.btnp(pyxel.KEY_SPACE):  # Note that we don't support multiple jumps
                inputs.append(Commands.JUMP)
            self.inputs.append((self.frame, inputs))

            # Share data with server as soon as possible.
            self.send_command(
                communication.COMMAND_STATE,
                {
                    communication.CLIENT_ID_KEY: self.client_id,
                    communication.FRAME_KEY: self.frame,
                    communication.INPUTS_KEY: inputs,
                },
            )

            # Apply all actions
            self.state.set_inputs(self.client_id, inputs)
            self.state.update()

        # We do this after the update, such that server has as much time as possible to
        # respond, but before drawing, such that what we display is as accurate as
        # possible.
        self.receive_from_server()

        # Move on to next frame
        self.frame += 1

    def draw(self) -> None:
        if self.client_id:
            self.state.draw()
        else:
            pyxel.cls(constants.BLACK)
            host, port = self.socket.getpeername()
            pyxel.text(
                20,
                constants.LEVEL_SIZE_PIXELS // 2 - 10,
                f"Connecting to\n{host}:{port}...",
                constants.WHITE,
            )

    def receive_from_server(self) -> None:
        for message, _address in communication.receive_all(self.socket):
            command, data = communication.parse_command(message)

            if command == communication.COMMAND_CONNECT:
                self.on_connect(data)
            elif command == communication.COMMAND_PING:
                self.on_ping(data)
            elif command == communication.COMMAND_STATE:
                self.on_state(data)
            else:
                print(f"WARNING unknow command from server: '{command}'")

    def on_connect(self, data: dict[str, t.Any]) -> None:
        client_id = data.get(communication.CLIENT_ID_KEY)
        if not client_id:
            raise ValueError(f"Received invalid client ID from server: {client_id}")
        self.client_id = client_id
        self.state.add_client(self.client_id)
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
            print(
                f"WARNING more than 1s delay between client and server frame: {self.frame - server_frame} frames"
            )
            # TODO IMPORTANT we must do something in that case. It happens because the server/client frame rates are slightly different.

    def on_state(self, data: dict[str, t.Any]) -> None:
        server_frame = data[communication.FRAME_KEY]
        if server_frame >= self.frame:
            print("WARNING Server is ahead. Did we pause the game?")
            # TODO IMPORTANT we should be doing something about it...

        # Load
        self.state.from_json(data[communication.STATE_KEY])

        # Clear inputs that came before the server frame
        while self.inputs and self.inputs[0][0] < server_frame:
            self.inputs.pop(0)

        # Re-apply all inputs
        for frame in range(server_frame + 1, self.frame + 1):
            inputs = []
            for past_frame, past_inputs in self.inputs:
                # TODO there is a more efficient way to read this list
                if past_frame == frame:
                    inputs = past_inputs
                if past_frame > frame:
                    break
            self.state.set_inputs(self.client_id, inputs)
            self.state.update()

    def send_command(self, command: str, data: dict[str, t.Any]) -> None:
        """
        Send command to server.
        """
        if self.client_id:
            data[communication.CLIENT_ID_KEY] = self.client_id
        communication.send_command(self.socket, command, data)
