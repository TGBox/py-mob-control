"""Main battle simulation scene managing mobs, gates, cannons, collisions and HUD."""

import math
import random
from typing import List, Optional, Tuple
import pygame

from py_mob_control.config import (
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
    TRACK_Y_PLAYER,
    TRACK_Y_ENEMY,
    COLOR_BG_DARK,
    COLOR_BG_SIDEBAR,
    COLOR_BG_SIDEBAR_CARD,
    COLOR_BORDER,
    COLOR_ACCENT_CYAN,
    COLOR_ACCENT_GOLD,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_PLAYER_PRIMARY,
    COLOR_ENEMY_PRIMARY,
    COLOR_BRICK_BASE,
    DEFAULT_MOB_SPEED,
)
from py_mob_control.engine.display_manager import DisplayManager
from py_mob_control.engine.input_manager import InputManager
from py_mob_control.engine.spatial_grid import SpatialGrid
from py_mob_control.audio.audio_manager import AudioManager
from py_mob_control.vfx.screen_shake import ScreenShake
from py_mob_control.vfx.particle_system import ParticleSystem
from py_mob_control.vfx.floating_text import FloatingTextManager
from py_mob_control.meta.save_manager import SaveManager
from py_mob_control.meta.upgrade_system import UpgradeSystem
from py_mob_control.levels.level_data import LevelConfig
from .entities.mob import Mob, Team
from .entities.cannon import Cannon
from .entities.gate import MultiplierGate, GateOperation
from .entities.base import EnemyBase


class BattleScene:
    """Active combat scene where the player steers the cannon and overwhelms the enemy base."""

    def __init__(
        self,
        level_config: LevelConfig,
        save_mgr: SaveManager,
        upgrade_sys: UpgradeSystem,
        display_mgr: DisplayManager,
        audio_mgr: AudioManager,
    ) -> None:
        self.level_config = level_config
        self.save_mgr = save_mgr
        self.upgrade_sys = upgrade_sys
        self.display_mgr = display_mgr
        self.audio_mgr = audio_mgr

        # Combat systems
        self.spatial_grid = SpatialGrid(cell_size=32.0)
        self.screen_shake = ScreenShake()
        self.particles = ParticleSystem()
        self.floating_texts = FloatingTextManager()

        # Player stats from upgrades
        self.mob_speed = self.upgrade_sys.get_mob_speed()
        self.fire_rate = self.upgrade_sys.get_fire_rate()
        self.champion_hp = self.upgrade_sys.get_champion_hp()

        # Entities
        self.player_cannon = Cannon(
            y=TRACK_Y_PLAYER,
            team=Team.PLAYER,
            fire_rate=self.fire_rate,
        )

        self.enemy_base = EnemyBase(
            max_bricks=level_config.base_bricks,
            spawn_rate=level_config.base_spawn_rate,
        )

        self.enemy_cannon: Optional[Cannon] = None
        if level_config.has_enemy_cannon:
            self.enemy_cannon = Cannon(
                y=TRACK_Y_ENEMY,
                team=Team.ENEMY,
                fire_rate=level_config.enemy_cannon_fire_rate,
            )

        self.gates: List[MultiplierGate] = level_config.gates
        self.player_mobs: List[Mob] = []
        self.enemy_mobs: List[Mob] = []

        # Battle stats & state
        self.mobs_spawned_total = 0
        self.enemies_killed = 0
        self.gate_combo_counter = 0
        self.combo_timer = 0.0
        self.bricks_destroyed = 0
        self.combat_coins_earned = 0

        self.player_health = 100
        self.max_player_health = 100

        self.is_victory = False
        self.is_defeat = False
        self.transition_timer = 0.0

        # Background grid animation
        self.bg_scroll_offset = 0.0

    def update(self, dt: float, input_mgr: InputManager) -> Optional[str]:
        """Update battle physics, inputs, and collisions.

        Returns scene transition string ('LOOT', 'DEFEAT') or None.
        """
        self.bg_scroll_offset = (self.bg_scroll_offset + dt * 40.0) % 40.0
        self.screen_shake.update(dt)
        self.particles.update(dt)
        self.floating_texts.update(dt)
        self.audio_mgr.update(dt)

        # Decay combo
        if self.combo_timer > 0.0:
            self.combo_timer -= dt
            if self.combo_timer <= 0.0:
                self.gate_combo_counter = 0

        if self.is_victory:
            self.transition_timer += dt
            if self.transition_timer >= 0.7:
                return "LOOT"
            return None

        if self.is_defeat:
            self.transition_timer += dt
            if self.transition_timer >= 1.5:
                return "DEFEAT"
            return None

        # 1. Player Cannon Movement & Firing
        # Mouse target X
        vx, _ = self.display_mgr.screen_to_virtual(input_mgr.mouse_screen_pos)
        kb_axis = input_mgr.get_horizontal_keyboard_axis()

        if abs(kb_axis) > 0.01:
            self.player_cannon.move_axis(kb_axis, dt)
        else:
            self.player_cannon.move_toward(vx, dt)

        self.player_cannon.update(dt)

        # Firing
        if input_mgr.is_firing():
            new_mob = self.player_cannon.try_fire(self.mob_speed)
            if new_mob:
                self.player_mobs.append(new_mob)
                self.mobs_spawned_total += 1
                self.audio_mgr.play("mob_pop")

        # Champion Summon
        if input_mgr.is_champion_summon_triggered():
            champ = self.player_cannon.try_summon_champion(self.mob_speed)
            if champ:
                champ.hp = self.champion_hp
                champ.max_hp = self.champion_hp
                self.player_mobs.append(champ)
                self.audio_mgr.play("champion_summon")
                self.screen_shake.add_trauma(0.35)
                self.floating_texts.spawn("CHAMPION!", champ.x, champ.y - 30, color=COLOR_ACCENT_GOLD, large=True)

        # 2. Enemy Cannon / Base Spawners
        if self.enemy_cannon:
            self.enemy_cannon.update(dt)
            # AI tracks player cannon position with slight lag
            self.enemy_cannon.move_toward(self.player_cannon.x, dt * 0.7)
            enemy_mob = self.enemy_cannon.try_fire(DEFAULT_MOB_SPEED * 0.95)
            if enemy_mob:
                self.enemy_mobs.append(enemy_mob)

        base_mob = self.enemy_base.update(dt)
        if base_mob:
            self.enemy_mobs.append(base_mob)

        # 3. Update Multiplier Gates
        for gate in self.gates:
            gate.update(dt)

        # 4. Update Mobs & Gate Interactions
        MAX_ACTIVE_RENDER_MOBS = 400
        new_player_clones: List[Mob] = []
        current_entity_count = len(self.player_mobs)

        for mob in self.player_mobs:
            mob.update(dt)
            for gate in self.gates:
                if current_entity_count + len(new_player_clones) < MAX_ACTIVE_RENDER_MOBS:
                    clones = gate.process_mob(mob)
                    if clones:
                        new_player_clones.extend(clones)
                        self.gate_combo_counter += 1
                        self.combo_timer = 1.2
                        self.audio_mgr.play_gate_chime(self.gate_combo_counter)
                        self.particles.emit_sparks(gate.x, gate.y, count=6)
                else:
                    # Density compression: boost count of existing mob directly instead of allocating hundreds of objects
                    if not mob.alive or gate.id in mob.passed_gate_ids:
                        continue
                    if gate.rect.collidepoint(int(mob.x), int(mob.y)):
                        mob.passed_gate_ids.add(gate.id)
                        gate.pulse = 1.0
                        if gate.operation == GateOperation.MULTIPLY:
                            mob.count = min(50000, mob.count * gate.value)
                        elif gate.operation == GateOperation.ADD:
                            mob.count = min(50000, mob.count + gate.value)
                        elif gate.operation == GateOperation.SPEED:
                            mob.speed *= 1.45
                        self.gate_combo_counter += 1
                        self.combo_timer = 1.2
                        self.audio_mgr.play_gate_chime(self.gate_combo_counter)
                        self.particles.emit_sparks(gate.x, gate.y, count=4)

        self.player_mobs.extend(new_player_clones)

        for mob in self.enemy_mobs:
            mob.update(dt)

        # 5. Spatial Grid & Mob-to-Mob Collisions
        all_active_mobs = [m for m in self.player_mobs if m.alive] + [m for m in self.enemy_mobs if m.alive]
        self.spatial_grid.populate(all_active_mobs)
        self.spatial_grid.solve_separation(all_active_mobs, dt)

        # Clash resolution: Invert query to iterate over enemy mobs (minority team, O(E) queries instead of O(P))
        for em in self.enemy_mobs:
            if not em.alive:
                continue
            neighbors = self.spatial_grid.query_radius(em.x, em.y, em.radius + 15.0)
            for pm in neighbors:
                if not pm.alive or pm.team != Team.PLAYER:
                    continue
                dist_sq = (pm.x - em.x) ** 2 + (pm.y - em.y) ** 2
                combined_r = pm.radius + em.radius
                if dist_sq <= combined_r * combined_r:
                    p_dmg = 5 if pm.is_champion else 1
                    e_dmg = 5 if em.is_champion else 1

                    pm.take_damage(e_dmg)
                    killed = em.take_damage(p_dmg)

                    self.audio_mgr.play("mob_clash")
                    mid_x = (pm.x + em.x) / 2.0
                    mid_y = (pm.y + em.y) / 2.0
                    self.particles.emit_mob_pop(mid_x, mid_y, COLOR_PLAYER_PRIMARY, count=3)
                    self.particles.emit_mob_pop(mid_x, mid_y, COLOR_ENEMY_PRIMARY, count=3)

                    if killed:
                        self.enemies_killed += 1
                        self.combat_coins_earned += 1
                        self.player_cannon.add_ultimate_charge(0.02)

                    if pm.is_champion:
                        self.audio_mgr.play("champion_stomp")
                        self.screen_shake.add_trauma(0.18)

                    if not em.alive:
                        break

        # 6. Base Attack & Damage (Filtered by Y threshold to avoid iterating whole army)
        base_threshold = self.enemy_base.y + (self.enemy_base.height / 2.0) + 30.0
        for pm in self.player_mobs:
            if pm.alive and pm.y <= base_threshold:
                bricks_hit, base_destroyed = self.enemy_base.check_mob_attack(pm)
                if bricks_hit > 0:
                    self.bricks_destroyed += bricks_hit
                    self.particles.emit_brick_fragments(pm.x, self.enemy_base.rect.bottom)
                    self.audio_mgr.play("brick_chip")
                    self.screen_shake.add_trauma(0.12)
                    if base_destroyed:
                        self.is_victory = True
                        if self.combat_coins_earned > 0:
                            self.save_mgr.add_coins(self.combat_coins_earned)
                        self.audio_mgr.play("win")
                        self.screen_shake.add_trauma(0.6)
                        self.particles.emit_confetti(VIRTUAL_WIDTH / 2.0, 150.0, count=60)
                        self.floating_texts.spawn("VICTORY!", VIRTUAL_WIDTH / 2.0, 200.0, color=COLOR_ACCENT_GOLD, large=True)
                        break

        # 7. Enemy Mobs Reaching Player Line
        player_defense_line = TRACK_Y_PLAYER - 20.0
        for em in self.enemy_mobs:
            if em.alive and em.y >= player_defense_line:
                em.alive = False
                dmg = 10 if em.is_champion else 2
                self.player_health = max(0, self.player_health - dmg)
                self.audio_mgr.play("mob_clash")
                self.screen_shake.add_trauma(0.2)
                if self.player_health <= 0 and not self.is_defeat and not self.is_victory:
                    self.is_defeat = True
                    if self.combat_coins_earned > 0:
                        self.save_mgr.add_coins(self.combat_coins_earned)
                    self.audio_mgr.play("lose")
                    self.floating_texts.spawn("DEFEAT!", VIRTUAL_WIDTH / 2.0, VIRTUAL_HEIGHT / 2.0, color=COLOR_ENEMY_PRIMARY, large=True)

        # Clean dead mobs
        self.player_mobs = [m for m in self.player_mobs if m.alive]
        self.enemy_mobs = [m for m in self.enemy_mobs if m.alive]

        return None

    def draw(self) -> None:
        """Render virtual battlefield and dynamic ultrawide sidebars."""
        v_surf = self.display_mgr.virtual_surface

        # --- Draw Virtual Battlefield ---
        v_surf.fill(COLOR_BG_DARK)

        # Background grid with perspective movement
        grid_spacing = 40
        for x in range(0, VIRTUAL_WIDTH + 1, grid_spacing):
            pygame.draw.line(v_surf, (22, 28, 44), (x, 0), (x, VIRTUAL_HEIGHT), 1)

        for y in range(int(self.bg_scroll_offset), VIRTUAL_HEIGHT + 1, grid_spacing):
            pygame.draw.line(v_surf, (22, 28, 44), (0, y), (VIRTUAL_WIDTH, y), 1)

        # Defense line markers
        pygame.draw.line(v_surf, (80, 20, 30), (20, TRACK_Y_PLAYER - 20), (VIRTUAL_WIDTH - 20, TRACK_Y_PLAYER - 20), 1)

        # Draw Base
        self.enemy_base.draw(v_surf)

        # Draw Multiplier Gates
        for gate in self.gates:
            gate.draw(v_surf)

        # Draw Cannons
        if self.enemy_cannon:
            self.enemy_cannon.draw(v_surf)
        self.player_cannon.draw(v_surf)

        # Draw Mobs
        for m in self.enemy_mobs:
            m.draw(v_surf)
        for m in self.player_mobs:
            m.draw(v_surf)

        # Draw Particles & Floating Texts
        self.particles.draw(v_surf)
        self.floating_texts.draw(v_surf)

        # Render framed battlefield onto screen with screen shake
        shake_offset = self.screen_shake.get_offset()
        self.display_mgr.render_frame(screen_shake_offset=shake_offset)

        # --- Draw Adaptive Sidebars on Main Screen Surface ---
        self._draw_sidebars()

    def _draw_sidebars(self) -> None:
        """Draw live statistics, mini radar, and economy cards on sidebars."""
        screen = self.display_mgr.screen
        lp = self.display_mgr.left_panel_rect
        rp = self.display_mgr.right_panel_rect

        # 1. Left Panel (Battlefield Analytics)
        if lp.width >= 160:
            pygame.draw.rect(screen, COLOR_BG_SIDEBAR, lp, border_radius=8)
            pygame.draw.rect(screen, COLOR_BORDER, lp, 1, border_radius=8)

            y_cursor = lp.top + 20

            # Title
            t_surf = self.display_mgr.font_header.render("BATTLE RADAR", True, COLOR_ACCENT_CYAN)
            screen.blit(t_surf, (lp.left + 16, y_cursor))
            y_cursor += 36

            # Mob Count Cards
            card_w = lp.width - 32
            # Blue Mobs
            card_blue = pygame.Rect(lp.left + 16, y_cursor, card_w, 46)
            pygame.draw.rect(screen, COLOR_BG_SIDEBAR_CARD, card_blue, border_radius=6)
            pygame.draw.rect(screen, COLOR_PLAYER_PRIMARY, card_blue, 1, border_radius=6)
            c_text = self.display_mgr.font_body.render("Allied Mobs Active:", True, COLOR_TEXT_MUTED)
            total_allied_count = sum(m.count for m in self.player_mobs)
            c_val = self.display_mgr.font_header.render(str(total_allied_count), True, COLOR_PLAYER_PRIMARY)
            screen.blit(c_text, (card_blue.left + 10, card_blue.top + 5))
            screen.blit(c_val, (card_blue.left + 10, card_blue.top + 22))
            y_cursor += 56

            # Red Mobs
            card_red = pygame.Rect(lp.left + 16, y_cursor, card_w, 46)
            pygame.draw.rect(screen, COLOR_BG_SIDEBAR_CARD, card_red, border_radius=6)
            pygame.draw.rect(screen, COLOR_ENEMY_PRIMARY, card_red, 1, border_radius=6)
            r_text = self.display_mgr.font_body.render("Enemy Mobs Active:", True, COLOR_TEXT_MUTED)
            r_val = self.display_mgr.font_header.render(str(len(self.enemy_mobs)), True, COLOR_ENEMY_PRIMARY)
            screen.blit(r_text, (card_red.left + 10, card_red.top + 5))
            screen.blit(r_val, (card_red.left + 10, card_red.top + 22))
            y_cursor += 64

            # Player Health Bar
            hp_lbl = self.display_mgr.font_body.render("Player Base Integrity:", True, COLOR_TEXT_MUTED)
            screen.blit(hp_lbl, (lp.left + 16, y_cursor))
            y_cursor += 22

            hp_bar = pygame.Rect(lp.left + 16, y_cursor, card_w, 14)
            pygame.draw.rect(screen, (30, 30, 45), hp_bar, border_radius=4)
            hp_ratio = max(0.0, self.player_health / float(self.max_player_health))
            if hp_ratio > 0:
                fill_w = int(card_w * hp_ratio)
                fill_col = (50, 220, 100) if hp_ratio > 0.4 else (255, 60, 60)
                pygame.draw.rect(screen, fill_col, (hp_bar.left, hp_bar.top, fill_w, hp_bar.height), border_radius=4)
            y_cursor += 34

            # Champion Charge Gauge
            ult_lbl = self.display_mgr.font_body.render("Champion Gauge:", True, COLOR_TEXT_MUTED)
            screen.blit(ult_lbl, (lp.left + 16, y_cursor))
            y_cursor += 22

            ult_bar = pygame.Rect(lp.left + 16, y_cursor, card_w, 18)
            pygame.draw.rect(screen, (30, 30, 45), ult_bar, border_radius=4)
            ult_prog = self.player_cannon.ultimate_progress
            if ult_prog > 0:
                fill_w = int(card_w * ult_prog)
                fill_col = COLOR_ACCENT_GOLD if self.player_cannon.is_ultimate_ready else COLOR_ACCENT_CYAN
                pygame.draw.rect(screen, fill_col, (ult_bar.left, ult_bar.top, fill_w, ult_bar.height), border_radius=4)

            u_status = "READY! (R-Click/Q)" if self.player_cannon.is_ultimate_ready else f"{int(ult_prog * 100)}%"
            u_text = self.display_mgr.font_mono.render(u_status, True, (255, 255, 255))
            u_rect = u_text.get_rect(center=ult_bar.center)
            screen.blit(u_text, u_rect)
            y_cursor += 44

            # Audio Status
            mute_str = "[M] Audio: MUTED" if self.audio_mgr.is_muted else "[M] Audio: ON"
            m_surf = self.display_mgr.font_mono.render(mute_str, True, COLOR_TEXT_MUTED)
            screen.blit(m_surf, (lp.left + 16, lp.bottom - 30))

        # 2. Right Panel (Command Deck, Level Info & Controls)
        if rp.width >= 160:
            pygame.draw.rect(screen, COLOR_BG_SIDEBAR, rp, border_radius=8)
            pygame.draw.rect(screen, COLOR_BORDER, rp, 1, border_radius=8)

            y_cursor = rp.top + 20

            # Level Title
            lvl_surf = self.display_mgr.font_header.render(f"LEVEL {self.level_config.level_number}", True, COLOR_ACCENT_GOLD)
            screen.blit(lvl_surf, (rp.left + 16, y_cursor))
            y_cursor += 26
            name_surf = self.display_mgr.font_body.render(self.level_config.title, True, COLOR_TEXT_PRIMARY)
            screen.blit(name_surf, (rp.left + 16, y_cursor))
            y_cursor += 40

            # Currencies
            card_w = rp.width - 32
            curr_box = pygame.Rect(rp.left + 16, y_cursor, card_w, 70)
            pygame.draw.rect(screen, COLOR_BG_SIDEBAR_CARD, curr_box, border_radius=6)
            pygame.draw.rect(screen, COLOR_BORDER, curr_box, 1, border_radius=6)

            coins_text = self.display_mgr.font_body.render(f"Coins: {self.save_mgr.data['coins']}", True, COLOR_ACCENT_GOLD)
            bricks_text = self.display_mgr.font_body.render(f"Bricks: {self.save_mgr.data['bricks']}", True, COLOR_BRICK_BASE)
            screen.blit(coins_text, (curr_box.left + 12, curr_box.top + 10))
            screen.blit(bricks_text, (curr_box.left + 12, curr_box.top + 38))
            y_cursor += 90

            # Controls Cheatsheet Card
            ctrl_box = pygame.Rect(rp.left + 16, y_cursor, card_w, 160)
            pygame.draw.rect(screen, COLOR_BG_SIDEBAR_CARD, ctrl_box, border_radius=6)
            pygame.draw.rect(screen, COLOR_BORDER, ctrl_box, 1, border_radius=6)

            ctrl_title = self.display_mgr.font_body.render("CONTROLS:", True, COLOR_ACCENT_CYAN)
            screen.blit(ctrl_title, (ctrl_box.left + 10, ctrl_box.top + 8))

            shortcuts = [
                ("Mouse / A, D:", "Aim Cannon"),
                ("Left-Click / Space:", "Fire Mobs"),
                ("Right-Click / Q, E:", "Champion"),
                ("F11:", "Fullscreen"),
                ("M:", "Toggle Audio"),
            ]
            cy = ctrl_box.top + 32
            for key_str, desc_str in shortcuts:
                k_s = self.display_mgr.font_mono.render(key_str, True, COLOR_TEXT_PRIMARY)
                d_s = self.display_mgr.font_mono.render(desc_str, True, COLOR_TEXT_MUTED)
                screen.blit(k_s, (ctrl_box.left + 10, cy))
                screen.blit(d_s, (ctrl_box.left + 120, cy))
                cy += 24
