import json
import os
import typing as t
import socket

BUFFER_SIZE = 1024

COMMAND_KEY = "command"
COMMAND_CONNECT = "connect"
COMMAND_PING = "ping"
CLIENT_ID_KEY = "client_id"
TIME_KEY = "time"
DATA_KEY = "data"


def create_server_socket(host: str, port: int) -> socket.socket:
    s = _create_blocking_udp_socket()
    s.bind((host, port))
    print(f"Server listening on {host}:{port}")
    return s


def create_client_socket(host: str = "127.0.0.1", port: int = 5260) -> socket.socket:
    """
    Create non-blocking client socket
    """
    s = _create_blocking_udp_socket()
    host, port = get_server_address()
    s.connect((host, port))
    return s


def get_server_address() -> tuple[str, int]:
    """
    Find a game server.

    TODO auto-detect server on LAN
    """
    host = os.environ.get("GAME_SERVER_HOST", "127.0.0.1")
    port = os.environ.get("GAME_SERVER_PORT", "5260")
    return host, int(port)


def _create_blocking_udp_socket() -> socket.socket:
    s = socket.socket(type=socket.SOCK_DGRAM)
    s.setblocking(False)
    return s


def receive(s: socket.socket) -> tuple[dict[str, t.Any] | None, t.Any]:
    """
    Attempt to read JSON-formatted data. In case no data is available, return None, None.
    """
    try:
        encoded, address = s.recvfrom(BUFFER_SIZE)
    except BlockingIOError:
        return None, None
    try:
        decoded = encoded.decode()
    except UnicodeDecodeError:
        print(f"WARNING cannot decode data of length {len(encoded)}")
        return None, address
    try:
        parsed = json.loads(decoded)
    except json.JSONDecodeError:
        print(f"WARNING cannot parse JSON from data of length {len(decoded)}")
        return None, address
    if not isinstance(parsed, dict):
        print(f"WARNING parsed data is not valid dict {parsed}")
        return None, address
    return parsed, address


def send_command(
    s: socket.socket, command: str, data: dict[str, t.Any], address: t.Any = None
) -> None:
    """
    Send a command with arguments, to an optional address.

    If no address argument, then the message will be sent to the server that the client is connected to.
    """
    message = json.dumps({COMMAND_KEY: command, DATA_KEY: data}).encode()
    if address:
        s.sendto(message, address)
    else:
        s.send(message)


def parse_command(message: dict[str, t.Any]) -> tuple[str, dict[str, t.Any]]:
    """
    Parse command and data (arguments) fields in JSON message.
    """
    command = message.get(COMMAND_KEY)
    data = message.get(DATA_KEY, {})
    if not isinstance(command, str):
        print(f"WARNING invalid parsed command type: {command.__class__}")
        command = ""
    if not isinstance(data, dict):
        print(
            f"WARNING invalid parsed data type: {data.__class__} for command {command}"
        )
        data = {}
    if not command:
        return "", {}
    return command, data
