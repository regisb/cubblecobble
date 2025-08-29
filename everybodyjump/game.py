from time import time

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
        self.x: float = constants.SCREEN_WIDTH // 2 - constants.PLAYER_SIZE
        self.y: float = constants.SCREEN_HEIGHT // 2 - constants.PLAYER_SIZE
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
        pyxel.init(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        self.state = State()

        # Communicate with server
        self.client_id = ""
        self.socket = communication.create_client_socket()
        communication.send_command(self.socket, communication.COMMAND_CONNECT, {})


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
                    raise ValueError(f"Received invalid client ID from server: {client_id}")
                self.client_id = client_id
                print(f"INFO received client ID from server: {self.client_id}")


    def update(self) -> None:
        dt = self.state.update()

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
        self.state.x %= constants.SCREEN_WIDTH
        self.state.y += self.state.vy * dt
        self.state.y %= constants.SCREEN_HEIGHT

    def draw(self) -> None:
        pyxel.cls(constants.BLACK)
        draw_player(self.state.x, self.state.y)
        # Manage overlap
        if self.state.x >= constants.SCREEN_WIDTH - constants.PLAYER_SIZE:
            draw_player(self.state.x - constants.SCREEN_WIDTH, self.state.y)
        if self.state.y >= constants.SCREEN_HEIGHT - constants.PLAYER_SIZE:
            draw_player(self.state.x, self.state.y - constants.SCREEN_HEIGHT)


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
