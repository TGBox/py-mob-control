"""Interactive Headquarters and Shop scene for upgrading combat stats and town buildings."""

from typing import List, Optional, Tuple, Dict, Any
import pygame

from py_mob_control.config import (
    COLOR_BG_DARK,
    COLOR_BG_SIDEBAR,
    COLOR_BG_SIDEBAR_CARD,
    COLOR_BORDER,
    COLOR_ACCENT_GOLD,
    COLOR_ACCENT_CYAN,
    COLOR_BRICK_BASE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_PLAYER_PRIMARY,
)
from py_mob_control.engine.display_manager import DisplayManager
from py_mob_control.engine.input_manager import InputManager
from py_mob_control.audio.audio_manager import AudioManager
from .save_manager import SaveManager
from .upgrade_system import UpgradeSystem


class Button:
    """Simple UI Button with hover effect and click detection."""

    def __init__(self, rect: pygame.Rect, text: str, color: Tuple[int, int, int] = COLOR_ACCENT_CYAN) -> None:
        self.rect = rect
        self.text = text
        self.color = color
        self.is_hovered = False

    def update(self, mouse_pos: Tuple[int, int]) -> None:
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, enabled: bool = True) -> None:
        bg_col = self.color if enabled else (50, 55, 70)
        if enabled and self.is_hovered:
            # Brighten on hover
            bg_col = (min(255, bg_col[0] + 30), min(255, bg_col[1] + 30), min(255, bg_col[2] + 30))

        pygame.draw.rect(surface, bg_col, self.rect, border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255) if self.is_hovered else COLOR_BORDER, self.rect, 1, border_radius=6)

        text_col = (10, 15, 25) if enabled else (140, 140, 150)
        t_surf = font.render(self.text, True, text_col)
        t_rect = t_surf.get_rect(center=self.rect.center)
        surface.blit(t_surf, t_rect)


class ShopScene:
    """Headquarters scene where player upgrades combat stats and expands town buildings."""

    def __init__(
        self,
        save_mgr: SaveManager,
        upgrade_sys: UpgradeSystem,
        display_mgr: DisplayManager,
        audio_mgr: AudioManager,
    ) -> None:
        self.save_mgr = save_mgr
        self.upgrade_sys = upgrade_sys
        self.display_mgr = display_mgr
        self.audio_mgr = audio_mgr

        self.buttons: Dict[str, Button] = {}

    def update(self, dt: float, input_mgr: InputManager) -> Optional[str]:
        """Process clicks and keyboard shortcuts. Returns 'BATTLE' when player launches level."""
        self.audio_mgr.update(dt)

        mouse_pos = input_mgr.mouse_screen_pos

        # Update button hover states
        for btn in self.buttons.values():
            btn.update(mouse_pos)

        # Handle mouse clicks
        if input_mgr.mouse_clicked_this_frame:
            # Check Play button
            if "play" in self.buttons and self.buttons["play"].rect.collidepoint(mouse_pos):
                self.audio_mgr.play("mob_pop")
                return "BATTLE"

            # Check Combat upgrades
            if "fire_rate" in self.buttons and self.buttons["fire_rate"].rect.collidepoint(mouse_pos):
                if self.upgrade_sys.upgrade_fire_rate():
                    self.audio_mgr.play("coin")

            if "mob_speed" in self.buttons and self.buttons["mob_speed"].rect.collidepoint(mouse_pos):
                if self.upgrade_sys.upgrade_mob_speed():
                    self.audio_mgr.play("coin")

            if "champion" in self.buttons and self.buttons["champion"].rect.collidepoint(mouse_pos):
                if self.upgrade_sys.upgrade_champion():
                    self.audio_mgr.play("coin")

            # Check Town upgrades
            if "town_hall" in self.buttons and self.buttons["town_hall"].rect.collidepoint(mouse_pos):
                if self.upgrade_sys.upgrade_town_hall():
                    self.audio_mgr.play("brick_chip")

            if "brick_factory" in self.buttons and self.buttons["brick_factory"].rect.collidepoint(mouse_pos):
                if self.upgrade_sys.upgrade_brick_factory():
                    self.audio_mgr.play("brick_chip")

        # Keyboard shortcuts
        if input_mgr.is_key_just_pressed([pygame.K_SPACE, pygame.K_RETURN]):
            self.audio_mgr.play("mob_pop")
            return "BATTLE"

        if input_mgr.is_key_just_pressed([pygame.K_1]):
            if self.upgrade_sys.upgrade_fire_rate():
                self.audio_mgr.play("coin")
        elif input_mgr.is_key_just_pressed([pygame.K_2]):
            if self.upgrade_sys.upgrade_mob_speed():
                self.audio_mgr.play("coin")
        elif input_mgr.is_key_just_pressed([pygame.K_3]):
            if self.upgrade_sys.upgrade_champion():
                self.audio_mgr.play("coin")
        elif input_mgr.is_key_just_pressed([pygame.K_4]):
            if self.upgrade_sys.upgrade_town_hall():
                self.audio_mgr.play("brick_chip")
        elif input_mgr.is_key_just_pressed([pygame.K_5]):
            if self.upgrade_sys.upgrade_brick_factory():
                self.audio_mgr.play("brick_chip")

        return None

    def draw(self) -> None:
        """Render modern cyberpunk dashboard layout across the window."""
        screen = self.display_mgr.screen
        screen.fill(COLOR_BG_DARK)

        w = self.display_mgr.window_width
        h = self.display_mgr.window_height

        # 1. Top Header Banner (Currency Vault & Title)
        header_h = 75
        header_rect = pygame.Rect(20, 20, w - 40, header_h)
        pygame.draw.rect(screen, COLOR_BG_SIDEBAR, header_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_BORDER, header_rect, 1, border_radius=8)

        # Title
        title_surf = self.display_mgr.font_title.render("MOB CONTROL - COMMAND HEADQUARTERS", True, COLOR_TEXT_PRIMARY)
        screen.blit(title_surf, (header_rect.left + 24, header_rect.top + 20))

        # Currency Badges on the right of the header
        coins = self.save_mgr.data.get("coins", 0)
        bricks = self.save_mgr.data.get("bricks", 0)

        badge_w = 170
        coin_badge = pygame.Rect(header_rect.right - (badge_w * 2) - 30, header_rect.top + 16, badge_w, 42)
        brick_badge = pygame.Rect(header_rect.right - badge_w - 16, header_rect.top + 16, badge_w, 42)

        # Coin badge
        pygame.draw.rect(screen, COLOR_BG_SIDEBAR_CARD, coin_badge, border_radius=6)
        pygame.draw.rect(screen, COLOR_ACCENT_GOLD, coin_badge, 1, border_radius=6)
        c_text = self.display_mgr.font_body.render(f"Coins: {coins}", True, COLOR_ACCENT_GOLD)
        screen.blit(c_text, c_text.get_rect(center=coin_badge.center))

        # Brick badge
        pygame.draw.rect(screen, COLOR_BG_SIDEBAR_CARD, brick_badge, border_radius=6)
        pygame.draw.rect(screen, COLOR_BRICK_BASE, brick_badge, 1, border_radius=6)
        b_text = self.display_mgr.font_body.render(f"Bricks: {bricks}", True, COLOR_BRICK_BASE)
        screen.blit(b_text, b_text.get_rect(center=brick_badge.center))

        # 2. Main Columns: Column 1 = Combat Upgrades | Column 2 = Town Construction
        content_y = header_rect.bottom + 20
        bottom_bar_h = 90
        available_content_h = h - content_y - bottom_bar_h - 20
        col_w = (w - 60) // 2

        col1_rect = pygame.Rect(20, content_y, col_w, available_content_h)
        col2_rect = pygame.Rect(col1_rect.right + 20, content_y, col_w, available_content_h)

        pygame.draw.rect(screen, COLOR_BG_SIDEBAR, col1_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_BORDER, col1_rect, 1, border_radius=8)

        pygame.draw.rect(screen, COLOR_BG_SIDEBAR, col2_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_BORDER, col2_rect, 1, border_radius=8)

        # --- Section 1: Cannon & Combat Upgrades ---
        c1_title = self.display_mgr.font_header.render("CANNON & COMBAT TECH (COINS)", True, COLOR_ACCENT_CYAN)
        screen.blit(c1_title, (col1_rect.left + 20, col1_rect.top + 16))

        y1 = col1_rect.top + 55
        card_w = col1_rect.width - 40
        card_h = 75

        # Card 1: Fire Rate
        fr_lvl = self.save_mgr.data["upgrades"].get("fire_rate_level", 1)
        fr_val = self.upgrade_sys.get_fire_rate()
        fr_cost = self.upgrade_sys.get_fire_rate_cost()
        self._draw_upgrade_card(
            screen,
            rect=pygame.Rect(col1_rect.left + 20, y1, card_w, card_h),
            title="[1] Cannon Fire Rate",
            desc=f"Current: {fr_val:.1f} Mobs/sec (Lvl {fr_lvl})",
            cost_str=f"{fr_cost} Coins",
            can_afford=(coins >= fr_cost),
            btn_key="fire_rate",
            btn_color=COLOR_ACCENT_CYAN,
        )
        y1 += card_h + 16

        # Card 2: Mob Speed
        ms_lvl = self.save_mgr.data["upgrades"].get("mob_speed_level", 1)
        ms_val = self.upgrade_sys.get_mob_speed()
        ms_cost = self.upgrade_sys.get_mob_speed_cost()
        self._draw_upgrade_card(
            screen,
            rect=pygame.Rect(col1_rect.left + 20, y1, card_w, card_h),
            title="[2] Mob Movement Speed",
            desc=f"Current: {int(ms_val)} px/s (Lvl {ms_lvl})",
            cost_str=f"{ms_cost} Coins",
            can_afford=(coins >= ms_cost),
            btn_key="mob_speed",
            btn_color=COLOR_ACCENT_CYAN,
        )
        y1 += card_h + 16

        # Card 3: Champion HP
        ch_lvl = self.save_mgr.data["upgrades"].get("champion_level", 1)
        ch_hp = self.upgrade_sys.get_champion_hp()
        ch_cost = self.upgrade_sys.get_champion_cost()
        self._draw_upgrade_card(
            screen,
            rect=pygame.Rect(col1_rect.left + 20, y1, card_w, card_h),
            title="[3] Champion Giant Power",
            desc=f"Current HP: {ch_hp} (Lvl {ch_lvl})",
            cost_str=f"{ch_cost} Coins",
            can_afford=(coins >= ch_cost),
            btn_key="champion",
            btn_color=COLOR_ACCENT_CYAN,
        )

        # --- Section 2: Town Construction (Bricks) ---
        c2_title = self.display_mgr.font_header.render("TOWN BASE BUILDINGS (BRICKS)", True, COLOR_BRICK_BASE)
        screen.blit(c2_title, (col2_rect.left + 20, col2_rect.top + 16))

        y2 = col2_rect.top + 55

        # Card 4: Town Hall
        th_lvl = self.upgrade_sys.get_town_hall_level()
        th_bonus = int((self.upgrade_sys.get_coin_reward_multiplier() - 1.0) * 100)
        th_cost = self.upgrade_sys.get_town_hall_cost()
        self._draw_upgrade_card(
            screen,
            rect=pygame.Rect(col2_rect.left + 20, y2, card_w, card_h),
            title="[4] Town Hall",
            desc=f"Coin Yield Bonus: +{th_bonus}% (Lvl {th_lvl})",
            cost_str=f"{th_cost} Bricks",
            can_afford=(bricks >= th_cost),
            btn_key="town_hall",
            btn_color=COLOR_BRICK_BASE,
        )
        y2 += card_h + 16

        # Card 5: Brick Factory
        fac_lvl = self.upgrade_sys.get_brick_factory_level()
        fac_bonus = int((self.upgrade_sys.get_brick_looting_multiplier() - 1.0) * 100)
        fac_cost = self.upgrade_sys.get_brick_factory_cost()
        self._draw_upgrade_card(
            screen,
            rect=pygame.Rect(col2_rect.left + 20, y2, card_w, card_h),
            title="[5] Brick Factory",
            desc=f"Looting Bonus: +{fac_bonus}% (Lvl {fac_lvl})",
            cost_str=f"{fac_cost} Bricks",
            can_afford=(bricks >= fac_cost),
            btn_key="brick_factory",
            btn_color=COLOR_BRICK_BASE,
        )

        # 3. Bottom Launch Bar
        bottom_bar = pygame.Rect(20, h - bottom_bar_h - 15, w - 40, bottom_bar_h)
        pygame.draw.rect(screen, COLOR_BG_SIDEBAR, bottom_bar, border_radius=8)
        pygame.draw.rect(screen, COLOR_BORDER, bottom_bar, 1, border_radius=8)

        current_level = self.save_mgr.data.get("current_level", 1)
        play_btn_w = 340
        play_btn_h = 56
        play_rect = pygame.Rect(
            bottom_bar.centerx - (play_btn_w // 2),
            bottom_bar.centery - (play_btn_h // 2),
            play_btn_w,
            play_btn_h,
        )

        if "play" not in self.buttons or self.buttons["play"].rect != play_rect:
            self.buttons["play"] = Button(play_rect, f"DEPLOY TO LEVEL {current_level} [ENTER]", COLOR_ACCENT_GOLD)
        else:
            self.buttons["play"].text = f"DEPLOY TO LEVEL {current_level} [ENTER]"

        self.buttons["play"].draw(screen, self.display_mgr.font_header, enabled=True)

        # Cheatsheet text in bottom bar
        hint_text = self.display_mgr.font_mono.render("Press [1-5] to Quick-Upgrade | [ENTER] to Deploy | [F11] Fullscreen", True, COLOR_TEXT_MUTED)
        screen.blit(hint_text, (bottom_bar.left + 20, bottom_bar.centery - 8))

    def _draw_upgrade_card(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        title: str,
        desc: str,
        cost_str: str,
        can_afford: bool,
        btn_key: str,
        btn_color: Tuple[int, int, int],
    ) -> None:
        pygame.draw.rect(surface, COLOR_BG_SIDEBAR_CARD, rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER, rect, 1, border_radius=6)

        t_surf = self.display_mgr.font_header.render(title, True, COLOR_TEXT_PRIMARY)
        d_surf = self.display_mgr.font_body.render(desc, True, COLOR_TEXT_MUTED)
        surface.blit(t_surf, (rect.left + 16, rect.top + 12))
        surface.blit(d_surf, (rect.left + 16, rect.top + 38))

        # Upgrade Button on the right
        btn_w = 140
        btn_h = 42
        btn_rect = pygame.Rect(rect.right - btn_w - 14, rect.centery - (btn_h // 2), btn_w, btn_h)

        if btn_key not in self.buttons or self.buttons[btn_key].rect != btn_rect:
            self.buttons[btn_key] = Button(btn_rect, cost_str, btn_color)
        else:
            self.buttons[btn_key].text = cost_str
            self.buttons[btn_key].color = btn_color

        self.buttons[btn_key].draw(surface, self.display_mgr.font_body, enabled=can_afford)
