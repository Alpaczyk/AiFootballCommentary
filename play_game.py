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


"""Script allowing to play the game by multiple players."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app
from absl import flags
from absl import logging


from gfootball.env import config
from gfootball.env import football_env


import os
import openai
import webbrowser


openai.api_key = "api_key"
list = openai.Model.list()

FLAGS = flags.FLAGS

flags.DEFINE_string('players', 'keyboard:left_players=1',
                    'Semicolon separated list of players, single keyboard '
                    'player on the left by default')
flags.DEFINE_string('level', '', 'Level to play')
flags.DEFINE_enum('action_set', 'default', ['default', 'full'], 'Action set')
flags.DEFINE_bool('real_time', True,
                  'If true, environment will slow down so humans can play.')
flags.DEFINE_bool('render', True, 'Whether to do game rendering.')


def gpt3_completion(prompt, engine='text-davinci-003', temp=0.7, top_p=1.0, tokens=300, freq_pen=0.5, pres_pen=0.5, stop=['DARIUS:', 'AGENT:']):
  prompt = prompt.encode(encoding='ASCII', errors='ignore').decode()
  response = openai.Completion.create(
    engine = engine,
    prompt = prompt,
    temperature = temp,
    max_tokens = tokens,
    top_p = top_p,
    frequency_penalty = freq_pen,
    presence_penalty = pres_pen,
    stop = stop
  )
  text = response['choices'][0]['text'].strip()
  return text


def ttsCreator(response):
  tts = response.replace(' ', '%20')
  tts = tts.replace(',', '%2C')
  tts = tts.replace('\'', '%27')
  tts = tts.replace('!', '')
  browser = 'http://localhost:5500/api/tts?voice=marytts%3Adfki-spike-hsmm&text=' + tts + '%21&vocoder=high&denoiserStrength=0.03&cache=false'
  webbrowser.open(browser)
  
def main(_):
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
  try:
    currentState = 0
    currentBallPos = ''
    currentBallTeam = -1
    currentBallPlayer = -1
    currentHomeYellow = 0
    currentAwayYellow = 0
    currentHomeScore = 0
    currentAwayScore = 0
    lastPlayer = ''
    commentary = 'The following is a conversation between AGENT and DARIUS. DARIUS is a football commentator, who is getting information about the match from AGENT. The football match will be between Real Madrid and Manchester United.'
    welcome = commentary + ' AGENT: The match will start in a second. Make a welcome talk, where you tell who is playing, in what stadium (Santiago Bernabeu), and who are the best players in both teams (Ronaldo, and Rashford)'
    prompt = welcome + '\nDARIUS: '
    response = gpt3_completion(prompt)
    ttsCreator(response)
    prompt = prompt + response
    while True:
      _, _, done, _ = env.step([])
      state = env.observation()['game_mode']
      state1 = env.observation()
      timeInt = int(90-(env.observation()['steps_left']/33.33))
      time = str(timeInt)
      homeYellow = sum(env.observation()['left_team_yellow_card'])
      awayYellow = sum(env.observation()['right_team_yellow_card'])
      ballTeam = env.observation()['ball_owned_team']
      ballPlayer = env.observation()['ball_owned_player']
      score = env.observation()['score']
      ballState = env.observation()['ball']
      if ballPlayer != currentBallPlayer:
        if ballTeam == 0 and ballPlayer == 0:
          lastPlayer = 'Courtois'
          currentBallPos = 'Real Madrid'
        if ballTeam == 0 and ballPlayer == 1:
          lastPlayer = 'Camavinga'
          currentBallPos = 'Real Madrid'
        if ballTeam == 0 and ballPlayer == 2:
          lastPlayer = 'Sergio Ramos'
          currentBallPos = 'Real Madrid'
        if ballTeam == 0 and ballPlayer == 3:
          lastPlayer = 'Militao'
          currentBallPos = 'Real Madrid'
        if ballTeam == 0 and ballPlayer == 4:
          lastPlayer = 'Carvajal'
          currentBallPos = 'Real Madrid'
        if ballTeam == 0 and ballPlayer == 5:
          lastPlayer = 'Modric'
          currentBallPos = 'Real Madrid'
        if ballTeam == 0 and ballPlayer == 6:
          lastPlayer = 'Kross'
          currentBallPos = 'Real Madrid'
        if ballTeam == 0 and ballPlayer == 7:
          lastPlayer = 'Valverde'
          currentBallPos = 'Real Madrid'
        if ballTeam == 0 and ballPlayer == 8:
          lastPlayer = 'Vinicius'
          currentBallPos = 'Real Madrid'
        if ballTeam == 0 and ballPlayer == 9:
          lastPlayer = 'Benzema'
          currentBallPos = 'Real Madrid'
        if ballTeam == 0 and ballPlayer == 10:
          lastPlayer = 'Ronaldo'
          currentBallPos = 'Real Madrid'
        if ballTeam == 1 and ballPlayer == 0:
          lastPlayer = 'De Gea'
          currentBallPos = 'Manchester United'
        if ballTeam == 1 and ballPlayer == 1:
          lastPlayer = 'Martinez'
          currentBallPos = 'Manchester United'
        if ballTeam == 1 and ballPlayer == 2:
          lastPlayer = 'Maguire'
          currentBallPos = 'Manchester United'
        if ballTeam == 1 and ballPlayer == 3:
          lastPlayer = 'Sabitzer'
          currentBallPos = 'Manchester United'
        if ballTeam == 1 and ballPlayer == 4:
          lastPlayer = 'Fred'
          currentBallPos = 'Manchester United'
        if ballTeam == 1 and ballPlayer == 5:
          lastPlayer = 'Eriksen'
          currentBallPos = 'Manchester United'
        if ballTeam == 1 and ballPlayer == 6:
          lastPlayer = 'Casemiro'
          currentBallPos = 'Manchester United'
        if ballTeam == 1 and ballPlayer == 7:
          lastPlayer = 'Bruno Fernandes'
          currentBallPos = 'Manchester United'
        if ballTeam == 1 and ballPlayer == 8:
          lastPlayer = 'Martial'
          currentBallPos = 'Manchester United'
        if ballTeam == 1 and ballPlayer == 9:
          lastPlayer = 'Rashford'
          currentBallPos = 'Manchester United'
        if ballTeam == 1 and ballPlayer == 10:
          lastPlayer = 'Garnacho'
          currentBallPos = 'Manchester United'
        currentBallPlayer = ballPlayer
      if state != currentState:
        if state == 1:
          print('kickoff')
        if state == 2:
          prompt = prompt + '\nAGENT: In ' + time + ' minute, the ball was kicked out from the field by ' + currentBallPos + 'player, ' + lastPlayer
          prompt = prompt + '\nDARIUS: '
          response = gpt3_completion(prompt)
          ttsCreator(response)
          prompt = prompt + response
        if state == 3:
          prompt = prompt + '\nAGENT: In ' + time + ' minute ' + lastPlayer + ' from ' + currentBallPos + ' is on offside'
          prompt = prompt + '\nDARIUS: '
          response = gpt3_completion(prompt)
          ttsCreator(response)
          prompt = prompt + response
        if state == 4:
          prompt = prompt + '\nAGENT: In ' + time + ' minute, the ball is kicked on corner by ' + lastPlayer + ', ' + currentBallPos + ' will have a chance'
          prompt = prompt + '\nDARIUS: '
          response = gpt3_completion(prompt)
          ttsCreator(response)
          prompt = prompt + response
        if state == 5:
          prompt = prompt + '\nAGENT: In ' + time + ' minute, there is throwout made by ' + lastPlayer + ' from ' + currentBallPos
          Prompt = prompt + '\nDARIUS: '
          response = gpt3_completion(prompt)
          ttsCreator(response)
          prompt = prompt + response
        if state == 6:
          prompt = prompt + '\nAGENT: In ' + time + ' minute, ' + lastPlayer + ' is fouled in penalty box and ' + currentBallPos + ' will have a penalty'
          prompt = prompt + '\nDARIUS: '
          response = gpt3_completion(prompt)
          ttsCreator(response)
          prompt = prompt + response
        if state == 0:
          prompt = prompt + '\nAGENT: It is ' + time + ' minute of the match, the score is ' + str(score[0]) + ' to ' + str(score[1]) + ', talk briefly about the situation in the match '
          prompt = prompt + '\nDARIUS: '
          response = gpt3_completion(prompt)
          print(response)
          prompt = prompt + response
        currentState = state
      if homeYellow > currentHomeYellow:
        prompt = prompt + '\nAGENT: In ' + time + ' minute, there is yellow card for United'
        prompt = prompt + '\nDARIUS: ' 
        response = gpt3_completion(prompt)
        ttsCreator(response)
        prompt = prompt + response
        currentHomeYellow = homeYellow
      if awayYellow > currentAwayYellow:
        prompt = prompt + '\nAGENT: In ' + time + ' minute, there is yellow card for Real'
        prompt = prompt + '\nDARIUS: ' 
        response = gpt3_completion(prompt)
        ttsCreator(response)
        prompt = prompt + response
        currentAwayYellow = awayYellow
      if score[0] > currentHomeScore:
        prompt = prompt + '\nAGENT: In ' + time + ' minute, there is goal for Real, scored by ' + lastPlayer
        prompt = prompt + '\nDARIUS: ' 
        response = gpt3_completion(prompt)
        ttsCreator(response)
        prompt = prompt + response
        currentHomeScore = score[0]
      if score[1] > currentAwayScore:
        prompt = prompt + '\nAGENT: In ' + time + ' minute, there is goal for United, scored by ' + lastPlayer
        prompt = prompt + '\nDARIUS: ' 
        response = gpt3_completion(prompt)
        ttsCreator(response)
        prompt = prompt + response
        currentAwayScore = score[1]
      
      if done:
        break
  except KeyboardInterrupt:
    pass
  finally:
    if score[0] > score[1]:
      winner= 'for Real Madrid'
    if score[0] < score[1]:
      winner= 'for Manchester United'
    if score[0] == score[1]:
      winner= 'so it is a draw'
    prompt = prompt + '\nAGENT: It is the end of the match, the score is ' + str(score[0]) + ' to ' + str(score[1]) + ' ' + winner + ' summarize the match'
    prompt = prompt + '\nDARIUS: ' 
    response = gpt3_completion(prompt)
    prompt = prompt + response
    print(prompt)
    ttsCreator(response)
    env.write_dump('shutdown')
    exit(1)


if __name__ == '__main__':
  app.run(main)
