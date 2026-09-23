"""Post-battle brick looting celebration phase where surviving mobs dismantle the fortress."""

import math
import random
from typing import List, Optional, Tuple
import pygame

from py_mob_control.config import (
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
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
from py_mob_control.vfx.particle_system import ParticleSystem
from py_mob_control.vfx.screen_shake import ScreenShake
from py_mob_control.meta.save_manager import SaveManager
from py_mob_control.meta.upgrade_system import UpgradeSystem
from .entities.mob import Mob, Team


class LootScene:
    """Celebratory looting sequence: surviving mobs swarm the broken fortress and harvest bricks."""

    def __init__(
        self,
        level_number: int,
        surviving_mobs: List[Mob],
        save_mgr: SaveManager,
        upgrade_sys: UpgradeSystem,
        display_mgr: DisplayManager,
        audio_mgr: AudioManager,
    ) -> None:
        self.level_number = level_number
        self.save_mgr = save_mgr
        self.upgrade_sys = upgrade_sys
        self.display_mgr = display_mgr
        self.audio_mgr = audio_mgr

        self.particles = ParticleSystem()
        self.screen_shake = ScreenShake()

        # Ensure we have at least 15-25 enthusiastic looting mobs even if only few survived
        min_looters = max(len(surviving_mobs), 20)
        self.mobs: List[Mob] = []
        for i in range(min_looters):
            orig = surviving_mobs[i] if i < len(surviving_mobs) else None
            x = orig.x if orig else random.uniform(80.0, VIRTUAL_WIDTH - 80.0)
            y = orig.y if orig else random.uniform(400.0, 750.0)
            m = Mob(x=x, y=y, team=orig.team if orig else Team.PLAYER, speed=260.0)
            self.mobs.append(m)

        # Base rubble area
        self.base_rubble_y = 120.0
        self.total_bricks_available = 40 + (level_number * 15)
        self.bricks_looted = 0
        self.coins_earned = 50 + (level_number * 25)

        # Apply Town Upgrade multipliers
        self.brick_multiplier = self.upgrade_sys.get_brick_looting_multiplier()
        self.coin_multiplier = self.upgrade_sys.get_coin_reward_multiplier()
        self.final_bricks = int(self.total_bricks_available * self.brick_multiplier)
        self.final_coins = int(self.coins_earned * self.coin_multiplier)

        # Target position on screen where bricks fly into (Right sidebar)
        self.target_screen_pos = (
            display_mgr.right_panel_rect.centerx,
            display_mgr.right_panel_rect.top + 120,
        )

        # Timer
        self.phase_time = 0.0
        self.looting_finished = False
        self.has_saved_rewards = False

        # Periodic brick spawn interval
        self.chip_timer = 0.0
        self.is_speeding_up = False

        # Confetti burst
        self.particles.emit_confetti(VIRTUAL_WIDTH / 2.0, 160.0, count=50)

    def update(self, dt: float, input_mgr: InputManager) -> Optional[str]:
        """Update mob swarm, brick flight, and rewards collection."""
        self.phase_time += dt
        self.screen_shake.update(dt)
        self.audio_mgr.update(dt)

        # 1. Mobs march upward to assault the rubble
        for mob in self.mobs:
            if mob.y > self.base_rubble_y:
                mob.y -= mob.speed * dt
            else:
                # Milling around the rubble hammering bricks
                mob.x += math.sin(self.phase_time * 6.0 + mob.id) * 35.0 * dt

        # Check if user holds mouse left button or space to accelerate animation
        self.is_speeding_up = input_mgr.mouse_left_down or input_mgr.is_key_held([pygame.K_SPACE, pygame.K_RETURN])

        # 2. Spawn flying bricks continuously until quota reached
        remaining = self.final_bricks - self.bricks_looted
        if remaining > 0:
            if self.is_speeding_up:
                # Fast forward: all remaining bricks spawn in under 0.4s
                spawn_rate = max(25.0, remaining / 0.4)
                self.chip_timer += dt * spawn_rate
                spawns_to_do = int(self.chip_timer)
                if spawns_to_do > 0:
                    self.chip_timer -= spawns_to_do
                    spawns_to_do = min(spawns_to_do, remaining)
                    for _ in range(spawns_to_do):
                        self.bricks_looted += 1
                        source_mob = random.choice(self.mobs)
                        start_virt = (source_mob.x, max(self.base_rubble_y, source_mob.y))
                        start_screen = self.display_mgr.virtual_to_screen(start_virt)
                        self.particles.spawn_flying_brick(start_screen, self.target_screen_pos)
                    self.particles.emit_brick_fragments(start_virt[0], start_virt[1], count=2)
                    self.audio_mgr.play("brick_chip")
            else:
                self.chip_timer += dt
                if self.chip_timer >= 0.06:
                    self.chip_timer = 0.0
                    self.bricks_looted += 1
                    source_mob = random.choice(self.mobs)
                    start_virt = (source_mob.x, max(self.base_rubble_y, source_mob.y))
                    start_screen = self.display_mgr.virtual_to_screen(start_virt)
                    self.particles.spawn_flying_brick(start_screen, self.target_screen_pos)
                    self.particles.emit_brick_fragments(start_virt[0], start_virt[1], count=3)
                    self.audio_mgr.play("brick_chip")
                    self.screen_shake.add_trauma(0.04)

        elif not self.looting_finished:
            self.looting_finished = True
            # Confetti finale
            self.particles.emit_confetti(VIRTUAL_WIDTH / 2.0, 160.0, count=40)
            self.audio_mgr.play("win")

        # 3. Particle update & arrived bricks (4.5x faster when speeding up)
        flying_mult = 4.5 if self.is_speeding_up else 1.0
        arrived = self.particles.update(dt, flying_speed_multiplier=flying_mult)
        if arrived > 0:
            self.audio_mgr.play("coin")

        # Save once complete
        if self.looting_finished and not self.has_saved_rewards:
            self.has_saved_rewards = True
            self.save_mgr.add_bricks(self.final_bricks)
            self.save_mgr.add_coins(self.final_coins)
            self.save_mgr.advance_level(self.level_number)

        # Continue button (if speeding up, allow continuing after only 0.8s)
        min_phase_time = 0.8 if self.is_speeding_up else 1.8
        if self.looting_finished and self.phase_time >= min_phase_time:
            if input_mgr.mouse_clicked_this_frame or input_mgr.is_key_just_pressed([pygame.K_SPACE, pygame.K_RETURN]):
                return "SHOP"

        return None

    def draw(self) -> None:
        """Render victory looting scene and summary cards."""
        v_surf = self.display_mgr.virtual_surface
        v_surf.fill(COLOR_BG_DARK)

        # Draw base rubble / gold vault
        rubble_rect = pygame.Rect(int(VIRTUAL_WIDTH / 2.0 - 130), int(self.base_rubble_y - 40), 260, 70)
        pygame.draw.rect(v_surf, (60, 30, 40), rubble_rect, border_radius=6)
        pygame.draw.rect(v_surf, COLOR_ACCENT_GOLD, rubble_rect, 2, border_radius=6)

        # Rubble label
        r_text = self.display_mgr.font_header.render("FORTRESS DESTROYED!", True, COLOR_ACCENT_GOLD)
        r_pos = r_text.get_rect(center=rubble_rect.center)
        v_surf.blit(r_text, r_pos)

        # Draw Mobs hammering
        for m in self.mobs:
            m.draw(v_surf)

        # Draw virtual particles (debris)
        # Note: flying bricks are drawn in screen coords
        for p in self.particles.particles:
            alpha_ratio = max(0.0, p.life / p.max_life)
            current_size = max(1.0, p.size * alpha_ratio)
            pygame.draw.circle(v_surf, p.color, (int(p.x), int(p.y)), int(current_size))

        # Render battlefield frame
        shake = self.screen_shake.get_offset()
        self.display_mgr.render_frame(screen_shake_offset=shake)

        # Draw flying bricks on screen surface
        screen = self.display_mgr.screen
        for fb in self.particles.flying_bricks:
            bx, by = fb.get_pos()
            b_rect = pygame.Rect(int(bx) - 6, int(by) - 5, 12, 10)
            pygame.draw.rect(screen, fb.color, b_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 240, 160), b_rect, 1, border_radius=3)

        # Render sidebars and victory summary
        self._draw_summary_sidebars()

    def _draw_summary_sidebars(self) -> None:
        screen = self.display_mgr.screen
        rp = self.display_mgr.right_panel_rect

        if rp.width >= 160:
            pygame.draw.rect(screen, COLOR_BG_SIDEBAR, rp, border_radius=8)
            pygame.draw.rect(screen, COLOR_BORDER, rp, 1, border_radius=8)

            y_cursor = rp.top + 25

            t1 = self.display_mgr.font_title.render("VICTORY!", True, COLOR_ACCENT_GOLD)
            screen.blit(t1, (rp.left + 20, y_cursor))
            y_cursor += 36

            t2 = self.display_mgr.font_body.render(f"Level {self.level_number} Cleared", True, COLOR_TEXT_MUTED)
            screen.blit(t2, (rp.left + 20, y_cursor))
            y_cursor += 44

            card_w = rp.width - 40
            # Bricks Looted Card
            b_card = pygame.Rect(rp.left + 20, y_cursor, card_w, 65)
            pygame.draw.rect(screen, COLOR_BG_SIDEBAR_CARD, b_card, border_radius=6)
            pygame.draw.rect(screen, COLOR_BRICK_BASE, b_card, 1, border_radius=6)

            b_lbl = self.display_mgr.font_body.render("Bricks Harvested:", True, COLOR_TEXT_MUTED)
            b_val = self.display_mgr.font_header.render(f"+{self.bricks_looted} Bricks", True, COLOR_BRICK_BASE)
            screen.blit(b_lbl, (b_card.left + 12, b_card.top + 8))
            screen.blit(b_val, (b_card.left + 12, b_card.top + 30))
            y_cursor += 80

            # Coins Earned Card
            c_card = pygame.Rect(rp.left + 20, y_cursor, card_w, 65)
            pygame.draw.rect(screen, COLOR_BG_SIDEBAR_CARD, c_card, border_radius=6)
            pygame.draw.rect(screen, COLOR_ACCENT_GOLD, c_card, 1, border_radius=6)

            c_lbl = self.display_mgr.font_body.render("Coins Earned:", True, COLOR_TEXT_MUTED)
            c_val = self.display_mgr.font_header.render(f"+{self.final_coins} Coins", True, COLOR_ACCENT_GOLD)
            screen.blit(c_lbl, (c_card.left + 12, c_card.top + 8))
            screen.blit(c_val, (c_card.left + 12, c_card.top + 30))
            y_cursor += 95

            # Continue button or fast-forward hint
            if not self.looting_finished:
                hint_str = ">> FAST-FORWARDING..." if self.is_speeding_up else "HOLD [CLICK] TO SPEED UP (1s)"
                hint_col = COLOR_ACCENT_GOLD if self.is_speeding_up else COLOR_TEXT_MUTED
                h_surf = self.display_mgr.font_mono.render(hint_str, True, hint_col)
                screen.blit(h_surf, (rp.left + 20, y_cursor))
            elif self.looting_finished:
                btn_rect = pygame.Rect(rp.left + 20, y_cursor, card_w, 48)
                pygame.draw.rect(screen, COLOR_ACCENT_CYAN, btn_rect, border_radius=6)
                btn_text = self.display_mgr.font_header.render("CONTINUE TO HQ [SPACE]", True, (10, 15, 25))
                btn_pos = btn_text.get_rect(center=btn_rect.center)
                screen.blit(btn_text, btn_pos)
