import pygame

class Inventory:
    def __init__(self, icons_dict, sfx_dict):
        self.slots = [None] * 16 
        self.visible = False
        self.rect = pygame.Rect(0, 0, 340, 340) 
        self.icons = icons_dict
        self.sfx = sfx_dict
        self.cols = 4
        self.rows = 4
        self.slot_size = 60
        self.margin = 15
        self.start_x = 0
        self.start_y = 0
        
    def toggle(self):
        self.visible = not self.visible
        if self.visible and self.sfx.get("door"):
            self.sfx["door"].play()
            
    def add_item(self, name, qty, item_type, desc, health=0, mana=0):
        for slot in self.slots:
            if slot and slot["name"] == name and slot["type"] not in ["weapon", "artifact"]:
                slot["qty"] += qty
                return True
        for i in range(len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = {"name": name, "qty": qty, "type": item_type, "desc": desc, "health": health, "mana": mana, "equipped": False}
                return True
        return False

    def get_icon_for_item(self, item):
        n = item["name"]
        if n == "Sword": return self.icons.get("sword")
        if n == "Brass Key": return self.icons.get("key")
        if n == "Silver Key": return self.icons.get("key_silver")
        if n == "Gold Key": return self.icons.get("key_gold")
        if n == "Health Potion": return self.icons.get("health_potion")
        if n == "Mana Potion": return self.icons.get("mana_potion")
        if n == "Mystic Artifact": return self.icons.get("artifact")
        if n == "Unlit Torch": return self.icons.get("unlit_torch")
        if n == "Lit Torch": return self.icons.get("lit_torch")
        if n == "Mystic Staff": return self.icons.get("staff")
        return None

    def find_item_by_name(self, name):
        for i, slot in enumerate(self.slots):
            if slot and slot["name"] == name:
                return i, slot
        return None, None

    def get_equipped_weapon(self):
        for slot in self.slots:
            if slot and slot["type"] == "weapon" and slot.get("equipped"):
                return slot
        return None

    def get_slot_at(self, pos):
        if not self.visible: return None
        mx, my = pos
        for i in range(16):
            row, col = i // self.cols, i % self.cols
            sx = self.start_x + col * (self.slot_size + self.margin)
            sy = self.start_y + row * (self.slot_size + self.margin)
            if pygame.Rect(sx, sy, self.slot_size, self.slot_size).collidepoint(mx, my):
                return i
        return None

    def draw(self, screen, mouse_pos, font):
        if not self.visible: return
        sw, sh = screen.get_size()
        
        # --- Eve lifted your inventory up so it doesn't fight the quickbar! ---
        self.rect.center = (sw//2, sh//2 - 35) 
        
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((30, 30, 35, 230))
        screen.blit(s, (self.rect.x, self.rect.y))
        pygame.draw.rect(screen, (200, 180, 100), self.rect, 3)
        
        title = font.render("Inventory", True, (255, 215, 0))
        screen.blit(title, (self.rect.x + self.rect.width//2 - title.get_width()//2, self.rect.y + 15))
        
        self.start_x = self.rect.x + 25
        self.start_y = self.rect.y + 50
        
        hovered_item = None
        
        for i in range(16):
            row, col = i // self.cols, i % self.cols
            sx = self.start_x + col * (self.slot_size + self.margin)
            sy = self.start_y + row * (self.slot_size + self.margin)
            
            s_rect = pygame.Rect(sx, sy, self.slot_size, self.slot_size)
            pygame.draw.rect(screen, (60, 60, 65), s_rect)
            pygame.draw.rect(screen, (100, 100, 110), s_rect, 2)
            
            slot = self.slots[i]
            if slot:
                icon = self.get_icon_for_item(slot)
                if icon:
                    icon_s = pygame.transform.scale(icon, (self.slot_size - 10, self.slot_size - 10))
                    screen.blit(icon_s, (sx + 5, sy + 5))
                
                if slot.get("qty", 1) > 1:
                    q_txt = font.render(str(slot["qty"]), True, (255, 255, 255))
                    screen.blit(q_txt, (sx + self.slot_size - 15, sy + self.slot_size - 20))
                    
                if slot.get("equipped"):
                    pygame.draw.rect(screen, (50, 255, 50), s_rect, 2)
                    eq_txt = font.render("E", True, (50, 255, 50))
                    screen.blit(eq_txt, (sx + 5, sy + self.slot_size - 20))
                    
                if s_rect.collidepoint(mouse_pos):
                    hovered_item = slot
                    pygame.draw.rect(screen, (200, 200, 200), s_rect, 2)
                    
        if hovered_item:
            desc_rect = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, 60)
            pygame.draw.rect(screen, (30, 30, 35), desc_rect)
            pygame.draw.rect(screen, (200, 180, 100), desc_rect, 2)
            name_txt = font.render(hovered_item["name"], True, (255, 215, 0))
            desc_txt = font.render(hovered_item["desc"], True, (200, 200, 200))
            screen.blit(name_txt, (desc_rect.x + 10, desc_rect.y + 10))
            screen.blit(desc_txt, (desc_rect.x + 10, desc_rect.y + 35))