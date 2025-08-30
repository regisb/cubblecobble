import time
import typing as t
import uuid

import communication
import constants


def run() -> None:
    server = Server()
    server.run()


class Server:
    """
    Create a UDP game server for managing game state across multiple clients.
    """

    BUFFER_SIZE = 1024

    def __init__(self, host: str = "0.0.0.0", port: int = 5260) -> None:
        self.client_addresses: dict[str, t.Any] = {}
        self.socket = communication.create_server_socket(host, port)
        self.frame = 0

    def run(self) -> None:
        """
        https://docs.python.org/3/library/socket.html#example
        """
        while True:
            t_start = time.time()

            # Receive and process messages
            for message, address in communication.receive_all(self.socket):
                self.process(message, address)

            # Sleep until end of frame, thus maintaining a constant framerate
            time_elapsed = time.time() - t_start
            if time_elapsed > constants.FRAME_DURATION:
                print(
                    f"WARNING slow frame: {time_elapsed}s ({time_elapsed*100/constants.FRAME_DURATION})%"
                )
            else:
                time.sleep(constants.FRAME_DURATION - time_elapsed)
            self.frame += 1 # TODO we should sometimes loop over

    def process(self, message: dict[str, t.Any], address: str) -> None:
        # Parse command
        command, data = communication.parse_command(message)

        # Connect
        if command == communication.COMMAND_CONNECT:
            self.connect(address)
            return
        # Ping
        if command == communication.COMMAND_PING:
            self.ping(address, data)
            return

        # Parse client ID
        client_id = data.get(communication.CLIENT_ID_KEY, "")
        if client_id not in self.client_addresses:
            print(f"WARNING invalid client ID: '{client_id}' for command: '{command}'")
            return
        # Update client address
        self.client_addresses[client_id] = address
        # TODO Parse other commands

    def send(self, client_id: str, command: str, data: dict[str, t.Any]) -> None:
        """
        Send some JSON-formatted data to a client.
        """
        self.send_to(self.client_addresses[client_id], command, data)

    def send_to(self, address: t.Any, command: str, data: dict[str, t.Any]) -> None:
        """
        Send some JSON-formatted data to an address.
        """
        communication.send_command(
            self.socket, command, data, address
        )

    def connect(self, address: str) -> str:
        """
        Connect a new client

        The client ID is sent back to the client, which is then responsible for storing it.
        """
        client_id = str(uuid.uuid4())
        self.client_addresses[client_id] = address
        print(f"INFO connected new client f{client_id} to {address}")
        self.send(
            client_id,
            communication.COMMAND_CONNECT,
            {communication.CLIENT_ID_KEY: client_id},
        )
        return client_id

    def ping(self, address: t.Any, data: dict[str, t.Any]) -> None:
        """
        Respond with the same data and the current frame.
        """
        response_data = {
            # TODO handle missing field in client data?
            communication.TIME_KEY: data[communication.TIME_KEY],
            communication.FRAME_KEY: self.frame,
        }
        self.send_to(address, communication.COMMAND_PING, response_data)
