# Py-Mob-Control (Python Desktop Edition)

Eine moderne, performante Desktop-Adaption des beliebten Mobile-Hits **Mob Control** in reinem Python mit **pygame-ce**, NumPy-Synthese und dynamischem Widescreen/Ultrawide-Support.

---

## 🌟 Highlights & Features

- **Schwarm-Physik & Performance**: 2D Spatial Hash Grid ermöglicht flüssige 60 FPS bei über 1.000 Einheiten gleichzeitig mit sanftem Crowd-Flocking.
- **Widescreen & Ultrawide (21:9)**: Zentrales, hochauflösendes Spielfeld mit dynamischen Seitenpanels (Live-Battle-Radar, DPS, Einheiten-Zähler, Mini-Map und Steuerungs-Cheatsheet).
- **Echter Fullscreen-Modus**: Umschalten zwischen skalierbarem Fenster und echtem Vollbild mit `F11`.
- **Zero External Assets**: Alle Grafiken, Shader/Glow-Effekte, Partikel und Sounds werden 100 % prozedural im Code generiert – keine externen PNGs oder WAVs erforderlich!
- **Prozedurales NumPy-Sound-Design**:
  - Organische Pop-Sounds beim Feuern
  - Aufsteigende diatonische Tonleitern (Chimes) bei Multiplikator-Durchläufen
  - Satter Bass-Impact bei Champion-Tritten mit Screen-Shake
  - Knackige Brick-Chipping- und Münz-Sounds
  - Mute-Taste (`M`) jederzeit verfügbar
- **Vollständiger Core Loop**:
  - Dynamische Multiplikator-Tore (`+N`, `xN`, `SPEED`, Oszillierend, Ping-Pong)
  - Feindliche Gegenkanonen und Wellen-Türme
  - Champion-Beschwörung (Riesen mit hoher Lebensenergie und Flächenschaden)
  - **Brick-Looting-Endphase**: Nach dem Zerstören der Festung plündern überlebende Mobs die Trümmer, während Bricks in parabolischen Flugbahnen ins Konto fliegen!
- **Meta-Progression & Basisausbau**:
  - Kanonen-Feuerrate, Mob-Geschwindigkeit und Champion-Stärke mit Coins leveln
  - Rathaus und Ziegelfabrik mit Bricks ausbauen (passive Boni auf Münzen & Beute)
  - Automatisches, manipulationssicheres JSON-Savegame (`savegame.json`)
- **Endlose Level-Skalierung**: 5 handgebaute Tutorial-Level + deterministischer prozeduraler Generator für unendliche Sektoren ab Level 6.

---

## 🎮 Steuerung

| Aktion | Maus | Tastatur |
| :--- | :--- | :--- |
| **Kanone zielen** | Mauszeiger bewegen | `A` / `D` oder `Pfeil Links` / `Pfeil Rechts` |
| **Mobs abfeuern** | Linke Maustaste halten | `Leertaste` halten |
| **Champion rufen** | Rechte Maustaste | `Q` / `E` / `1` / `2` |
| **Vollbild umschalten** | — | `F11` |
| **Audio stumm/aktiv** | — | `M` |
| **Pause / Zurück zum HQ** | — | `ESC` |
| **Deploy / Start** | Klick auf "Deploy" | `Enter` / `Leertaste` |
| **Schnell-Upgrades (HQ)** | Klick auf Buttons | Tasten `1` bis `5` |

---

## 🚀 Installation & Start

Das Projekt nutzt `uv` für die Python-Umgebungs- und Paketverwaltung.

```bash
# Virtuelle Umgebung synchronisieren
uv sync

# Spiel starten
uv run py-mob-control
# oder direkt:
uv run python -m py_mob_control.main
```

---

## 🧪 Tests ausführen

Das Projekt verfügt über eine umfassende Test-Suite mit Headless-Smoke-Tests und Unit-Tests für Physik, Mathematik-Tore, Speicherstand und Audio-Synthese:

```bash
uv run pytest
```
