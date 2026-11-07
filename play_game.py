# coding=utf-8
# Copyright 2019 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modifications for AI Football Commentary
# (https://github.com/Alpaczyk/AiFootballCommentary):
# Copyright 2023 Michal Czaplicki, licensed under the Apache License,
# Version 2.0.

"""Play a Google Research Football match with live AI commentary.

This is a modified version of GFootball's ``play_game.py``. While a match
is being played, the script observes the game state, detects commentary-
worthy events (possession changes, set pieces, cards, goals) and feeds
them to GPT-3 as a running dialogue between two personas:

  * AGENT  - the match reporter, supplying dry, factual event
    descriptions,
  * DARIUS - the football commentator, turning them into live
    commentary.

Every DARIUS response is spoken aloud through a local OpenTTS server
(MaryTTS voice), giving the match a real-time audio commentary.

The commentary assumes a fixed fixture: Real Madrid vs Manchester United
in the Santiago Bernabeu stadium, with named line-ups (see
``PLAYER_NAMES``).

This code was written for a bachelor thesis in 2023 and is preserved as
it was last tested then: it relies on the pre-1.0 OpenAI Python API and
the ``text-davinci-003`` model (since retired by OpenAI).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys
import webbrowser

from absl import app
from absl import flags
from absl import logging

import openai

from gfootball.env import config
from gfootball.env import football_env

FLAGS = flags.FLAGS

flags.DEFINE_string('players', 'keyboard:left_players=1',
                    'Semicolon separated list of players, single keyboard '
                    'player on the left by default')
flags.DEFINE_string('level', '', 'Level to play')
flags.DEFINE_enum('action_set', 'default', ['default', 'full'], 'Action set')
flags.DEFINE_bool('real_time', True,
                  'If true, environment will slow down so humans can play.')
flags.DEFINE_bool('render', True, 'Whether to do game rendering.')

# OpenAI API key. Alternatively, paste your key here directly, as in the
# original version of this script.
openai.api_key = os.environ.get('OPENAI_API_KEY', 'api_key')

# The commented fixture. Team 0 is the left team, team 1 the right team.
HOME_TEAM = 'Real Madrid'
AWAY_TEAM = 'Manchester United'

# Player names, indexed by (team, player number).
PLAYER_NAMES = {
    (0, 0): ('Courtois', HOME_TEAM),
    (0, 1): ('Camavinga', HOME_TEAM),
    (0, 2): ('Sergio Ramos', HOME_TEAM),
    (0, 3): ('Militao', HOME_TEAM),
    (0, 4): ('Carvajal', HOME_TEAM),
    (0, 5): ('Modric', HOME_TEAM),
    (0, 6): ('Kross', HOME_TEAM),
    (0, 7): ('Valverde', HOME_TEAM),
    (0, 8): ('Vinicius', HOME_TEAM),
    (0, 9): ('Benzema', HOME_TEAM),
    (0, 10): ('Ronaldo', HOME_TEAM),
    (1, 0): ('De Gea', AWAY_TEAM),
    (1, 1): ('Martinez', AWAY_TEAM),
    (1, 2): ('Maguire', AWAY_TEAM),
    (1, 3): ('Sabitzer', AWAY_TEAM),
    (1, 4): ('Fred', AWAY_TEAM),
    (1, 5): ('Eriksen', AWAY_TEAM),
    (1, 6): ('Casemiro', AWAY_TEAM),
    (1, 7): ('Bruno Fernandes', AWAY_TEAM),
    (1, 8): ('Martial', AWAY_TEAM),
    (1, 9): ('Rashford', AWAY_TEAM),
    (1, 10): ('Garnacho', AWAY_TEAM),
}

# GFootball game modes (see gfootball.env.observation).
GAME_MODE_NORMAL = 0
GAME_MODE_KICKOFF = 1
GAME_MODE_GOAL_KICK = 2
GAME_MODE_FREE_KICK = 3
GAME_MODE_CORNER = 4
GAME_MODE_THROW_IN = 5
GAME_MODE_PENALTY = 6

# Preamble setting up the AGENT/DARIUS dialogue for GPT-3.
COMMENTARY_PREAMBLE = (
    'The following is a conversation between AGENT and DARIUS. DARIUS is a '
    'football commentator, who is getting information about the match from '
    'AGENT. The football match will be between Real Madrid and Manchester '
    'United.')

# Instruction for DARIUS's welcome speech before the kick-off.
WELCOME_INSTRUCTION = (
    'The match will start in a second. Make a welcome talk, where you tell '
    'who is playing, in what stadium (Santiago Bernabeu), and who are the '
    'best players in both teams (Ronaldo, and Rashford)')

# Endpoint of the local OpenTTS server used for speech synthesis.
TTS_URL = ('http://localhost:5500/api/tts?voice=marytts%3Adfki-spike-hsmm'
           '&text={text}%21&vocoder=high&denoiserStrength=0.03&cache=false')


def gpt3_completion(prompt, engine='text-davinci-003', temp=0.7, top_p=1.0,
                    tokens=300, freq_pen=0.5, pres_pen=0.5,
                    stop=['DARIUS:', 'AGENT:']):
  """Generates DARIUS's commentary for the given conversation.

  Uses the legacy (pre-1.0) OpenAI completions API, as in the original
  2023 implementation.
  """
  prompt = prompt.encode(encoding='ASCII', errors='ignore').decode()
  response = openai.Completion.create(
      engine=engine,
      prompt=prompt,
      temperature=temp,
      max_tokens=tokens,
      top_p=top_p,
      frequency_penalty=freq_pen,
      presence_penalty=pres_pen,
      stop=stop)
  return response['choices'][0]['text'].strip()


def speak(text):
  """Reads the commentary text aloud via the local OpenTTS server.

  The synthesized speech is opened (and played) in a new browser tab, as
  in the original implementation.
  """
  # Minimal URL encoding of the text, as in the original implementation.
  encoded = (text.replace(' ', '%20')
                .replace(',', '%2C')
                .replace("'", '%27')
                .replace('!', ''))
  webbrowser.open(TTS_URL.format(text=encoded))


def commentate(prompt, agent_message, voice=True):
  """Has DARIUS comment on an event, returns the updated conversation.

  The event is appended to the conversation as an AGENT message, DARIUS
  (GPT-3) responds with a commentary line, which is spoken (or printed),
  and the extended conversation is returned. Keeping the whole match in a
  single conversation lets DARIUS reference earlier events.
  """
  prompt = prompt + '\nAGENT: ' + agent_message + '\nDARIUS: '
  response = gpt3_completion(prompt)
  if voice:
    speak(response)
  else:
    print(response)
  return prompt + response


def main(_):
  """Plays the game and produces the live AI commentary."""
  players = FLAGS.players.split(';') if FLAGS.players else ''
  assert not (any(['agent' in player for player in players])
             ), ('Player type \'agent\' can not be used with play_game.')
  cfg_values = {
      'action_set': FLAGS.action_set,
      'dump_full_episodes': True,
      'players': players,
      'real_time': FLAGS.real_time,
  }
  if FLAGS.level:
    cfg_values['level'] = FLAGS.level
  cfg = config.Config(cfg_values)
  env = football_env.FootballEnv(cfg)
  if FLAGS.render:
    env.render()
  env.reset()

  if openai.api_key == 'api_key':
    logging.warning('No OpenAI API key found. Set the OPENAI_API_KEY '
                    'environment variable, or paste your key directly into '
                    'play_game.py.')

  # The running AGENT/DARIUS conversation, accumulated over the whole match.
  # The welcome turn opens the dialogue.
  prompt = (COMMENTARY_PREAMBLE + ' AGENT: ' + WELCOME_INSTRUCTION +
            '\nDARIUS: ')
  response = gpt3_completion(prompt)
  speak(response)
  prompt = prompt + response

  # Match state tracked between frames to detect commentary-worthy events.
  score = [0, 0]
  current_state = GAME_MODE_NORMAL
  current_ball_player = -1
  current_home_yellow = 0
  current_away_yellow = 0
  current_home_score = 0
  current_away_score = 0
  last_player = ''
  team_in_possession = ''

  try:
    while True:
      _, _, done, _ = env.step([])
      obs = env.observation()
      minute = str(int(90 - obs['steps_left'] / 33.33))
      home_yellow = sum(obs['left_team_yellow_card'])
      away_yellow = sum(obs['right_team_yellow_card'])
      ball_team = obs['ball_owned_team']
      ball_player = obs['ball_owned_player']
      score = obs['score']

      # Name the player that just got the ball, so that subsequent events
      # can refer to him in the commentary.
      if ball_player != current_ball_player:
        entry = PLAYER_NAMES.get((ball_team, ball_player))
        if entry is not None:
          last_player, team_in_possession = entry
        current_ball_player = ball_player

      # React to a change of the game mode (restarts and set pieces).
      game_mode = obs['game_mode']
      if game_mode != current_state:
        if game_mode == GAME_MODE_KICKOFF:
          print('kickoff')
        elif game_mode == GAME_MODE_GOAL_KICK:
          prompt = commentate(
              prompt,
              f'In {minute} minute, the ball was kicked out from the field '
              f'by {team_in_possession}player, {last_player}')
        elif game_mode == GAME_MODE_FREE_KICK:
          prompt = commentate(
              prompt,
              f'In {minute} minute {last_player} from '
              f'{team_in_possession} is on offside')
        elif game_mode == GAME_MODE_CORNER:
          prompt = commentate(
              prompt,
              f'In {minute} minute, the ball is kicked on corner by '
              f'{last_player}, {team_in_possession} will have a chance')
        elif game_mode == GAME_MODE_THROW_IN:
          prompt = commentate(
              prompt,
              f'In {minute} minute, there is throwout made by {last_player} '
              f'from {team_in_possession}')
        elif game_mode == GAME_MODE_PENALTY:
          prompt = commentate(
              prompt,
              f'In {minute} minute, {last_player} is fouled in penalty box '
              f'and {team_in_possession} will have a penalty')
        elif game_mode == GAME_MODE_NORMAL:
          # Periodic match status updates are printed, not spoken.
          prompt = commentate(
              prompt,
              f'It is {minute} minute of the match, the score is '
              f'{score[0]} to {score[1]}, talk briefly about the situation '
              f'in the match ',
              voice=False)
        current_state = game_mode

      # Cards and goals. Note: the home/away attribution of the yellow card
      # messages is kept verbatim from the original implementation.
      if home_yellow > current_home_yellow:
        prompt = commentate(
            prompt, f'In {minute} minute, there is yellow card for United')
        current_home_yellow = home_yellow
      if away_yellow > current_away_yellow:
        prompt = commentate(
            prompt, f'In {minute} minute, there is yellow card for Real')
        current_away_yellow = away_yellow
      if score[0] > current_home_score:
        prompt = commentate(
            prompt,
            f'In {minute} minute, there is goal for Real, scored by '
            f'{last_player}')
        current_home_score = score[0]
      if score[1] > current_away_score:
        prompt = commentate(
            prompt,
            f'In {minute} minute, there is goal for United, scored by '
            f'{last_player}')
        current_away_score = score[1]

      if done:
        break
  except KeyboardInterrupt:
    pass
  finally:
    if score[0] > score[1]:
      winner = 'for Real Madrid'
    elif score[0] < score[1]:
      winner = 'for Manchester United'
    else:
      winner = 'so it is a draw'
    prompt = commentate(
        prompt,
        f'It is the end of the match, the score is {score[0]} to '
        f'{score[1]} {winner} summarize the match')
    # Print the full AGENT/DARIUS conversation of the match.
    print(prompt)
    env.write_dump('shutdown')
    sys.exit(1)


if __name__ == '__main__':
  app.run(main)
