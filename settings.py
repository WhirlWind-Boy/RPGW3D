import math
from enum import Enum

# --- Configuration ---
WIDTH, HEIGHT = 800, 480
FPS = 60
TILE_SIZE = 64
MAP_SIZE = 30  
FOV = math.pi / 3
NUM_RAYS = 120
MAX_DEPTH = 800
DELTA_ANGLE = FOV / NUM_RAYS
PLAYER_SPEED = 3.0 
PLAYER_ROTATION_SPEED = 0.05
QUEST_PICKUP_DISTANCE = 40
WALL_HEIGHT_MULTIPLIER = 21000
FOG_DISTANCE_DIVISOR = 2.6
PARTICLE_EPSILON = 0.0001

# Cloud parallax constants
CLOUD_SPRITE_PATH = "clouds_pixel.png"
CLOUD_LAYERS = 3  
CLOUD_SPEED_MULTIPLIERS = [0.05, 0.1, 0.2]

# --- WEATHER SETTINGS ---
WEATHER_TYPES = ['none', 'rain', 'rain_heavy', 'snow', 'sand']

WEATHER_TRANSITIONS = {
    'none': (2000, 4000),
    'rain': (1000, 2000),
    'rain_heavy': (1000, 1500),
    'snow': (1500, 3000),
    'sand': (800, 1500)
}

WEATHER_INTENSITY = {
    'none': {'count': 0},
    'rain': {'count': 150},
    'rain_heavy': {'count': 400},
    'snow': {'count': 200},
    'sand': {'count': 300}
}

# Weather Particle Colors
RAIN_COLOR = (150, 170, 200)
SNOW_COLOR = (255, 255, 255)
DUST_COLOR = (194, 178, 128)

# --- SPRITE ASSET PATHS ---
WALL_TEXTURE_PATH = "Brick_Wall_64x64.png"
FLOOR_DIRT_PATH = "Dirt_Road_64x64.png"
FLOOR_GRASS_PATH = "Grass_Ground_64x64.png" 
HEALTH_POTION_PATH = "health_potion.png"
MANA_POTION_PATH = "mana_potion.png"

# Environment Sprites
BUSH_PATH = "bush.png"
TREE_DEAD_PATH = "DeadTree.png"
TREE_LEAFY_PATH = "LeafyTree.png"
ROCK_PATH = "rocks.png"
FIREBALL_PATH = "fireball.png"

# Inventory Sprites
KEY_PATH = "Key_Icon.png"
SWORD_PATH = "Sword_Icon.png"
FOOD_PATH = "food.png"
ARTIFACT_PATH = "artifact.png"

class TileType(Enum):
    EMPTY = 0; WALL_BRICK = 1; DOOR = 2; WATER = 3; GRASS = 4
    TREE = 5; WALL_STONE = 6; WALL_WOOD = 7; STANDING_TORCH = 8; WALL_TORCH = 9
    BUSH = 10; ROCK = 11; DEAD_TREE = 12
    ITEM_DAGGER = 13; ITEM_KEY = 14; ITEM_FOOD = 15; ITEM_ARTIFACT = 16
    ITEM_HEALTH_POTION = 17

class FloorTextureType(Enum):
    DIRT = 1; STONE = 2; WOOD = 3; GRASS = 4

MAP_DATA_FILE = "map_data.json"
TOOLBAR_HEIGHT = 80
GRID_SIZE = 20