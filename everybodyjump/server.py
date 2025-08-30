import socket
import typing as t
import uuid


import communication


def run() -> None:
    server = Server()
    server.run()


class Server:
    """
    Create a UDP game server for managing game state across multiple clients.
    """

    BUFFER_SIZE = 1024

    def __init__(self) -> None:
        self.clients: dict[str, "Client"] = {}
        self.socket = socket.socket(type=socket.SOCK_DGRAM)  # udp

    def run(self, host: str = "0.0.0.0", port: int = 5260) -> None:
        """
        https://docs.python.org/3/library/socket.html#example
        """
        self.socket = communication.create_server_socket(host, port)
        while True:
            message, address = communication.receive(self.socket)
            if message is None:
                # no data
                continue
            self.process(message, address)

    def process(self, message: dict[str, t.Any], address: str) -> None:
        # Parse command
        command, data = communication.parse_command(message)

        # Connect
        if command == communication.COMMAND_CONNECT:
            client_id = self.connect(address)
        else:
            # Parse client ID
            client_id = data.get(communication.CLIENT_ID_KEY, "")

        if client_id not in self.clients:
            print(f"WARNING invalid client ID: '{client_id}' for command: '{command}'")
            return

        # Update client address
        self.clients[client_id].address = address

        # Parse command
        if command == communication.COMMAND_PING:
            self.ping(client_id, data)

    def send(self, client_id: str, command: str, data: dict[str, t.Any]) -> None:
        """
        Send some JSON-formatted data to a client.
        """
        address = self.clients[client_id].address
        communication.send_command(self.socket, command, data, address)

    def connect(self, address: str) -> str:
        """
        Connect a new client

        The client ID is sent back to the client, which is then responsible for storing it.
        """
        client_id = str(uuid.uuid4())
        client = Client(address)
        self.clients[client_id] = client
        print(f"INFO connected new client f{client_id} to {address}")
        self.send(
            client_id,
            communication.COMMAND_CONNECT,
            {communication.CLIENT_ID_KEY: client_id},
        )
        return client_id

    def ping(self, client_id: str, data: dict[str, t.Any]) -> None:
        """
        Respond with the same data.
        """
        self.send(client_id, communication.COMMAND_PING, data)


class Client:
    """
    Store client address for the server. Note that the client ID is not stored here.
    """

    def __init__(self, address: str) -> None:
        self.address = address
