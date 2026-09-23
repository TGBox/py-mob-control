"""Game configuration constants, color definitions, and tuning parameters for py-mob-control."""

import pygame

# Logical battlefield dimensions (coordinates used for physics and collision)
VIRTUAL_WIDTH: int = 560
VIRTUAL_HEIGHT: int = 880

# Default desktop window dimensions
DEFAULT_WINDOW_WIDTH: int = 1440
DEFAULT_WINDOW_HEIGHT: int = 900
TARGET_FPS: int = 60

# Physics and bounds
TRACK_Y_PLAYER: float = 820.0
TRACK_Y_ENEMY: float = 90.0
TRACK_MARGIN_X: float = 30.0

# Mob Properties
DEFAULT_MOB_SPEED: float = 230.0
DEFAULT_MOB_RADIUS: float = 9.0
DEFAULT_CHAMPION_RADIUS: float = 22.0
DEFAULT_CHAMPION_HP: int = 40
CHAMPION_CHARGE_REQUIRED: int = 80  # mobs shot to charge ultimate

# Color Palette - Sleek, vibrant modern arcade look
COLOR_BG_DARK = (15, 18, 28)
COLOR_BG_SIDEBAR = (22, 26, 40)
COLOR_BG_SIDEBAR_CARD = (30, 36, 56)
COLOR_BORDER = (45, 55, 85)
COLOR_TEXT_PRIMARY = (245, 248, 255)
COLOR_TEXT_MUTED = (140, 155, 185)
COLOR_ACCENT_GOLD = (255, 195, 30)
COLOR_ACCENT_CYAN = (40, 220, 255)

# Faction Colors
COLOR_PLAYER_PRIMARY = (30, 144, 255)       # Electric Dodger Blue
COLOR_PLAYER_SECONDARY = (90, 200, 255)     # Highlight Blue
COLOR_PLAYER_CHAMPION = (0, 80, 220)        # Deep Royal Blue
COLOR_PLAYER_GLOW = (50, 170, 255, 90)

COLOR_ENEMY_PRIMARY = (255, 55, 75)         # Neon Crimson
COLOR_ENEMY_SECONDARY = (255, 130, 140)     # Highlight Red
COLOR_ENEMY_CHAMPION = (180, 20, 45)        # Deep Crimson
COLOR_ENEMY_GLOW = (255, 60, 80, 90)

# Multiplier Gate Colors
COLOR_GATE_ADD = (50, 205, 110)             # Emerald Green (+N)
COLOR_GATE_MULTIPLY = (20, 180, 255)        # Vibrant Azure (xN)
COLOR_GATE_SUBTRACT = (255, 120, 40)        # Orange-Red (-N)
COLOR_GATE_DIVIDE = (220, 40, 60)           # Dark Red (/N)
COLOR_GATE_SPEED = (255, 215, 0)            # Gold (Speed)

# Base & Brick Colors
COLOR_BRICK_BASE = (240, 140, 40)
COLOR_BRICK_CRACKED = (200, 110, 30)
COLOR_BRICK_GOLD = (255, 210, 60)

# Controls Cheatsheet
KEY_LEFT = [pygame.K_a, pygame.K_LEFT]
KEY_RIGHT = [pygame.K_d, pygame.K_RIGHT]
KEY_FIRE = [pygame.K_SPACE]
KEY_CHAMPION = [pygame.K_q, pygame.K_e, pygame.K_1, pygame.K_2]
KEY_FULLSCREEN = [pygame.K_F11]
KEY_MUTE = [pygame.K_m]
KEY_PAUSE = [pygame.K_ESCAPE, pygame.K_p]
