# SILICON FURY

**Brand Brawl** — a 2D fighter where PC makers collide with silicon titans.

Built in **Python + pygame**, with **articulated limb combat** (walk, punch, kick, air kick, dash, specials), blood/fire hit FX, and a neon arena stage.

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

## What's new

- **No black boxes** — fighters are drawn with opaque articulated limbs (no sprite rotation artifacts)
- **Nimble combat** — walk cycles, punches, kicks, air kicks, double-jump, and dash
- **Brand kits** — each fighter has a unique silhouette, armor style, and hair
- **Explosive FX** — blood, fire, shockwaves, and screen shake on big hits

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
| Dash | `Shift` + `A`/`D` | `RShift` + `←`/`→` |
| Jump (double-jump OK) | `W` | `↑` |
| Block | `S` | `↓` |
| Punch (air OK) | `J` | `N` |
| Kick / air kick | `K` | `M` |
| **Special** (meter ≥ 55%) | `L` | `,` |

Menu: `Enter` confirm · `Esc` back · `Tab` switch team on select screen.

---

## Install & run

### Requirements
- Python **3.10+**
- `pygame-ce` (or `pygame`) **2.5+**
- `Pillow`

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

Requires `ffmpeg`.

---

## Project layout

```text
Silicon-Fury/
├── main.py                 # Entry point
├── silicon_fury/
│   ├── characters.py       # Roster + attributes + specials
│   ├── body.py             # Articulated fighter rendering
│   ├── fighter.py          # Movement, combat
│   ├── effects.py          # Blood / fire / explosions
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
