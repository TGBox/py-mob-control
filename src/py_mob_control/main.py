"""Main application entry point and game loop state machine for py-mob-control."""

import sys
from typing import Optional
import pygame

from py_mob_control.config import TARGET_FPS, COLOR_BG_DARK, COLOR_TEXT_PRIMARY, COLOR_ACCENT_GOLD
from py_mob_control.engine.display_manager import DisplayManager
from py_mob_control.engine.input_manager import InputManager
from py_mob_control.audio.audio_manager import AudioManager
from py_mob_control.meta.save_manager import SaveManager
from py_mob_control.meta.upgrade_system import UpgradeSystem
from py_mob_control.levels.level_data import get_level_config
from py_mob_control.game.battle_scene import BattleScene
from py_mob_control.game.loot_scene import LootScene
from py_mob_control.meta.shop_scene import ShopScene


class GameApp:
    """Core game application coordinating state transitions and rendering."""

    STATE_SHOP = "SHOP"
    STATE_BATTLE = "BATTLE"
    STATE_LOOT = "LOOT"
    STATE_DEFEAT = "DEFEAT"

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Mob Control - Python Desktop Edition")

        self.display_mgr = DisplayManager()
        self.input_mgr = InputManager()
        self.audio_mgr = AudioManager.get_instance()
        self.save_mgr = SaveManager()
        self.upgrade_sys = UpgradeSystem(self.save_mgr)

        self.clock = pygame.time.Clock()
        self.is_running = True

        # State management
        self.state = self.STATE_SHOP
        self.shop_scene = ShopScene(self.save_mgr, self.upgrade_sys, self.display_mgr, self.audio_mgr)
        self.battle_scene: Optional[BattleScene] = None
        self.loot_scene: Optional[LootScene] = None

        # Defeat screen timer
        self.defeat_timer = 0.0

    def start_battle(self, level: Optional[int] = None) -> None:
        """Initialize a new battle for current savegame level or selected level."""
        current_lvl = level or (self.shop_scene.selected_level if self.shop_scene else None) or self.save_mgr.data.get("current_level", 1)
        cfg = get_level_config(current_lvl)
        self.battle_scene = BattleScene(
            level_config=cfg,
            save_mgr=self.save_mgr,
            upgrade_sys=self.upgrade_sys,
            display_mgr=self.display_mgr,
            audio_mgr=self.audio_mgr,
        )
        self.state = self.STATE_BATTLE

    def start_looting(self) -> None:
        """Trigger post-victory brick harvesting phase."""
        if not self.battle_scene:
            self.state = self.STATE_SHOP
            return

        current_lvl = self.battle_scene.level_config.level_number
        survivors = [m for m in self.battle_scene.player_mobs if m.alive]
        self.loot_scene = LootScene(
            level_number=current_lvl,
            surviving_mobs=survivors,
            save_mgr=self.save_mgr,
            upgrade_sys=self.upgrade_sys,
            display_mgr=self.display_mgr,
            audio_mgr=self.audio_mgr,
        )
        self.state = self.STATE_LOOT

    def run(self) -> None:
        """Main game loop."""
        while self.is_running:
            dt = min(self.clock.tick(TARGET_FPS) / 1000.0, 0.05)

            # Event Polling
            self.input_mgr.begin_frame()
            for event in pygame.event.get():
                self.input_mgr.process_event(event)

            if self.input_mgr.quit_requested:
                self.is_running = False
                break

            # Window Resize handling
            if self.input_mgr.resize_event:
                w, h = self.input_mgr.resize_event
                self.display_mgr.handle_resize(w, h)

            # Global Hotkeys
            if self.input_mgr.is_fullscreen_toggle_pressed():
                self.display_mgr.toggle_fullscreen()

            if self.input_mgr.is_mute_toggle_pressed():
                self.audio_mgr.toggle_mute()

            # State Machine Updates
            if self.state == self.STATE_SHOP:
                action = self.shop_scene.update(dt, self.input_mgr)
                if action == "BATTLE":
                    self.start_battle()
                self.shop_scene.draw()

            elif self.state == self.STATE_BATTLE:
                if self.input_mgr.is_pause_pressed():
                    # Return to HQ
                    self.state = self.STATE_SHOP
                    continue

                action = self.battle_scene.update(dt, self.input_mgr)
                if action == "LOOT":
                    self.start_looting()
                elif action == "DEFEAT":
                    self.state = self.STATE_DEFEAT
                    self.defeat_timer = 0.0

                self.battle_scene.draw()

            elif self.state == self.STATE_LOOT:
                action = self.loot_scene.update(dt, self.input_mgr)
                if action == "SHOP":
                    self.state = self.STATE_SHOP
                self.loot_scene.draw()

            elif self.state == self.STATE_DEFEAT:
                self.defeat_timer += dt
                self._draw_defeat_screen()
                if self.defeat_timer >= 1.0 and (self.input_mgr.mouse_clicked_this_frame or self.input_mgr.is_key_just_pressed([pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE])):
                    self.state = self.STATE_SHOP

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)

    def _draw_defeat_screen(self) -> None:
        """Render defeat message over the battlefield."""
        if self.battle_scene:
            self.battle_scene.draw()

        # Dark overlay
        overlay = pygame.Surface((self.display_mgr.window_width, self.display_mgr.window_height), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 180))
        self.display_mgr.screen.blit(overlay, (0, 0))

        cx = self.display_mgr.window_width // 2
        cy = self.display_mgr.window_height // 2

        coins_msg = f"Recovered +{self.battle_scene.combat_coins_earned} Coins from combat!" if self.battle_scene else ""

        t1 = self.display_mgr.font_big.render("DEFEAT!", True, (255, 60, 60))
        t2 = self.display_mgr.font_header.render("Your defense line was overrun.", True, COLOR_TEXT_PRIMARY)
        t_coins = self.display_mgr.font_header.render(coins_msg, True, COLOR_ACCENT_GOLD)
        t3 = self.display_mgr.font_body.render("Click or press [SPACE] to return to HQ & upgrade.", True, COLOR_TEXT_PRIMARY)

        self.display_mgr.screen.blit(t1, t1.get_rect(center=(cx, cy - 50)))
        self.display_mgr.screen.blit(t2, t2.get_rect(center=(cx, cy - 5)))
        self.display_mgr.screen.blit(t_coins, t_coins.get_rect(center=(cx, cy + 28)))
        self.display_mgr.screen.blit(t3, t3.get_rect(center=(cx, cy + 65)))


def main() -> None:
    """CLI script entrypoint."""
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()
