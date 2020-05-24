import socketio
import copy
from module.shitty_math import compare
import random
import pygame


class Interactive(socketio.ClientNamespace):
    def __init__(self, game, *args):
        super().__init__(*args)
        self.game = game

    def on_message(self, data):
        print('Received: ' + str(data))

    def on_error(self, data):
        print('Received Error: ' + str(data))

    def on_ping(self, data):
        if data == self.game.sio.sid:
            return
        self.emit('pong', self.game.sio.sid)

    def on_connect(self):
        print('Connected to Server')
        self.do_authentication()

    def do_authentication(self):
        player = self.game.player
        self.emit('authentication', data=player)

    def on_player_info(self, data):
        self.game.player['wind'] = data['wind']
        #  add more if needed in the future...

    def on_game_start(self, _):
        self.game.start = True

    def on_draw_tile(self, data: dict):
        tile = copy.deepcopy(self.game.tiles[data['tile']])
        tile.load_tile()
        if data['special']:
            tile.load_board()
            self.game.board.append(tile)
        else:
            self.game.hand.append(tile)

    def on_first_status(self, data: dict):
        player_wind = self.game.player['wind']

        self.game.isTurn = data[player_wind]['turn']

        if player_wind == 'east':
            self.game.enemy_pos = {'front': 'west', 'left': 'north', 'right': 'south'}
        elif player_wind == 'south':
            self.game.enemy_pos = {'front': 'north', 'left': 'east', 'right': 'west'}
        elif player_wind == 'west':
            self.game.enemy_pos = {'front': 'east', 'left': 'south', 'right': 'north'}
        elif player_wind == 'north':
            self.game.enemy_pos = {'front': 'south', 'left': 'west', 'right': 'east'}

        for pos, wind in self.game.enemy_pos.items():
            for i in data[wind]['board']:
                tile = copy.deepcopy(self.game.tiles[i])
                tile.load_tile('enemy', pos)
                self.game.enemy_board[pos].append(tile)
            self.game.enemy_board[pos].sort(key=lambda x: x.name)
        self.game.hand.sort(key=lambda x: x.name)
        self.game.board.sort(key=lambda x: x.name)

    def on_status(self, data: dict):
        #  1) update enemy board
        for pos, wind in self.game.enemy_pos.items():
            old_board = [i.name for i in self.game.enemy_board[pos]]
            dif = compare(data[wind]['board'], old_board)
            for i in dif:
                tile = copy.deepcopy(self.game.tiles[i])
                tile.load_tile('enemy', pos)
                self.game.enemy_board[pos].append(tile)

        #  2) update ffa (NOTE: DO NOT SORT FFA)
        #     check if FFA is append or call (to remove)
        player_call = data.get('call', False)
        if player_call:
            if data.get('remove_ffa', False):
                del self.game.ffa[-1]
        else:
            old_ffa = [i.name for i in self.game.ffa]
            dif = compare(data['ffa'], old_ffa)
            for i in dif:
                tile = copy.deepcopy(self.game.tiles[i])
                tile.load_tile('ffa')
                self.game.lblLastThrown.text = f'Last Thrown: {i}'
                self.game.ffa.append(tile)

        #  3) Update Hand if call is called
        player_wind = self.game.player['wind']
        if player_call:
            res = data.get('remove', False)
            if res and data['remove']['player'] == player_wind:
                tiles = data['remove']['tiles']
                for i in tiles:
                    tile_index = [idx for idx, t in enumerate(self.game.hand) if t.name == i]
                    del self.game.hand[tile_index[0]]

        #  4) Update Self Board if call is called (Pong)
        if player_call:
            old_board = [i.name for i in self.game.board]
            dif = compare(data[player_wind]['board'], old_board)
            for i in dif:
                tile = copy.deepcopy(self.game.tiles[i])
                tile.load_tile('board')
                self.game.board.append(tile)

        #  5) Check if call is called (Chi)
        if player_call:
            pattern = data.get('pattern', False)
            if pattern is not False:
                self.game.possibleCheck = True
                for tileLst in pattern:
                    tmp = []
                    for i in tileLst:
                        tile = copy.deepcopy(self.game.tiles[i])
                        tile.load_tile('possible')
                        tmp.append(tile)
                    self.game.possible_tiles.append(tmp)
        #  6) Clear possible_tiles (timer ran out and random)
        if player_call:
            check = data.get('random_chi', False)
            if check:
                self.game.possibleCheck = False
                self.game.possible_tiles.clear()

        #  7) Check if turn
        self.game.isTurn = data[player_wind]['turn']

    def on_player_hu(self, data: dict):
        if data['info']['name'] == self.game.player['name']:
            #  dont display yes no button
            pass
        else:
            self.game.show_hu_btn = True
            # self.game.ffa.clear()
            tiles = data['tiles']
            for i in tiles:
                tile = copy.deepcopy(self.game.tiles[i])
                tile.load_tile('hu')
                self.game.hu_tiles.append(tile)

    def on_next_game(self, data):
        self.game.hand = []
        self.game.ffa = []
        self.game.board = []
        self.game.hu_tiles = []
        self.game.enemy_board = {'front': [], 'left': [], 'right': []}

        self.game.show_hu_btn = False
        for i in self.game.hu_decision_btn:
            i.show = True

        self.game.player['wind'] = data['player'][self.game.player['name']]['wind']
        self.game.table = data['table']
        self.emit('start', data='')
