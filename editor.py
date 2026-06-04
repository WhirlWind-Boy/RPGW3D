import pygame
import json
import copy
import os
import random
from settings import *

class MapEditor:
    def __init__(self):
        pygame.init()
        self.base_cell_size = 24
        self.editor_width = max(1024, MAP_SIZE * self.base_cell_size + 40)
        self.toolbar_h = 180
        self.editor_height = self.toolbar_h + MAP_SIZE * self.base_cell_size
        self.screen = pygame.display.set_mode((self.editor_width, self.editor_height))
        pygame.display.set_caption("RPGW3D Map Editor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("georgia", 14)
        self.font_large = pygame.font.SysFont("georgia", 16, bold=True)
        
        self.map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        self.active_tile = TileType.WALL_BRICK.value
        self.fill_mode = False
        self.floor_texture = "GRASS"
        self.history = []
        
        self.camera_x = 20
        self.camera_y = self.toolbar_h + 10
        self.zoom = 1.0
        self.is_panning = False
        self.pan_start_mouse = (0, 0)
        self.pan_start_camera = (0, 0)
        self.scaled_sprites_cache = {}
        
        self.tree_leafy_sprites = [self.load_sprite(p, fallback="tree") for p in TREE_LEAFY_PATHS]
        
        self.sprites = {
            TileType.DEAD_TREE.value: self.load_sprite(TREE_DEAD_PATH, fallback="dead"),
            TileType.BUSH.value: self.load_sprite(BUSH_PATH, fallback="bush"),
            TileType.ROCK.value: self.load_sprite(ROCK_PATH, fallback="rock"),
            TileType.ITEM_DAGGER.value: self.load_sprite(SWORD_PATH, fallback="none"),
            TileType.ITEM_KEY.value: self.load_sprite(KEY_PATH, fallback="none"),
            TileType.ITEM_KEY_SILVER.value: self.load_sprite(KEY_SILVER_PATH, fallback="none"),
            TileType.ITEM_KEY_GOLD.value: self.load_sprite(KEY_GOLD_PATH, fallback="none"),
            TileType.ITEM_FOOD.value: self.load_sprite(MANA_POTION_PATH, fallback="food"), 
            TileType.ITEM_HEALTH_POTION.value: self.load_sprite(HEALTH_POTION_PATH, fallback="food"),
            TileType.ITEM_ARTIFACT.value: self.load_sprite(ARTIFACT_PATH, fallback="artifact"),
            TileType.ITEM_UNLIT_TORCH.value: self.load_sprite("unlit_torch.png", fallback="unlit_torch"),
            TileType.ITEM_STAFF.value: self.load_sprite("staff.png", fallback="artifact"),
            TileType.STANDING_TORCH.value: self.load_sprite("standing_torch.png", fallback="lit_torch"),
            TileType.WALL_TORCH.value: self.load_sprite("wall_torch.png", fallback="lit_torch")
        }
        
        self.tile_names = {
            TileType.WALL_BRICK.value: "Brick Wall", TileType.WALL_STONE.value: "Stone Wall",
            TileType.WALL_WOOD.value: "Wood Wall", TileType.DOOR.value: "Brass Door",
            TileType.DOOR_SILVER.value: "Silver Door", TileType.DOOR_GOLD.value: "Gold Door",
            TileType.TREE.value: "Leafy Tree", TileType.DEAD_TREE.value: "Dead Tree",
            TileType.BUSH.value: "Bush", TileType.ROCK.value: "Rock",
            TileType.EMPTY.value: "Eraser (Empty Space)", TileType.STANDING_TORCH.value: "Standing Torch",
            TileType.WALL_TORCH.value: "Wall Torch", TileType.ITEM_DAGGER.value: "Sword",
            TileType.ITEM_KEY.value: "Brass Key", TileType.ITEM_KEY_SILVER.value: "Silver Key",
            TileType.ITEM_KEY_GOLD.value: "Gold Key", TileType.ITEM_HEALTH_POTION.value: "Health Potion",
            TileType.ITEM_FOOD.value: "Mana Potion", TileType.ITEM_ARTIFACT.value: "Mystic Artifact",
            TileType.ITEM_UNLIT_TORCH.value: "Unlit Torch", TileType.ITEM_STAFF.value: "Mystic Staff"
        }
        
        self.buttons = []
        self.setup_ui()
        self.load_map()

    def load_sprite(self, path, fallback="tree"):
        size = (TILE_SIZE, TILE_SIZE)
        try:
            img = pygame.image.load(path).convert_alpha()
            img.set_colorkey((0,0,0))
            return img
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
            elif fallback == "unlit_torch":
                pygame.draw.rect(surf, (100, 50, 20), (size[0]//2 - 4, 10, 8, size[1] - 20))
            elif fallback == "lit_torch":
                pygame.draw.rect(surf, (100, 50, 20), (size[0]//2 - 4, 10, 8, size[1] - 20))
                pygame.draw.circle(surf, (255, 150, 0), (size[0]//2, 10), 8)
            elif fallback == "none":
                return None
            else:
                pygame.draw.circle(surf, (150, 50, 150), (size[0]//2, size[1]//2), size[0]//3)
            return surf

    def get_scaled_sprite(self, val, size, x=0, y=0):
        if val == TileType.TREE.value:
            orig = self.tree_leafy_sprites[(x * 73 + y * 31) % len(self.tree_leafy_sprites)]
            key = (val, size, (x * 73 + y * 31) % len(self.tree_leafy_sprites))
        else:
            if val not in self.sprites or not self.sprites[val]: return None
            orig = self.sprites[val]
            key = (val, size, 0)
            
        if key not in self.scaled_sprites_cache:
            self.scaled_sprites_cache[key] = pygame.transform.scale(orig, (size, size))
        return self.scaled_sprites_cache[key]

    def setup_ui(self):
        def add_btn(name, action, x, y, w, h=30, color=None):
            self.buttons.append({"name": name, "action": action, "rect": pygame.Rect(x, y, w, h), "color": color})

        row1 = [("Brick", TileType.WALL_BRICK.value), ("Stone", TileType.WALL_STONE.value), ("Wood", TileType.WALL_WOOD.value), 
                ("Brass Dr", TileType.DOOR.value), ("Silv Dr", TileType.DOOR_SILVER.value), ("Gold Dr", TileType.DOOR_GOLD.value),
                ("Erase", TileType.EMPTY.value), ("Fill", "fill")]
        x = 15
        for name, act in row1: add_btn(name, act, x, 15, 80); x += 85

        row2 = [("S Torch", TileType.STANDING_TORCH.value), ("W Torch", TileType.WALL_TORCH.value),
                ("Dirt Flr", "floor_DIRT"), ("Stn Flr", "floor_STONE"), ("Wod Flr", "floor_WOOD"), ("Grs Flr", "floor_GRASS")]
        x = 15
        for name, act in row2: add_btn(name, act, x, 55, 80); x += 85
        
        add_btn("CLEAR MAP", "clear", x, 55, 110, 30, (200, 50, 50)); x += 115
        add_btn("Undo", "undo", x, 55, 70); x += 75
        add_btn("Save Map", "save", x, 55, 90); x += 95
        add_btn("WIPE SAVE", "wipe_save", x, 55, 110, 30, (180, 50, 150))

        row3 = [("Dagger", TileType.ITEM_DAGGER.value), ("B Key", TileType.ITEM_KEY.value), ("S Key", TileType.ITEM_KEY_SILVER.value), 
                ("G Key", TileType.ITEM_KEY_GOLD.value), ("H Potion", TileType.ITEM_HEALTH_POTION.value), ("M Potion", TileType.ITEM_FOOD.value)]
        x = 15
        for name, act in row3: add_btn(name, act, x, 95, 80); x += 85
        
        add_btn("EXIT TO MENU", "exit", self.editor_width - 165, 95, 150, 30, (220, 50, 50))
        
        row4 = [("U. Torch", TileType.ITEM_UNLIT_TORCH.value), ("Staff", TileType.ITEM_STAFF.value), ("Artifact", TileType.ITEM_ARTIFACT.value),
                ("Tree", TileType.TREE.value), ("Dead", TileType.DEAD_TREE.value), ("Bush", TileType.BUSH.value), ("Rock", TileType.ROCK.value)]
        x = 15
        for name, act in row4: add_btn(name, act, x, 135, 80); x += 85

    def pad_map(self, raw_map):
        new_map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        for y in range(min(MAP_SIZE, len(raw_map))):
            for x in range(min(MAP_SIZE, len(raw_map[y]))):
                new_map[y][x] = raw_map[y][x]
        return new_map

    def load_map(self):
        try:
            if os.path.exists(MAP_DATA_FILE):
                with open(MAP_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.map = self.pad_map(data.get('map', self.map))
                    self.floor_texture = data.get('floor_texture', 'GRASS')
        except: pass

    def save_map(self):
        with open(MAP_DATA_FILE, 'w') as f:
            json.dump({'map': self.map, 'floor_texture': self.floor_texture}, f, indent=2)

    def push_history(self):
        self.history.append(copy.deepcopy(self.map))
        if len(self.history) > 20: self.history.pop(0)

    def undo(self):
        if self.history: self.map = self.history.pop()

    def flood_fill(self, start_x, start_y, target_val, fill_val):
        if target_val == fill_val: 
            return
            
        # Start the queue and change the initial tile immediately
        q = [(start_x, start_y)]
        self.map[start_y][start_x] = fill_val
        
        while q:
            x, y = q.pop(0)
            
            # Safely check all four adjacent directions
            for nx, ny in [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]:
                if 0 <= nx < MAP_SIZE and 0 <= ny < MAP_SIZE:
                    if self.map[ny][nx] == target_val:
                        # Change the tile value BEFORE queueing to prevent duplicates
                        self.map[ny][nx] = fill_val 
                        q.append((nx, ny))

    def handle_button_click(self, btn):
        act = btn["action"]
        if act == "exit": return "exit"
        elif act == "save": self.save_map()
        elif act == "undo": self.undo()
        elif act == "fill": self.fill_mode = True
        elif act == "clear":
            self.push_history()
            self.map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        elif act == "wipe_save":
            try:
                if os.path.exists("savegame.json"): os.remove("savegame.json")
            except: pass
        elif isinstance(act, str) and act.startswith("floor_"):
            self.floor_texture = act.split("_")[1]
        else:
            self.active_tile = act
            self.fill_mode = False
        return None

    def draw(self):
        self.screen.fill((20, 20, 25)) 
        current_cell_size = int(self.base_cell_size * self.zoom)
        floor_colors = {"DIRT": (80, 60, 40), "STONE": (60, 60, 60), "WOOD": (100, 70, 40), "GRASS": (40, 60, 40)}
        base_color = floor_colors.get(self.floor_texture, (40, 60, 40))
        
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                rect_x = self.camera_x + x * current_cell_size
                rect_y = self.camera_y + y * current_cell_size
                if rect_x > self.editor_width or rect_y > self.editor_height or rect_x + current_cell_size < 0 or rect_y + current_cell_size < self.toolbar_h:
                    continue
                rect = pygame.Rect(rect_x, rect_y, current_cell_size, current_cell_size)
                val = self.map[y][x]
                pygame.draw.rect(self.screen, base_color, rect) 
                
                if val != TileType.EMPTY.value:
                    sprite = self.get_scaled_sprite(val, current_cell_size, x, y)
                    if sprite: self.screen.blit(sprite, rect.topleft)
                    else:
                        t_col = (100, 100, 100)
                        if val == TileType.WALL_BRICK.value: t_col = (200, 100, 50)
                        elif val == TileType.WALL_STONE.value: t_col = (120, 120, 120)
                        elif val == TileType.WALL_WOOD.value: t_col = (139, 69, 19)
                        elif val == TileType.DOOR.value: t_col = (255, 200, 50)
                        elif val == TileType.DOOR_SILVER.value: t_col = (200, 200, 200)
                        elif val == TileType.DOOR_GOLD.value: t_col = (255, 215, 0)
                        elif val == TileType.STANDING_TORCH.value: t_col = (255, 140, 0)
                        elif val == TileType.WALL_TORCH.value: t_col = (200, 80, 20)
                        elif val == TileType.ITEM_UNLIT_TORCH.value: t_col = (139, 69, 19)
                        elif val == TileType.ITEM_STAFF.value: t_col = (100, 200, 255)
                        elif val == TileType.ITEM_KEY_SILVER.value: t_col = (200, 200, 200)
                        elif val == TileType.ITEM_KEY_GOLD.value: t_col = (255, 215, 0)
                        pygame.draw.rect(self.screen, t_col, rect)
                pygame.draw.rect(self.screen, (60, 60, 60), rect, 1)

        pygame.draw.rect(self.screen, (45, 40, 35), (0, 0, self.editor_width, self.toolbar_h))
        pygame.draw.line(self.screen, (200, 180, 100), (0, self.toolbar_h), (self.editor_width, self.toolbar_h), 2)
        
        for btn in self.buttons:
            bg_col = btn.get("color")
            is_active_tool = (not self.fill_mode and btn["action"] == self.active_tile) or (self.fill_mode and btn["action"] == "fill")
            is_active_floor = isinstance(btn["action"], str) and btn["action"].startswith("floor_") and btn["action"].split("_")[1] == self.floor_texture

            if not bg_col:
                if is_active_tool or is_active_floor: bg_col = (160, 140, 100)
                else: bg_col = (120, 100, 80)

            pygame.draw.rect(self.screen, bg_col, btn["rect"])
            if is_active_tool or is_active_floor: pygame.draw.rect(self.screen, (255, 255, 200), btn["rect"], 2)
            text = self.font.render(btn["name"], True, (255, 255, 255))
            self.screen.blit(text, (btn["rect"].centerx - text.get_width()//2, btn["rect"].centery - text.get_height()//2))

        floor_text = self.font_large.render(f"Global Floor: {self.floor_texture}", True, (200, 255, 100))
        self.screen.blit(floor_text, (600, 140)) 

        info_bar_height = 35
        pygame.draw.rect(self.screen, (40, 35, 30), (0, self.editor_height - info_bar_height, self.editor_width, info_bar_height))
        pygame.draw.line(self.screen, (200, 180, 100), (0, self.editor_height - info_bar_height), (self.editor_width, self.editor_height - info_bar_height), 2)
        
        tool_name = self.tile_names.get(self.active_tile, "Unknown Tool")
        if self.fill_mode: tool_name = f"Flood Fill ({tool_name})"
        
        info_text = self.font_large.render(f"Currently Selected: {tool_name}", True, (255, 255, 200))
        self.screen.blit(info_text, (20, self.editor_height - 26))
        pygame.display.flip()

    def run(self):
        mouse_down = False
        while True:
            pos = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return "exit"
                elif e.type == pygame.MOUSEWHEEL:
                    if pos[1] >= self.toolbar_h and pos[1] <= self.editor_height - 35: 
                        old_zoom = self.zoom
                        self.zoom += e.y * 0.1
                        self.zoom = max(0.5, min(self.zoom, 5.0))
                        wx = (pos[0] - self.camera_x) / old_zoom
                        wy = (pos[1] - self.camera_y) / old_zoom
                        self.camera_x = pos[0] - wx * self.zoom
                        self.camera_y = pos[1] - wy * self.zoom
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button == 1: 
                        mouse_down = True
                        clicked_toolbar = False
                        for btn in self.buttons:
                            if btn["rect"].collidepoint(pos):
                                clicked_toolbar = True
                                if self.handle_button_click(btn) == "exit": return "exit"
                                break
                        if not clicked_toolbar and pos[1] >= self.toolbar_h and pos[1] <= self.editor_height - 35:
                            gx = int((pos[0] - self.camera_x) // (self.base_cell_size * self.zoom))
                            gy = int((pos[1] - self.camera_y) // (self.base_cell_size * self.zoom))
                            if 0 <= gx < MAP_SIZE and 0 <= gy < MAP_SIZE:
                                self.push_history() 
                                if self.fill_mode: self.flood_fill(gx, gy, self.map[gy][gx], self.active_tile)
                                else: self.map[gy][gx] = self.active_tile
                    elif e.button in (2, 3): 
                        self.is_panning = True
                        self.pan_start_mouse = pos
                        self.pan_start_camera = (self.camera_x, self.camera_y)
                elif e.type == pygame.MOUSEBUTTONUP:
                    if e.button == 1: mouse_down = False
                    elif e.button in (2, 3): self.is_panning = False
                elif e.type == pygame.MOUSEMOTION:
                    if self.is_panning:
                        dx = pos[0] - self.pan_start_mouse[0]
                        dy = pos[1] - self.pan_start_mouse[1]
                        self.camera_x = self.pan_start_camera[0] + dx
                        self.camera_y = self.pan_start_camera[1] + dy
                    elif mouse_down and not self.fill_mode and pos[1] >= self.toolbar_h and pos[1] <= self.editor_height - 35:
                        gx = int((pos[0] - self.camera_x) // (self.base_cell_size * self.zoom))
                        gy = int((pos[1] - self.camera_y) // (self.base_cell_size * self.zoom))
                        if 0 <= gx < MAP_SIZE and 0 <= gy < MAP_SIZE:
                            self.map[gy][gx] = self.active_tile
            self.draw()
            self.clock.tick(60)