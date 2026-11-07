# ⚽ AI Football Commentary

[![Last tested: 2023](https://img.shields.io/badge/last%20tested-2023-orange)](#️-historical-project)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Python 3](https://img.shields.io/badge/python-3-blue)](https://www.python.org)

**Live, AI-generated audio commentary for football matches played in
[Google Research Football](https://github.com/google-research/football).**

While you play the game, the script watches the match, reports notable
events — possession changes, set pieces, cards, goals — to **GPT-3**, and
speaks the generated commentary aloud through a local
[OpenTTS](https://github.com/synesthesiam/opentts) server. The result is a
full audio commentary of your match, produced in real time.

Developed in **2023** as part of my bachelor's thesis.

## The idea

The commentary is produced as a running dialogue between two personas, kept
in a single GPT-3 conversation so the commentator remembers the whole match:

- **AGENT** — the match reporter: receives dry, factual descriptions of match
  events (*"In 23 minute, there is goal for Real, scored by Benzema"*).
- **DARIUS** — the football commentator: turns each report into a live
  commentary line, which is then spoken aloud.

```text
AGENT: In 23 minute, there is goal for Real, scored by Benzema
DARIUS: Benzema! The Frenchman has been a menace all evening and Real
        Madrid finally have their breakthrough at the Bernabeu!
```

*(illustrative example of generated output)*

### Commentated events

| Event                                | Detected via        | Output |
| ------------------------------------ | ------------------- | ------ |
| Welcome speech (teams, stadium, key players) | match start  | spoken |
| Kick-off                             | game mode change    | console |
| Goal kick                            | game mode change    | spoken |
| Offside / free kick                  | game mode change    | spoken |
| Corner                               | game mode change    | spoken |
| Throw-in                             | game mode change    | spoken |
| Penalty                              | game mode change    | spoken |
| Periodic score & status update       | back to normal play | console |
| Yellow card                          | card counters       | spoken |
| Goal (with scorer)                   | score change        | spoken |
| Full-time summary                    | match end / Ctrl+C  | spoken |

The fixture is fixed to **Real Madrid vs Manchester United** at the
Santiago Bernabéu, with named line-ups (see `PLAYER_NAMES` in
[`play_game.py`](play_game.py)).

## Requirements

- Python 3 on Linux or macOS (see the
  [GFootball README](https://github.com/google-research/football) for
  platform notes; Windows users can use WSL or Docker)
- [Google Research Football](https://github.com/google-research/football)
- An OpenAI API key with access to `text-davinci-003` (legacy)
- [OpenTTS](https://github.com/synesthesiam/opentts) running locally with a
  MaryTTS voice

## Installation

1. **Install [Google Research Football](https://github.com/google-research/football)**
   (see its README for full instructions and system dependencies):

   ```bash
   python3 -m pip install gfootball
   ```

2. **Install the OpenAI SDK** — it must be a pre-1.0 release, since the code
   uses the legacy `openai.Completion.create` API (see
   [Historical project](#️-historical-project)):

   ```bash
   python3 -m pip install "openai<1.0"
   ```

3. **Replace `play_game.py`** in the installed `gfootball` package with the
   one from this repository. Locate the package first:

   ```bash
   python3 -c "import gfootball, os; print(os.path.dirname(gfootball.__file__))"
   ```

4. **Configure your OpenAI API key** — either export it as an environment
   variable (recommended):

   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

   or paste it directly into `play_game.py` (as in the original version of
   this script).

5. **Start the OpenTTS server** (provides the MaryTTS voice
   `dfki-spike-hsmm` used by the commentary):

   ```bash
   docker run -it -p 5500:5500 synesthesiam/opentts:en
   ```

## Usage

Play a match with full keyboard control and live commentary:

```bash
python3 -m gfootball.play_game --action_set=full
```

Press `Ctrl+C` in the terminal to quit — DARIUS will wrap up with a
full-time summary before the game shuts down.

### Keyboard controls (per GFootball)

| Key         | Attack mode          | Defense mode            |
| ----------- | -------------------- | ----------------------- |
| Arrow keys  | Move                 | Move                    |
| `S`         | Short pass           | Pressure                |
| `A`         | High pass            | Sliding                 |
| `D`         | Shot                 | Team pressure           |
| `W`         | Long pass            | Goalkeeper pressure     |
| `Q`         | —                    | Switch active player    |
| `C`         | Dribble              | —                       |
| `E`         | Sprint               | Sprint                  |

### Command-line flags

| Flag            | Default                   | Description                              |
| --------------- | ------------------------- | ---------------------------------------- |
| `--players`     | `keyboard:left_players=1` | Semicolon-separated list of players      |
| `--level`       | *(empty)*                 | Scenario/level to play                   |
| `--action_set`  | `default`                 | Action set: `default` or `full`          |
| `--real_time`   | `True`                    | Slow the game down to real time          |
| `--render`      | `True`                    | Render the game on screen                |

## Code overview

Everything lives in a single file, [`play_game.py`](play_game.py), which is
a modified version of GFootball's script of the same name:

- `PLAYER_NAMES` — squads of the two teams, indexed by `(team, player)`
- `gpt3_completion()` — the GPT-3 call (legacy pre-1.0 OpenAI API)
- `speak()` — speech synthesis through the local OpenTTS server
- `commentate()` — turns one match event into an AGENT/DARIUS dialogue turn
- `main()` — the game loop that detects events from the environment
  observations

## ⚠️ Historical project

This project was developed and last verified end-to-end in **2023**. Since
then, parts of the surrounding ecosystem have changed, so **the setup
instructions above may be (partially) obsolete**:

- `text-davinci-003` has been retired by OpenAI, and the pre-1.0
  `openai` Python SDK this code uses (`openai.Completion.create`) no longer
  exists in current SDK versions.
- GFootball and OpenTTS installation procedures may have changed since
  2023.

The code is **intentionally preserved as it was tested for the thesis** —
no API migrations or updates for newer versions. It documents what was
built and how it worked at the time.

## Known quirks (preserved intentionally)

To keep the code faithful to the version tested in 2023, one quirk of
the original implementation is preserved:

- Each spoken commentary line opens a new browser tab (this is how audio
  playback was implemented).

## License

[Apache License 2.0](LICENSE). This project is based on
[`play_game.py`](https://github.com/google-research/football) from Google
Research Football (Copyright 2019 Google LLC), modified for AI Football
Commentary.
