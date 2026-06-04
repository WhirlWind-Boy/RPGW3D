# RPGW3D Engine

A 3D RPG game engine built with Python and Pygame, featuring raycasting rendering, inventory system, and dynamic weather.

## Features
- **3D Raycasting Engine** - First-person perspective rendering
- **Inventory System** - Pick up and manage items
- **Action Bar** - Quick access spells and abilities (Hotkeys 1-6)
- **Dynamic Weather** - Rain, snow, sand storms
- **Dungeons & Exploration** - Multiple maps to explore
- **Day/Night Cycle** - Beautiful sky transitions
- **Minimap** - Fog of war system

## Installation

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| **W/A/S/D** | Move & Rotate |
| **I** | Toggle Inventory |
| **1-6** | Hotkeys (Spells/Items) |
| **Mouse Click** | Interact with world/inventory |
| **Right Click** | Equip items |
| **ESC** | Quit Game |

## Game Objective

Explore the world, navigate through dungeons, and find the **Mystic Artifact** to complete the level!

## File Structure

```
RPGW3D/
├── main.py              # Main game loop
├── settings.py          # Game configuration
├── inventory.py         # Inventory management
├── ui.py               # UI components (ActionBar)
├── engine.py           # Rendering engine (placeholder)
├── editor.py           # Map editor
└── README.md           # This file
```

## Dependencies

- **pygame** - Game library for rendering and input

## Notes

- Asset files (PNG images, MP3 audio) are optional - the game generates procedural graphics if missing
- The game auto-generates maps if no `map_data.json` is found
- All textures and sprites are procedurally generated as fallbacks

## TODO

- [ ] Add fullscreen mode option
- [ ] Implement enemy AI
- [ ] Add more spell types
- [ ] Improve raycasting performance
- [ ] Save/Load game state
