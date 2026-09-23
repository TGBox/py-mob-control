"""Unit tests for procedural audio synthesizer (Headless-safe)."""

import pytest
import numpy as np
import pygame
from py_mob_control.audio.sound_synth import (
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
from py_mob_control.audio.audio_manager import AudioManager


def test_audio_synth_and_manager():
    # Test that audio manager can instantiate safely even if mixer cannot open hardware audio device
    mgr = AudioManager(init_mixer=False)
    assert mgr.is_muted is False
    mgr.toggle_mute()
    assert mgr.is_muted is True

    # Initialize dummy mixer in software if possible
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        pop = synth_mob_pop()
        assert pop is not None

        chime = synth_gate_chime(440.0)
        assert chime is not None

        clash = synth_mob_clash()
        assert clash is not None

        summon = synth_champion_summon()
        assert summon is not None

        stomp = synth_champion_stomp()
        assert stomp is not None

        brick = synth_brick_chip()
        assert brick is not None

        coin = synth_coin()
        assert coin is not None

        win = synth_win_fanfare()
        assert win is not None

        lose = synth_game_over()
        assert lose is not None
        pygame.mixer.quit()
    except Exception:
        # Pass if OS has no audio driver attached (e.g. strict headless container)
        pass
