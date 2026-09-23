"""Audio Manager for py-mob-control.

Caches procedural sounds, throttles playback to avoid acoustic distortion,
and provides volume / mute controls.
"""

from typing import Dict, List, Optional
import pygame

from .sound_synth import (
    synth_mob_pop,
    synth_gate_chime,
    synth_mob_clash,
    synth_champion_summon,
    synth_champion_stomp,
    synth_brick_chip,
    synth_coin,
    synth_win_fanfare,
    synth_game_over,
)


class AudioManager:
    """Central audio manager with procedural sound catalog and playback throttling."""

    _instance: Optional["AudioManager"] = None

    def __init__(self, init_mixer: bool = True) -> None:
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.gate_chimes: List[pygame.mixer.Sound] = []
        self.is_muted: bool = False
        self.master_volume: float = 0.75
        self.is_available: bool = False

        # Throttling cooldowns (in seconds)
        self.cooldowns: Dict[str, float] = {
            "mob_pop": 0.05,
            "gate_chime": 0.06,
            "mob_clash": 0.04,
            "brick_chip": 0.03,
            "coin": 0.04,
            "stomp": 0.1,
        }
        self.timers: Dict[str, float] = {k: 0.0 for k in self.cooldowns}

        if init_mixer:
            self._init_audio()

    def _init_audio(self) -> None:
        """Initialize pygame.mixer safely and cache synthesized SFX."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.is_available = True
            self._build_catalog()
        except Exception:
            # Fallback gracefully in headless / CI environments without sound devices
            self.is_available = False

    def _build_catalog(self) -> None:
        """Synthesize and register all SFX."""
        pop = synth_mob_pop()
        if pop:
            self.sounds["mob_pop"] = pop

        clash = synth_mob_clash()
        if clash:
            self.sounds["mob_clash"] = clash

        summon = synth_champion_summon()
        if summon:
            self.sounds["champion_summon"] = summon

        stomp = synth_champion_stomp()
        if stomp:
            self.sounds["champion_stomp"] = stomp

        brick = synth_brick_chip()
        if brick:
            self.sounds["brick_chip"] = brick

        coin = synth_coin()
        if coin:
            self.sounds["coin"] = coin

        win = synth_win_fanfare()
        if win:
            self.sounds["win"] = win

        lose = synth_game_over()
        if lose:
            self.sounds["lose"] = lose

        # Ascending diatonic scale for multiplier gates (C5, D5, E5, F5, G5, A5, B5, C6)
        scale_frequencies = [
            523.25, 587.33, 659.25, 698.46,
            783.99, 880.00, 987.77, 1046.50
        ]
        self.gate_chimes = []
        for freq in scale_frequencies:
            chime = synth_gate_chime(frequency=freq)
            if chime:
                self.gate_chimes.append(chime)

        self._apply_volume()

    def update(self, dt: float) -> None:
        """Update cooldown timers."""
        for k in self.timers:
            if self.timers[k] > 0.0:
                self.timers[k] = max(0.0, self.timers[k] - dt)

    def play(self, sound_name: str) -> None:
        """Play a cached sound effect if available, not muted, and not on cooldown."""
        if not self.is_available or self.is_muted:
            return

        # Check cooldown
        if sound_name in self.timers and self.timers[sound_name] > 0.0:
            return

        sound = self.sounds.get(sound_name)
        if sound:
            sound.play()
            if sound_name in self.timers:
                self.timers[sound_name] = self.cooldowns.get(sound_name, 0.05)

    def play_gate_chime(self, combo_index: int = 0) -> None:
        """Play ascending chime based on multiplier combo intensity."""
        if not self.is_available or self.is_muted or not self.gate_chimes:
            return

        if self.timers.get("gate_chime", 0.0) > 0.0:
            return

        idx = combo_index % len(self.gate_chimes)
        self.gate_chimes[idx].play()
        self.timers["gate_chime"] = self.cooldowns.get("gate_chime", 0.06)

    def toggle_mute(self) -> bool:
        """Toggle mute state on/off."""
        self.is_muted = not self.is_muted
        return self.is_muted

    def set_volume(self, volume: float) -> None:
        """Set master volume [0.0, 1.0]."""
        self.master_volume = max(0.0, min(1.0, volume))
        self._apply_volume()

    def _apply_volume(self) -> None:
        for sound in self.sounds.values():
            sound.set_volume(self.master_volume)
        for chime in self.gate_chimes:
            chime.set_volume(self.master_volume)

    @classmethod
    def get_instance(cls) -> "AudioManager":
        if cls._instance is None:
            cls._instance = AudioManager()
        return cls._instance
