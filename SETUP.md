# Quick Start Guide

## Step 1: Install Python 3.9+

Download from: https://www.python.org/downloads/

## Step 2: Clone and Install Dependencies

```bash
git clone https://github.com/WhirlWind-Boy/RPGW3D.git
cd RPGW3D
pip install -r requirements.txt
```

## Step 3: Run the Game

```bash
python main.py
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'pygame'"

```bash
pip install pygame --upgrade
```

### "ImportError: cannot import name 'Inventory' from 'inventory'"

Make sure all `.py` files are in the same directory as `main.py`.

### Game runs but appears black/empty

This is normal on first run - wait 2-3 seconds for the game to generate assets.

### Performance issues

Try adjusting in `settings.py`:
- Reduce `NUM_RAYS` from 120 to 60
- Reduce `CLOUD_LAYERS` from 3 to 1
- Set `WEATHER_INTENSITY` to lower values

## Game Tips

1. **Find the Artifact** - Your goal is to reach the Mystic Artifact
2. **Manage Inventory** - Press I to open your inventory (max 16 items)
3. **Use Hotkeys** - Press 2 to cast Fireball (costs 10 mana)
4. **Explore Dungeons** - Click on green doors to enter dungeons
5. **Keys Required** - You'll need brass keys to enter certain dungeons

## Controls Reminder

- **WASD** - Move
- **Mouse** - Look around / Interact
- **I** - Inventory
- **1-6** - Action bar hotkeys
- **ESC** - Quit
