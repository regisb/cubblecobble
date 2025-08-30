FPS = 30

# Level
TILE_SIZE: int = 8# each tile is 8x8 pixels in pyxel
LEVEL_SIZE_TILES = 16 # TODO don't hardcode this
LEVEL_SIZE_PIXELS = LEVEL_SIZE_TILES * TILE_SIZE

# Global properties
GRAVITY = 1

# Player properties
# Note that speeds are counted per frame, and not per second
PLAYER_SIZE: int = 1 * TILE_SIZE
PLAYER_SPEED = 2
PLAYER_WEIGHT = 5
PLAYER_MAX_FALL_SPEED = 2
PLAYER_JUMP_SPEED = 20

# Colors
# https://github.com/kitao/pyxel?tab=readme-ov-file#color-palette
BLACK = 0
WHITE = 7
