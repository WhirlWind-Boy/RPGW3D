import pygame
import math
import random
import json
import os
from settings import *
from inventory import Inventory
from ui import ActionBar

# Initialize pygame components explicitly for engine.py safely
pygame.mixer.init()

def load_audio_safe(filename):
    try: return pygame.mixer.Sound(filename)
    except: return None

SFX_PICKUP = load_audio_safe("pickup.wav")
SFX_DOOR = load_audio_safe("door.wav")
SFX_ERROR = load_audio_safe("error.wav")
SFX_USE = load_audio_safe("use.wav")
SFX_WALK = load_audio_safe("walking.mp3")
SFX_RAIN = load_audio_safe("raining.mp3")
SFX_FIREBALL = load_audio_safe("shoot_fireball.wav")

CH_WALK = pygame.mixer.Channel(1)
CH_RAIN = pygame.mixer.Channel(2)

class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False) 
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("RPGW3D Engine")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("georgia", 16) 
        
        self.sfx = {
            "pickup": SFX_PICKUP,
            "door": SFX_DOOR,
            "error": SFX_ERROR,
            "use": SFX_USE,
            "fireball": SFX_FIREBALL
        }
        
        try:
            pygame.mixer.music.load("bgm.mp3") 
            pygame.mixer.music.set_volume(0.4)
        except: pass
        
        self.ui_icons = {
            "key": self.load_sprite_image(KEY_PATH, scale=True, size=(40, 40), fallback="none"),
            "sword": self.load_sprite_image(SWORD_PATH, scale=True, size=(40, 40), fallback="none"),
            "health_potion": self.load_sprite_image(HEALTH_POTION_PATH, scale=True, size=(40, 40), fallback="food"),
            "mana_potion": self.load_sprite_image(MANA_POTION_PATH, scale=True, size=(40, 40), fallback="food"),
            "artifact": self.load_sprite_image(ARTIFACT_PATH, scale=True, size=(40, 40), fallback="artifact"),
            "fireball": self.load_sprite_image(FIREBALL_PATH, scale=True, size=(40, 40), fallback="artifact")
        }
        
        self.inventory = Inventory(icons_dict=self.ui_icons, sfx_dict=self.sfx)
        self.action_bar = ActionBar(self.ui_icons)
        
        # --- Drag and Drop State ---
        self.drag_item = None
        self.drag_source = None 
        
        self.projectiles = [] 
        self.enemies = [] 
        
        self.floor_texture_type = FloorTextureType.DIRT
        
        self.exterior_map, self.exterior_items = self.load_or_generate_map()
        self.interior_map, self.interior_items = self.extract_items(self.generate_dungeon_layout())
        
        self.world_items = self.exterior_items
        self.map = self.exterior_map
        
        self.player_x, self.player_y = self.get_safe_spawn()
        self.player_angle = 0
        self.attack_swing = 0.0 
        
        self.health, self.max_health = 100, 100
        self.mana, self.max_mana = 50, 50
        self.time = 600.0 
        self.ambient_light = 255
        self.sky_keyframes = {0: (5, 5, 15), 400: (10, 10, 30), 600: (255, 120, 70), 800: (135, 206, 235), 1200: (100, 180, 255), 1600: (135, 206, 235), 1800: (200, 60, 30), 2000: (20, 15, 40), 2400: (5, 5, 15)}
        
        self.door_tex = self.load_door_texture() 
        self.wall_textures = self.load_all_wall_textures()
        self.floor_textures = self.load_all_floor_textures()
        self.floor_tex = self.floor_textures[FloorTextureType.DIRT.name]
        
        self.tree_leafy_sprite = self.load_sprite_image(TREE_LEAFY_PATH, fallback="tree")
        self.tree_dead_sprite = self.load_sprite_image(TREE_DEAD_PATH, fallback="dead")
        self.bush_sprite = self.load_sprite_image(BUSH_PATH, fallback="bush")
        self.rock_sprite = self.load_sprite_image(ROCK_PATH, fallback="rock")
        self.torch_sprite = self.generate_standing_torch_sprite()
        
        self.drop_sword_sprite = self.load_sprite_image(SWORD_PATH, fallback="none")
        self.drop_key_sprite = self.load_sprite_image(KEY_PATH, fallback="none")
        self.drop_food_sprite = self.load_sprite_image(MANA_POTION_PATH, fallback="food")
        self.drop_health_sprite = self.load_sprite_image(HEALTH_POTION_PATH, fallback="food")
        self.drop_artifact_sprite = self.load_sprite_image(ARTIFACT_PATH, fallback="artifact")
        
        self.weapon_idle_img = self.load_hud_weapon("weapon_idle.png")
        self.weapon_swing_img = self.load_hud_weapon("weapon_swing.png")
        
        self.cloud_sprite = self.load_cloud_sprite()
        self.cloud_sprites_cache = {}  
        self.clouds = self.generate_parallax_clouds()
        
        self.wind_effect = 0.0
        self.weather_type = 'none'
        self.weather_target = 'none'
        self.weather_timer = 0
        self.weather_duration = random.randint(*WEATHER_TRANSITIONS.get('none', (2000, 4000))) 
        self.weather_intensity = 0.0 
        self.particles = []
        
        self.global_flicker = 1.0
        self.lightmap = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        self.build_lightmap()

        self.consume_message = ""; self.consume_message_timer = 0
        self.level_complete = False
        self.level_complete_timer = 0
        
        self.depth_buffer = [MAX_DEPTH] * NUM_RAYS
        
        self.in_interior = False
        self.exterior_spawn = (128, 128)  
        self.doors = []
        self.build_interactables() 
        
        self.hovered_interactable = None
        self.hovered_rect = None
        
        self.fog_of_war = [[False for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        self.minimap_reveal_radius = 8  
        self.minimap_x, self.minimap_y, self.minimap_size = WIDTH - 150, 20, 140

    def extract_items(self, raw_map):
        items = []
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                v = raw_map[y][x]
                if v in [TileType.ITEM_DAGGER.value, TileType.ITEM_KEY.value, TileType.ITEM_FOOD.value, TileType.ITEM_ARTIFACT.value, TileType.ITEM_HEALTH_POTION.value]:
                    items.append({'id': v, 'x': x*TILE_SIZE + 32, 'y': y*TILE_SIZE + 32})
                    raw_map[y][x] = TileType.EMPTY.value 
        return raw_map, items

    def load_sprite_image(self, path, scale=True, size=(TILE_SIZE, TILE_SIZE), fallback="tree"):
        try:
            img = pygame.image.load(path).convert_alpha()
            img.set_colorkey((0,0,0)) 
            if scale: return pygame.transform.scale(img, size)
            else: return img
        except: 
            surf = pygame.Surface(size, pygame.SRCALPHA)
            if fallback == "tree":
                pygame.draw.rect(surf, (80, 50, 30), (28, 40, 8, 24))
                for _ in range(30): pygame.draw.circle(surf, (34, 139, 34), (random.randint(18, 46), random.randint(8, 38)), random.randint(5, 10))
            elif fallback == "dead":
                pygame.draw.rect(surf, (60, 40, 30), (28, 40, 8, 24))
                pygame.draw.line(surf, (60, 40, 30), (32, 40), (15, 20), 4); pygame.draw.line(surf, (60, 40, 30), (32, 35), (45, 15), 4)
            elif fallback == "bush":
                for _ in range(20): pygame.draw.circle(surf, (20, 100, 30), (random.randint(15, 49), random.randint(30, 60)), random.randint(8, 15))
            elif fallback == "rock":
                pygame.draw.polygon(surf, (100, 100, 100), [(10, 60), (32, 30), (54, 60)])
            elif fallback == "food":
                pygame.draw.circle(surf, (200, 150, 100), (size[0]//2, size[1]//2), size[0]//3)
            elif fallback == "artifact":
                pygame.draw.polygon(surf, (0, 255, 255), [(size[0]//2, 5), (size[0]-5, size[1]//2), (size[0]//2, size[1]-5), (5, size[1]//2)])
            elif fallback == "none":
                return None
            else:
                pygame.draw.circle(surf, (150, 50, 150), (size[0]//2, size[1]//2), size[0]//3)
            return surf

    def load_hud_weapon(self, path):
        try:
            img = pygame.image.load(path).convert_alpha()
            img.set_colorkey((0,0,0))
            return pygame.transform.scale(img, (400, 400))
        except:
            surf = pygame.Surface((400, 400), pygame.SRCALPHA)
            pygame.draw.rect(surf, (150, 150, 150), (180, 50, 40, 250)) 
            pygame.draw.rect(surf, (200, 150, 50), (140, 280, 120, 20)) 
            pygame.draw.rect(surf, (100, 50, 20), (185, 300, 30, 100)) 
            return surf

    def build_interactables(self):
        self.doors = []
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                if self.map[y][x] == TileType.DOOR.value:
                    self.doors.append({
                        "x": x * TILE_SIZE + TILE_SIZE // 2, "y": y * TILE_SIZE + TILE_SIZE // 2,
                        "name": "Dungeon Door", "key_required": "Brass Key" if not self.in_interior else None
                    })

    def generate_dungeon_layout(self):
        d_map = [[1 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        x, y = MAP_SIZE // 2, MAP_SIZE // 2
        d_map[y][x] = 0
        for _ in range(600):
            move = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
            if 1 <= x + move[0] < MAP_SIZE-1 and 1 <= y + move[1] < MAP_SIZE-1:
                x, y = x + move[0], y + move[1]
                d_map[y][x] = 0
        for _ in range(15):
            rx, ry = random.randint(1, MAP_SIZE-2), random.randint(1, MAP_SIZE-2)
            if d_map[ry][rx] == 0: d_map[ry][rx] = TileType.STANDING_TORCH.value
                    
        placed = False
        while not placed:
            rx, ry = random.randint(1, MAP_SIZE-2), random.randint(1, MAP_SIZE-2)
            if d_map[ry][rx] == 0: 
                d_map[ry][rx] = TileType.ITEM_ARTIFACT.value
                placed = True
        return d_map

    def load_or_generate_map(self):
        try:
            if os.path.exists(MAP_DATA_FILE):
                with open(MAP_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    if 'map' in data:
                        self.floor_texture_type = FloorTextureType[data.get('floor_texture', 'DIRT')]
                        return self.extract_items(data.get('map'))
        except: pass
        return self.extract_items(self.generate_dungeon_layout())

    def build_lightmap(self):
        self.lightmap = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                val = self.map[y][x]
                if val == TileType.STANDING_TORCH.value or val == TileType.WALL_TORCH.value:
                    for ly in range(max(0, y-5), min(MAP_SIZE, y+6)):
                        for lx in range(max(0, x-5), min(MAP_SIZE, x+6)):
                            dist = math.hypot(x - lx, y - ly)
                            intensity = int(max(0, 255 - (dist * 40)))
                            self.lightmap[ly][lx] = min(255, self.lightmap[ly][lx] + intensity)

    def get_safe_spawn(self):
        for _ in range(100):
            r, c = random.randint(1, MAP_SIZE-2), random.randint(1, MAP_SIZE-2)
            if self.map[r][c] == 0: return (c * TILE_SIZE + 32, r * TILE_SIZE + 32)
        return (128, 128)

    def lerp_color(self, c1, c2, t):
        t_smooth = (1 - math.cos(t * math.pi)) / 2
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t_smooth) for i in range(3))

    def get_sky_color(self):
        if self.in_interior: return (15, 15, 20)
        keys = sorted(self.sky_keyframes.keys())
        base_color = (5, 5, 15)
        for i in range(len(keys) - 1):
            if keys[i] <= self.time <= keys[i+1]:
                base_color = self.lerp_color(self.sky_keyframes[keys[i]], self.sky_keyframes[keys[i+1]], (self.time - keys[i]) / (keys[i+1] - keys[i]))
                break
        if 'rain' in self.weather_type:
            target_dark = (40, 45, 50)
            base_color = tuple(int(base_color[i] * (1 - self.weather_intensity) + target_dark[i] * self.weather_intensity) for i in range(3))
        elif 'sand' in self.weather_type:
            target_dark = (120, 100, 70)
            base_color = tuple(int(base_color[i] * (1 - self.weather_intensity) + target_dark[i] * self.weather_intensity) for i in range(3))
        return base_color

    def get_smooth_ambient_light(self):
        t = self.time
        if 400 <= t < 800: amb = int(40 + (255 - 40) * ((t - 400) / 400)) 
        elif 800 <= t < 1600: amb = 255 
        elif 1600 <= t < 2000: amb = int(255 - (255 - 40) * ((t - 1600) / 400)) 
        else: amb = 40 
        if 'rain' in self.weather_type or 'sand' in self.weather_type:
            amb = int(amb * (1.0 - (self.weather_intensity * 0.5)))
        return amb

    def generate_standing_torch_sprite(self):
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(surf, (100, 50, 20), (30, 24, 4, 40)); pygame.draw.rect(surf, (80, 80, 80), (28, 20, 8, 6))
        pygame.draw.circle(surf, (255, 150, 0), (32, 16), 8); pygame.draw.circle(surf, (255, 200, 50), (32, 18), 5)
        return surf

    def load_door_texture(self):
        tex = pygame.Surface((TILE_SIZE, TILE_SIZE)); tex.fill((100, 50, 20)) 
        for x in range(0, TILE_SIZE, 16): pygame.draw.line(tex, (60, 30, 10), (x, 0), (x, TILE_SIZE), 2)
        pygame.draw.rect(tex, (100, 100, 100), (0, TILE_SIZE//2 - 4, TILE_SIZE, 8))
        pygame.draw.circle(tex, (200, 180, 50), (TILE_SIZE - 12, TILE_SIZE//2), 6)
        return tex

    def load_all_wall_textures(self):
        textures = {}
        try: textures[TileType.WALL_BRICK.value] = pygame.transform.scale(pygame.image.load(WALL_TEXTURE_PATH).convert(), (TILE_SIZE, TILE_SIZE)) 
        except:
            tex = pygame.Surface((TILE_SIZE, TILE_SIZE)); tex.fill((90, 45, 35))
            for y in range(0, TILE_SIZE, 16): pygame.draw.line(tex, (50, 25, 20), (0, y), (TILE_SIZE, y), 2)
            textures[TileType.WALL_BRICK.value] = tex
        stone = pygame.Surface((TILE_SIZE, TILE_SIZE)); stone.fill((100, 100, 100))
        for y in range(0, TILE_SIZE, 16):
            pygame.draw.line(stone, (50, 50, 50), (0, y), (TILE_SIZE, y), 2)
            for x in range(16 if (y // 16) % 2 == 0 else 0, TILE_SIZE, 32): pygame.draw.line(stone, (50, 50, 50), (x, y), (x, y+16), 2)
        textures[TileType.WALL_STONE.value] = stone
        wood = pygame.Surface((TILE_SIZE, TILE_SIZE)); wood.fill((120, 70, 30))
        for x in range(0, TILE_SIZE, 16): pygame.draw.line(wood, (80, 40, 15), (x, 0), (x, TILE_SIZE), 2)
        textures[TileType.WALL_WOOD.value] = wood
        w_torch = textures[TileType.WALL_STONE.value].copy()
        pygame.draw.rect(w_torch, (80, 80, 80), (28, 20, 8, 20)); pygame.draw.circle(w_torch, (255, 150, 0), (32, 16), 10); pygame.draw.circle(w_torch, (255, 255, 100), (32, 18), 5)
        textures[TileType.WALL_TORCH.value] = w_torch
        return textures

    def generate_stone_dirt_texture(self):
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE)); surf.fill((65, 38, 15))
        random.seed(42) 
        for y in range(0, TILE_SIZE, 12):
            for x in range(0, TILE_SIZE, 12):
                cx, cy, r = x + random.randint(-4, 4), y + random.randint(-4, 4), random.uniform(5, 9)
                pts = [(cx + math.cos(math.radians(a))*r, cy + math.sin(math.radians(a))*r) for a in range(0, 360, 60)]
                for ox in [-TILE_SIZE, 0, TILE_SIZE]:
                    for oy in [-TILE_SIZE, 0, TILE_SIZE]: pygame.draw.polygon(surf, random.choice([(125, 85, 30), (145, 100, 40), (110, 70, 20)]), [(px+ox, py+oy) for px, py in pts])
        return surf

    def load_all_floor_textures(self):
        textures = {}
        try: textures['DIRT'] = pygame.transform.scale(pygame.image.load(FLOOR_DIRT_PATH).convert(), (TILE_SIZE, TILE_SIZE)) 
        except: textures['DIRT'] = self.generate_stone_dirt_texture()
        stone = pygame.Surface((TILE_SIZE, TILE_SIZE)); stone.fill((130, 130, 130))
        for _ in range(200): pygame.draw.rect(stone, (random.randint(100, 150), random.randint(100, 150), random.randint(100, 150)), (random.randint(0, 63), random.randint(0, 63), random.randint(1, 3), random.randint(1, 3)))
        textures['STONE'] = stone
        wood = pygame.Surface((TILE_SIZE, TILE_SIZE)); wood.fill((139, 69, 19))
        for y in range(0, TILE_SIZE, 4): pygame.draw.line(wood, (random.randint(120, 160), random.randint(50, 90), random.randint(20, 40)), (0, y), (64, y), 3)
        textures['WOOD'] = wood
        try: textures['GRASS'] = pygame.transform.scale(pygame.image.load(FLOOR_GRASS_PATH).convert(), (TILE_SIZE, TILE_SIZE))
        except:
            grass = pygame.Surface((TILE_SIZE, TILE_SIZE)); grass.fill((34, 139, 34))
            for _ in range(100): pygame.draw.rect(grass, (random.randint(20, 60), random.randint(120, 150), random.randint(20, 60)), (random.randint(0, 63), random.randint(0, 63), 2, 2))
            textures['GRASS'] = grass
        return textures

    def load_cloud_sprite(self):
        try: return pygame.image.load(CLOUD_SPRITE_PATH).convert_alpha()
        except:
            surf = pygame.Surface((100, 40), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255, 200), (20, 20), 15); pygame.draw.circle(surf, (255, 255, 255, 200), (40, 15), 18)
            pygame.draw.circle(surf, (255, 255, 255, 200), (60, 20), 16); pygame.draw.rect(surf, (255, 255, 255, 200), (20, 20, 40, 20))
            return surf

    def get_scaled_cloud_sprite(self, scale):
        rounded_scale = round(scale, 1)
        if rounded_scale not in self.cloud_sprites_cache:
            w, h = self.cloud_sprite.get_size()
            self.cloud_sprites_cache[rounded_scale] = pygame.transform.scale(self.cloud_sprite, (int(w * rounded_scale), int(h * rounded_scale)))
        return self.cloud_sprites_cache[rounded_scale]

    def generate_parallax_clouds(self):
        clouds = []
        for layer in range(CLOUD_LAYERS):
            depth = layer / (CLOUD_LAYERS - 1) if CLOUD_LAYERS > 1 else 1.0  
            for _ in range(4 + layer):
                clouds.append({'x': random.randint(0, WIDTH), 'y': random.randint(5, 80 + layer * 20), 'scale': 3.0 + (depth * 3.5), 'depth': depth, 'speed_mult': CLOUD_SPEED_MULTIPLIERS[layer], 'alpha': 220 - int(depth * 50)})
        return clouds

    def manage_weather(self):
        self.weather_timer += 1
        if self.weather_type != self.weather_target:
            self.weather_intensity -= 0.003
            if self.weather_intensity <= 0: self.weather_type = self.weather_target
        else:
            if self.weather_intensity < 1.0: self.weather_intensity += 0.003
        if self.weather_timer >= self.weather_duration and not self.in_interior:
            self.weather_target = random.choice([w for w in WEATHER_TYPES if w != self.weather_type])
            self.weather_timer = 0
            self.weather_duration = random.randint(*WEATHER_TRANSITIONS.get(self.weather_target, (2000, 4000)))
        target_count = int(WEATHER_INTENSITY.get(self.weather_type, {}).get('count', 0) * self.weather_intensity)
        while len(self.particles) < target_count: self.particles.append({'x': random.uniform(0, MAP_SIZE*TILE_SIZE), 'y': random.uniform(0, MAP_SIZE*TILE_SIZE), 'z': random.uniform(-180, 180), 'speed': random.uniform(4, 8), 'wind_accel': 0})
        while len(self.particles) > target_count and len(self.particles) > 0: self.particles.pop()

    def use_specific_door(self, door):
        if "key_required" in door and door["key_required"] is not None:
            key_item = None
            for slot in self.inventory.slots:
                if slot and slot["type"] == "key" and slot["name"] == door["key_required"] and slot["qty"] > 0: 
                    key_item = slot
                    break
            if not key_item:
                if self.sfx.get("error"): self.sfx["error"].play()
                self.consume_message = f"Need {door['key_required']}!"; self.consume_message_timer = 120; return
            if random.random() < 0.10:
                if self.sfx.get("error"): self.sfx["error"].play()
                key_item["qty"] -= 1
                if key_item["qty"] <= 0: self.inventory.slots[self.inventory.slots.index(key_item)] = None
                self.consume_message = "The key broke in the lock!"
                self.consume_message_timer = 120
                return
        if self.sfx.get("door"): self.sfx["door"].play()
        self.exterior_spawn = (self.player_x, self.player_y)
        self.in_interior = not self.in_interior
        if self.in_interior:
            self.map = self.interior_map; self.world_items = self.interior_items
            self.player_x, self.player_y = self.get_safe_spawn()
            self.consume_message = f"Entered {door['name']}!"
            self.exterior_floor = self.floor_texture_type
            self.floor_texture_type = FloorTextureType.STONE
            self.weather_type, self.weather_target, self.weather_intensity = 'rain_heavy', 'rain_heavy', 1.0
            self.weather_timer, self.weather_duration = 0, 999999
            try: pygame.mixer.music.load("dungeon_rainstorm.mp3"); pygame.mixer.music.play(-1)
            except: pass
        else:
            self.map = self.exterior_map; self.world_items = self.exterior_items
            self.player_x, self.player_y = self.exterior_spawn
            self.consume_message = "Exited dungeon!"
            if hasattr(self, 'exterior_floor'): self.floor_texture_type = self.exterior_floor
            self.weather_target = 'none' 
            self.weather_duration = random.randint(*WEATHER_TRANSITIONS.get('none', (2000, 4000)))
            try: pygame.mixer.music.load("bgm.mp3"); pygame.mixer.music.play(-1)
            except: pass
        self.consume_message_timer = 120
        self.build_lightmap()
        self.build_interactables()

    def update_fog_of_war(self):
        pgx, pgy = int(self.player_x / TILE_SIZE), int(self.player_y / TILE_SIZE)
        for y in range(max(0, pgy - self.minimap_reveal_radius), min(MAP_SIZE, pgy + self.minimap_reveal_radius + 1)):
            for x in range(max(0, pgx - self.minimap_reveal_radius), min(MAP_SIZE, pgx + self.minimap_reveal_radius + 1)):
                if math.hypot(x - pgx, y - pgy) <= self.minimap_reveal_radius: self.fog_of_war[y][x] = True

    def draw_sun_moon(self):
        sun_size = 40
        if 400 <= self.time < 2000:  
            progress = (self.time - 400) / 1600.0
            sun_x = int(50 + progress * (WIDTH - 100))
            sun_y = int(HEIGHT // 4 + 40 * math.sin(progress * math.pi))
            sun_alpha = 1.0
            if 'rain' in self.weather_type or 'sand' in self.weather_type:
                sun_alpha = max(0, 1.0 - (self.weather_intensity * 1.5))
            if sun_alpha > 0:
                pygame.draw.circle(self.screen, (int(255*sun_alpha), int(200*sun_alpha), int(50*sun_alpha)), (sun_x, sun_y), sun_size + 5)
                pygame.draw.circle(self.screen, (int(255*sun_alpha), int(220*sun_alpha), int(100*sun_alpha)), (sun_x, sun_y), sun_size)
        else:  
            progress = self.time / 400 if self.time < 400 else (self.time - 2000) / 400 
            moon_x = int(WIDTH // 2 + 1100 * math.cos(progress * math.pi))
            moon_y = int(HEIGHT // 4 + 30)
            moon_alpha = 1.0
            if 'rain' in self.weather_type or 'sand' in self.weather_type:
                moon_alpha = max(0, 1.0 - (self.weather_intensity * 1.5))
            if moon_alpha > 0:
                pygame.draw.circle(self.screen, (int(220*moon_alpha), int(220*moon_alpha), int(200*moon_alpha)), (moon_x, moon_y), sun_size - 5)
                pygame.draw.circle(self.screen, (int(100*moon_alpha), int(100*moon_alpha), int(80*moon_alpha)), (moon_x - 10, moon_y - 5), 4)
                pygame.draw.circle(self.screen, (int(100*moon_alpha), int(100*moon_alpha), int(80*moon_alpha)), (moon_x + 8, moon_y + 8), 3)

    def draw_stars(self):
        if self.time < 600 or self.time > 1800:
            star_alpha = 1.0
            if 'rain' in self.weather_type or 'sand' in self.weather_type:
                star_alpha = max(0, 1.0 - (self.weather_intensity * 1.5))
            if star_alpha > 0:
                random.seed(42)  
                for _ in range(100):
                    brightness = int((200 + 55 * math.sin(self.time / 100)) * star_alpha) 
                    pygame.draw.circle(self.screen, (brightness, brightness, brightness), (random.randint(0, WIDTH), random.randint(0, HEIGHT // 2)), random.randint(1, 2))
                random.seed() 

    def draw_minimap(self):
        cell_size = self.minimap_size / MAP_SIZE
        pygame.draw.rect(self.screen, (20, 20, 20), (self.minimap_x, self.minimap_y, self.minimap_size + 4, self.minimap_size + 4))
        pygame.draw.rect(self.screen, (100, 100, 100), (self.minimap_x, self.minimap_y, self.minimap_size + 4, self.minimap_size + 4), 2)
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                tile_x, tile_y = self.minimap_x + 2 + x * cell_size, self.minimap_y + 2 + y * cell_size
                if self.fog_of_war[y][x]:
                    val = self.map[y][x]
                    if val == TileType.WALL_BRICK.value: pygame.draw.rect(self.screen, (100, 50, 50), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.WALL_STONE.value: pygame.draw.rect(self.screen, (80, 80, 80), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.WALL_WOOD.value: pygame.draw.rect(self.screen, (100, 60, 20), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.DOOR.value: pygame.draw.rect(self.screen, (255, 200, 50), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.TREE.value: pygame.draw.rect(self.screen, (34, 100, 34), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.DEAD_TREE.value: pygame.draw.rect(self.screen, (80, 70, 60), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.BUSH.value: pygame.draw.rect(self.screen, (20, 150, 50), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.ROCK.value: pygame.draw.rect(self.screen, (150, 150, 150), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.STANDING_TORCH.value: pygame.draw.rect(self.screen, (255, 140, 0), (tile_x, tile_y, cell_size, cell_size))
                    elif val == TileType.WALL_TORCH.value: pygame.draw.rect(self.screen, (200, 80, 20), (tile_x, tile_y, cell_size, cell_size))
                    else: pygame.draw.rect(self.screen, (50, 80, 50), (tile_x, tile_y, cell_size, cell_size))
                else: pygame.draw.rect(self.screen, (30, 30, 30), (tile_x, tile_y, cell_size, cell_size))
        px, py = self.minimap_x + 2 + (self.player_x / (MAP_SIZE * TILE_SIZE)) * self.minimap_size, self.minimap_y + 2 + (self.player_y / (MAP_SIZE * TILE_SIZE)) * self.minimap_size
        pygame.draw.circle(self.screen, (0, 255, 0), (int(px), int(py)), 3)

    def draw_ss2_bracket(self, rect, label):
        x, y, w, h = rect
        l, t = max(5, w//4), 2
        alpha = int(150 + 105 * math.sin(pygame.time.get_ticks() / 150))
        bracket_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        color_with_alpha = (255, 255, 255, alpha)
        pygame.draw.line(bracket_surf, color_with_alpha, (x, y), (x+l, y), t); pygame.draw.line(bracket_surf, color_with_alpha, (x, y), (x, y+l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (x+w, y), (x+w-l, y), t); pygame.draw.line(bracket_surf, color_with_alpha, (x+w, y), (x+w, y+l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (x, y+h), (x+l, y+h), t); pygame.draw.line(bracket_surf, color_with_alpha, (x, y+h), (x, y+h-l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (x+w, y+h), (x+w-l, y+h), t); pygame.draw.line(bracket_surf, color_with_alpha, (x+w, y+h), (x+w, y+h-l), t)
        self.screen.blit(bracket_surf, (0, 0))
        font = pygame.font.SysFont("georgia", 14, bold=True)
        text = f"[ {label} ]"
        self.screen.blit(font.render(text, True, (255, 255, 255)), (x + w//2 - font.render(text, True, (255, 255, 255)).get_width()//2, y - 20))

    def update(self):
        if self.attack_swing > 0:
            self.attack_swing -= 0.05
            if self.attack_swing <= 0: self.attack_swing = 0
        if self.level_complete:
            self.level_complete_timer -= 1
            return 
        if self.inventory.visible: return 
        self.action_bar.update()
        for proj in self.projectiles[:]:
            proj['x'] += math.cos(proj['angle']) * proj['speed']
            proj['y'] += math.sin(proj['angle']) * proj['speed']
            gx, gy = int(proj['x'] // TILE_SIZE), int(proj['y'] // TILE_SIZE)
            if 0 <= gx < MAP_SIZE and 0 <= gy < MAP_SIZE:
                if self.map[gy][gx] not in [TileType.EMPTY.value, TileType.TREE.value, TileType.STANDING_TORCH.value, TileType.DEAD_TREE.value, TileType.BUSH.value, TileType.ROCK.value]:
                    self.projectiles.remove(proj)
            else:
                self.projectiles.remove(proj)
        self.time = (self.time + 0.2) % 2400 
        self.ambient_light = self.get_smooth_ambient_light()
        self.global_flicker = 0.9 + 0.1 * math.sin(pygame.time.get_ticks() / 100.0) + random.uniform(-0.05, 0.05)
        self.update_fog_of_war()
        if self.consume_message_timer > 0: self.consume_message_timer -= 1
        self.manage_weather()
        if 'rain' in self.weather_type:
            self.wind_effect = math.sin(self.weather_timer * 0.03) * (2.5 if 'heavy' in self.weather_type else 0.8)
        elif 'sand' in self.weather_type:
            self.wind_effect = math.sin(self.weather_timer * 0.02) * 2.0
        else:
            self.wind_effect = 0
        for c in self.clouds: 
            c['x'] = (c['x'] + c['speed_mult'] * 0.3) % (WIDTH + 200)
            c['current_scale'] = c['scale'] * (1.0 + (self.weather_intensity * 1.5))
        if len(self.particles) > 0:
            for p in self.particles:
                p['z'] += p['speed'] + (2.0 if self.weather_type == 'rain_heavy' else 0)
                if p['z'] > 180: p['z'] = -180
                if 'sand' in self.weather_type or 'rain' in self.weather_type: 
                    p['wind_accel'] = self.wind_effect
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.hovered_interactable = None
        self.hovered_rect = None
        proj_plane_dist = (WIDTH / 2) / math.tan(FOV / 2)
        for door in self.doors:
            dist = math.hypot(self.player_x - door["x"], self.player_y - door["y"])
            if dist < 120: 
                dx, dy = door["x"] - self.player_x, door["y"] - self.player_y
                px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
                py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
                if px > 0.5:
                    sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                    size = max(20, int(WALL_HEIGHT_MULTIPLIER / px))
                    bracket_w = min(120, size // 2)
                    bracket_h = min(120, size // 2)
                    rect = pygame.Rect(sx - bracket_w//2, HEIGHT//2 - bracket_h//2, bracket_w, bracket_h)
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.hovered_interactable = {"type": "door", "door": door}
                        self.hovered_rect = rect
        item_names = {TileType.ITEM_DAGGER.value: "Sword", TileType.ITEM_KEY.value: "Brass Key", TileType.ITEM_HEALTH_POTION.value: "Health Potion", TileType.ITEM_FOOD.value: "Mana Potion", TileType.ITEM_ARTIFACT.value: "Mystic Artifact"}
        for item in self.world_items:
            dist = math.hypot(self.player_x - item['x'], self.player_y - item['y'])
            if dist < 120:
                dx, dy = item['x'] - self.player_x, item['y'] - self.player_y
                px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
                py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
                if px > 0.5:
                    sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                    sprite_h = max(1, int(WALL_HEIGHT_MULTIPLIER / (px + PARTICLE_EPSILON))) // 3
                    rect = pygame.Rect(sx - sprite_h//2, (HEIGHT//2) + sprite_h//2, sprite_h, sprite_h)
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.hovered_interactable = {"type": "item", "item": item, "name": item_names.get(item['id'], "Item")}
                        self.hovered_rect = rect

    def draw_weather(self):
        if self.weather_intensity <= 0: return
        if 'rain' in self.weather_type: color, particle_height = RAIN_COLOR, 12 if 'heavy' in self.weather_type else 8
        elif self.weather_type == 'snow': color, particle_height = SNOW_COLOR, 4
        elif 'sand' in self.weather_type: color, particle_height = DUST_COLOR, 6
        else: return
        for p in self.particles:
            dx, dy = p['x'] - self.player_x, p['y'] - self.player_y
            px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
            py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
            if px > 2:
                wind_offset = p.get('wind_accel', 0) * 2 if 'sand' in self.weather_type else 0
                sx = (py / px) * (WIDTH / (2 * math.tan(FOV/2))) + (WIDTH / 2) + wind_offset
                if 0 <= sx < WIDTH and 0 <= idx < NUM_RAYS and px < self.depth_buffer[idx]:
                    pygame.draw.rect(self.screen, color, (sx, (HEIGHT // 2) + (p['z'] * (240 / px)), 4, particle_height))
        if 'sand' in self.weather_type:
            overlay = pygame.Surface((WIDTH, HEIGHT)); overlay.set_alpha(int(150 * self.weather_intensity)); overlay.fill(DUST_COLOR)
            self.screen.blit(overlay, (0, 0))

    def draw_hud(self):
        pygame.draw.rect(self.screen, (30, 30, 30), (20, 20, 200, 20)); pygame.draw.rect(self.screen, (100, 255, 100), (20, 20, int(200 * (self.health / self.max_health)), 20)); pygame.draw.rect(self.screen, (150, 150, 150), (20, 20, 200, 20), 2)
        pygame.draw.rect(self.screen, (30, 30, 30), (20, 50, 200, 20)); pygame.draw.rect(self.screen, (100, 100, 255), (20, 50, int(200 * (self.mana / self.max_mana)), 20)); pygame.draw.rect(self.screen, (150, 150, 150), (20, 50, 200, 20), 2)
        font = pygame.font.SysFont("georgia", 16)
        self.screen.blit(font.render(f"HP: {self.health}/{self.max_health}", True, (255, 255, 255)), (25, 22)); self.screen.blit(font.render(f"Mana: {self.mana}/{self.max_mana}", True, (255, 255, 255)), (25, 52))
        if self.consume_message_timer > 0:
            font_msg = pygame.font.SysFont("georgia", 20, bold=True)
            msg_surf = font_msg.render(self.consume_message, True, (100, 255, 100))
            msg_rect = msg_surf.get_rect(center=(WIDTH // 2, HEIGHT - 50))
            self.screen.blit(font_msg.render(self.consume_message, True, (0, 0, 0)), (msg_rect.x + 2, msg_rect.y + 2))
            self.screen.blit(msg_surf, msg_rect)

    def draw(self):
        self.screen.fill(self.get_sky_color(), (0, 0, WIDTH, HEIGHT // 2))
        if not self.in_interior:
            self.draw_stars(); self.draw_sun_moon()
            for c in self.clouds:
                scaled_sprite = self.get_scaled_cloud_sprite(c['current_scale'])
                self.screen.blit(scaled_sprite, (int(c['x'] - scaled_sprite.get_width()/2), int(c['y'] - scaled_sprite.get_height()/2)))
        
        # Placeholder 3D rendering
        pygame.draw.rect(self.screen, (50, 100, 50), (0, HEIGHT//2, WIDTH, HEIGHT//2))
        
        for i in range(NUM_RAYS):
            angle = self.player_angle - FOV/2 + (FOV / NUM_RAYS) * i
            for depth in range(1, MAX_DEPTH, 10):
                x, y = self.player_x + math.cos(angle) * depth, self.player_y + math.sin(angle) * depth
                gx, gy = int(x / TILE_SIZE), int(y / TILE_SIZE)
                if not (0 <= gx < MAP_SIZE and 0 <= gy < MAP_SIZE) or self.map[gy][gx] != TileType.EMPTY.value:
                    wall_height = int(WALL_HEIGHT_MULTIPLIER / depth)
                    pygame.draw.line(self.screen, (100, 100, 100), (i * (WIDTH // NUM_RAYS), HEIGHT//2 - wall_height//2), (i * (WIDTH // NUM_RAYS), HEIGHT//2 + wall_height//2), WIDTH // NUM_RAYS)
                    break
        
        self.draw_weather()
        self.draw_minimap()
        self.draw_hud()
        
        if self.hovered_rect:
            self.draw_ss2_bracket(self.hovered_rect, self.hovered_interactable.get('name', 'Object'))
        
        if self.level_complete:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            font_massive = pygame.font.SysFont("georgia", 50, bold=True)
            text = font_massive.render("ARTIFACT RETRIEVED", True, (255, 215, 0))
            self.screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
        
        self.inventory.draw(self.screen, pygame.mouse.get_pos(), self.font)
        self.action_bar.draw(self.screen)

    def use_hotkey_action(self, slot):
        if slot["type"] != "magic": return
        if self.mana < slot.get("cost", 0):
            if self.sfx.get("error"): self.sfx["error"].play()
            self.consume_message = "Not enough mana!"
            self.consume_message_timer = 60
            return
        self.mana -= slot.get("cost", 0)
        if slot["name"] == "Fireball":
            if SFX_FIREBALL: SFX_FIREBALL.play()
            for _ in range(3):
                proj_angle = self.player_angle + random.uniform(-0.3, 0.3)
                self.projectiles.append({'x': self.player_x, 'y': self.player_y, 'angle': proj_angle, 'speed': 8})
            self.consume_message = "Fireball cast!"
            self.consume_message_timer = 60

    def run(self):
        if pygame.mixer.music.get_busy() == False:
            try: pygame.mixer.music.play(-1)
            except: pass
        while True:
            if self.level_complete and self.level_complete_timer <= 0:
                pygame.mixer.music.stop()
                if CH_WALK.get_busy(): CH_WALK.stop()
                if CH_RAIN.get_busy(): CH_RAIN.stop()
                return
                
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE): 
                    pygame.mixer.music.stop()
                    if CH_WALK.get_busy(): CH_WALK.stop()
                    if CH_RAIN.get_busy(): CH_RAIN.stop()
                    return
                    
                elif e.type == pygame.KEYDOWN and not self.level_complete:
                    if e.key == pygame.K_i: self.inventory.toggle()
                    for slot in self.action_bar.slots:
                        if e.key == slot["key"]:
                            self.use_hotkey_action(slot)

                elif e.type == pygame.MOUSEBUTTONDOWN and not self.level_complete:
                    clicked_ui = False
                    inv_idx = self.inventory.get_slot_at(pygame.mouse.get_pos())
                    if inv_idx is not None:
                        clicked_ui = True
                        item = self.inventory.slots[inv_idx]
                        if e.button == 1:
                            self.drag_item = item
                            self.drag_source = ("inv", inv_idx)
                        elif e.button == 3:
                            if item["type"] == "weapon":
                                for s in self.inventory.slots: 
                                    if s and s["type"] == "weapon": s["equipped"] = False
                                item["equipped"] = True
                                if self.sfx.get("use"): self.sfx["use"].play()
                            elif item["type"] in ["consumable", "potion"]:
                                self.health = min(self.max_health, self.health + item.get("health", 0))
                                self.mana = min(self.max_mana, self.mana + item.get("mana", 0))
                                item["qty"] -= 1
                                if item["qty"] <= 0: self.inventory.slots[inv_idx] = None
                                self.consume_message = f"Used {item['name']}!"
                                self.consume_message_timer = 60
                                if self.sfx.get("use"): self.sfx["use"].play()

                    elif not clicked_ui and e.button == 1:
                        if self.hovered_interactable:
                            if self.hovered_interactable["type"] == "door":
                                self.use_specific_door(self.hovered_interactable["door"])
                            elif self.hovered_interactable["type"] == "item":
                                item = self.hovered_interactable["item"]
                                if item['id'] == TileType.ITEM_ARTIFACT.value: 
                                    if SFX_PICKUP: SFX_PICKUP.play()
                                    self.level_complete = True
                                    self.level_complete_timer = 180 
                                    self.world_items.remove(item)
                                else:
                                    success = False
                                    if item['id'] == TileType.ITEM_DAGGER.value: success = self.inventory.add_item("Sword", 1, "weapon", "A sturdy blade.")
                                    elif item['id'] == TileType.ITEM_KEY.value: success = self.inventory.add_item("Brass Key", 1, "key", "Unlocks doors.")
                                    elif item['id'] == TileType.ITEM_HEALTH_POTION.value: success = self.inventory.add_item("Health Potion", 1, "consumable", "Restores 30 HP.", health=30, mana=0)
                                    elif item['id'] == TileType.ITEM_FOOD.value: success = self.inventory.add_item("Mana Potion", 1, "consumable", "Restores 30 Mana.", health=0, mana=30)
                                    
                                    if success:
                                        if SFX_PICKUP: SFX_PICKUP.play()
                                        self.consume_message = f"Picked up {self.hovered_interactable['name']}!"
                                        self.consume_message_timer = 120
                                        self.world_items.remove(item)
                                    else:
                                        if self.sfx.get("error"): self.sfx["error"].play()
                                        self.consume_message = "Inventory Full!"
                                        self.consume_message_timer = 120

            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
    game.run()
