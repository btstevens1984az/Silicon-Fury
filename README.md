# SILICON FURY

**Brand Brawl** — a Tekken-style 2D fighter where PC makers collide with silicon titans.

Built in **Python + pygame** with **Tekken-inspired 3D fighter renders**, unique character designs per brand, blood hit FX, and a neon arena stage.

Local vs local, vs CPU, and Story Mode. Every fighter has Tekken-style attributes and a signature special.

<p align="center">
  <img src="media/gifs/03-versus-brawl.gif" alt="Versus brawl gameplay" width="100%" />
</p>

---

## Live gameplay

### 1. Title & teams

![Title and teams](media/gifs/01-title-teams.gif)

### 2. Character select

![Character select](media/gifs/02-character-select.gif)

### 3. Versus brawl

![Versus brawl](media/gifs/03-versus-brawl.gif)

### 4. Special moves

![Special moves](media/gifs/04-special-moves.gif)

### 5. Story mode K.O.

![Story mode KO](media/gifs/05-story-ko.gif)

---

## Teams & roster

### Team Computer
| Fighter | Special | Playstyle |
|---|---|---|
| **DELL** | POWEREDGE SLAM | Tanky enterprise bruiser |
| **HP** | LASERJET BARRAGE | Mid-range pressure |
| **LENOVO** | THINKPAD STRIKE | High defense / counter |
| **ASUS** | ROG RAMPAGE | Fast RGB rushdown |

### Team Tech
| Fighter | Special | Playstyle |
|---|---|---|
| **IBM** | WATSON WAVE | Heavy AI zoning |
| **INTEL** | CORE MELTDOWN | Overclocked flurry |
| **AMD** | RYZEN RUSH | Multi-hit chipset smash |
| **NVIDIA** | CUDA CANNON | High-damage beam special |

Each fighter has **HP · Power · Speed · Defense · Reach · Special** ratings (Tekken-style attribute spread).

---

## Modes

| Mode | Description |
|---|---|
| **1v1 Versus** | Two players, one keyboard |
| **1v PC** | Fight a CPU from the rival team |
| **Story Mode** | Climb the opposing roster — branded rivals wait at the end |

---

## Controls

| Action | Player 1 | Player 2 |
|---|---|---|
| Move | `A` `D` | `←` `→` |
| Jump | `W` | `↑` |
| Block | `S` | `↓` |
| Punch | `J` | `N` |
| Kick | `K` | `M` |
| **Special** (meter ≥ 60%) | `L` | `,` |

Menu: `Enter` confirm · `Esc` back · `Tab` switch team on select screen.

---

## Install & run

### Requirements
- Python **3.10+**
- `pygame 2.6+`

### Linux / macOS

```bash
git clone https://github.com/btstevens1984az/Silicon-Fury.git
cd Silicon-Fury
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Windows (PowerShell)

```powershell
git clone https://github.com/btstevens1984az/Silicon-Fury.git
cd Silicon-Fury
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### Regenerate demo GIFs

```bash
./scripts/make_gifs.sh
```

---

## Project layout

```text
Silicon-Fury/
├── main.py                 # Entry point
├── silicon_fury/
│   ├── characters.py       # Roster + attributes + specials
│   ├── fighter.py          # Movement, combat, rendering
│   ├── ai.py               # CPU brain
│   ├── game.py             # Menus, modes, fight loop, demos
│   └── config.py
├── media/gifs/             # Live gameplay GIFs
├── scripts/make_gifs.sh
└── requirements.txt
```

---

## License

MIT — see [LICENSE](LICENSE).

> Brand names are used fictitiously for parody/fan-game entertainment. Not affiliated with Dell, HP, Lenovo, ASUS, IBM, Intel, AMD, NVIDIA, or Bandai Namco.
