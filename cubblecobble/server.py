import bisect
import time
import typing as t
import uuid

import communication
import constants
from state import initialize as initialize_pyxel
from state import State


def run() -> None:
    while True:
        # Always restart server in case of crash
        server = Server()
        try:
            server.run()
        except KeyboardInterrupt:
            return
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"ERROR {e}")
            server.socket.close()


class Server:
    """
    Create a UDP game server for managing game state across multiple clients.
    """

    BUFFER_SIZE = 1024

    def __init__(self, host: str = "0.0.0.0", port: int = 5260) -> None:
        # TODO move all these dicts to a single data structure
        self.client_addresses: dict[str, t.Any] = {}
        self.client_states: dict[str, State] = {}
        # Each series of inputs is (frame, client_id, inputs)
        # This list should be kept sorted by frame.
        self.client_inputs: dict[str, list[tuple[int, str, list[int]]]] = {}
        self.client_last_seen_at: dict[str, float] = {}

        self.socket = communication.create_server_socket(host, port)
        self.frame = 0

    def run(self) -> None:
        """
        https://docs.python.org/3/library/socket.html#example
        """
        # Note that we initialize pyxel, because we need to load tilemaps. But we don't
        # pyxel.run(...) because that would pause the server window too frequently.
        initialize_pyxel("Cubble Cobble - Server")
        while True:
            self.update()

    def update(self) -> None:
        """
        Run a single game loop.
        """
        t_start = time.time()

        # Receive and process messages
        for message, address in communication.receive_all(self.socket):
            self.process(message, address)

        # Process inputs
        for client_id, inputs in self.client_inputs.items():
            # Clean outdated inputs
            while inputs and inputs[0][0] < self.frame:
                inputs.pop(0)

            # Get inputs for current frame
            client_inputs = []
            if inputs and inputs[0][0] == self.frame:
                client_inputs = inputs[0][2]

            # Update game state
            self.client_states[client_id].update(client_inputs)

        # Get rid of clients that we haven't seen in a long while
        clients_to_remove = []
        remove_after_seconds = 5
        for client_id, last_seen_at in self.client_last_seen_at.items():
            if last_seen_at < time.time() - remove_after_seconds:
                clients_to_remove.append(client_id)
        for client_id in clients_to_remove:
            print(f"Removing outdated client: {client_id}")
            self.client_addresses.pop(client_id)
            self.client_inputs.pop(client_id)
            self.client_last_seen_at.pop(client_id)
            self.client_states.pop(client_id)

        # Share state with all clients
        for client_id, client_state in self.client_states.items():
            states = [client_state.as_json()]
            states += [
                other_client_state.as_json()
                for other_client_id, other_client_state in self.client_states.items()
                if other_client_id != client_id
            ]
            self.send(
                client_id,
                communication.COMMAND_STATE,
                {
                    communication.FRAME_KEY: self.frame,
                    communication.STATES_KEY: states,
                },
            )

        # Sleep until end of frame, thus maintaining a constant framerate
        self.frame += 1  # TODO we should sometimes loop over
        time_elapsed = time.time() - t_start
        if time_elapsed > constants.FRAME_DURATION:
            print(
                f"WARNING slow frame: {time_elapsed}s ({time_elapsed*100/constants.FRAME_DURATION})%"
            )
        else:
            time.sleep(constants.FRAME_DURATION - time_elapsed)

    def process(self, message: dict[str, t.Any], address: str) -> None:
        # Parse command
        command, data = communication.parse_command(message)

        # Connect
        if command == communication.COMMAND_CONNECT:
            self.on_connect(address)
            return
        # Ping
        if command == communication.COMMAND_PING:
            self.on_ping(address, data)
            return

        # Parse client ID
        client_id = data.get(communication.CLIENT_ID_KEY, "")
        if client_id not in self.client_addresses:
            print(f"WARNING invalid client ID: '{client_id}' for command: '{command}'")
            return
        # Update client address
        self.client_addresses[client_id] = address

        # State update
        if command == communication.COMMAND_STATE:
            self.on_state(client_id, data)
        else:
            print(f"WARNING Unrecognized command '{command}' from client '{client_id}'")

    def send(self, client_id: str, command: str, data: dict[str, t.Any]) -> None:
        """
        Send some JSON-formatted data to a client.
        """
        self.send_to(self.client_addresses[client_id], command, data)

    def send_to(self, address: t.Any, command: str, data: dict[str, t.Any]) -> None:
        """
        Send some JSON-formatted data to an address.
        """
        communication.send_command(self.socket, command, data, address)

    def on_connect(self, address: str) -> None:
        """
        Connect a new client

        The client ID is sent back to the client, which is then responsible for storing it.
        """
        client_id = str(uuid.uuid4())

        # Add new client
        self.client_addresses[client_id] = address
        self.client_inputs[client_id] = []
        self.client_states[client_id] = State()
        self.client_last_seen_at[client_id] = time.time()

        print(f"INFO connected new client f{client_id} to {address}")

        # Tell client about its client ID, such that they can send it back
        self.send(
            client_id,
            communication.COMMAND_CONNECT,
            {communication.CLIENT_ID_KEY: client_id},
        )

    def on_ping(self, address: t.Any, data: dict[str, t.Any]) -> None:
        """
        Respond with the same data and the current frame.
        """
        response_data = {
            # TODO handle missing field in client data?
            communication.TIME_KEY: data[communication.TIME_KEY],
            communication.FRAME_KEY: self.frame,
        }
        self.send_to(address, communication.COMMAND_PING, response_data)

    def on_state(self, client_id: str, data: dict["str", t.Any]) -> None:
        client_frame: int = int(data[communication.FRAME_KEY])
        if client_frame < self.frame:
            # This is normal if it's the first frame
            if client_frame > 0:
                print(
                    f"WARNING received late frame {client_frame} from client: {self.frame - client_frame} frames delay"
                )
            # TODO ignore state
        inputs: list[int] = data[communication.INPUTS_KEY]
        if not isinstance(inputs, list):
            print(
                f"WARNING invalid format for inputs: expected list got {inputs.__class__}"
            )
        # TODO don't insert inputs twice
        # TODO check inputs are valid
        bisect.insort(self.client_inputs[client_id], (client_frame, client_id, inputs))

        # Update client last seen date
        self.client_last_seen_at[client_id] = time.time()
