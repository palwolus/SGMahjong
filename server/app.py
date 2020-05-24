import eventlet

eventlet.monkey_patch()

from flask import Flask, request
from flask_socketio import SocketIO, emit, Namespace, disconnect
from Game import Game
import argparse
import random

app = Flask(__name__)
app.secret_key = 'SECRET'
socketio = SocketIO(app, async_mode='eventlet')


class Interactive(Namespace):
    def __init__(self, *args):
        super().__init__(*args)
        self.players = []
        self.status = []
        self.game = None
        self.restart_count = 0

    def on_connect(self):
        print('Connected')

    def on_disconnect(self):
        print('Disconnected')

    def on_authentication(self, data: dict):
        #  Check Key Length
        if len(data['key']) < 10:
            self.emit('error', 'key length too short', room=request.sid)
            disconnect(request.sid)
            return

        #  Check number of players
        data['sid'] = request.sid
        data['status'] = False
        self.players.append(data)
        self.emit('message', 'Welcome to Server', room=request.sid)
        print(data['name'] + ' has joined the server')

    def on_request_ping(self, data):
        #  Set all status to False and the person who request to True
        for i in self.players:
            if i['sid'] == data:
                i['status'] = True
                print(f'Ping Requested: {i["name"]}')
            else:
                i['status'] = False
        self.emit('ping', data)

    def on_pong(self, data):
        #  On receiving 'pong', set status to True
        for i in self.players:
            if i['sid'] == data:
                i['status'] = True
                print(f'Received Pong: {i["name"]}')

    def on_request_start(self, _):
        # make sure all are ready
        clear_false = False
        for i in self.players:
            if i['status'] is False:
                clear_false = True
                break

        # remove those that probably dc or something
        if clear_false:
            print('Clearing Disconnected Players')
            self.players = [d for d in self.players if d['status'] is True]
        if len(self.players) == 4:
            #  load game tiles (might lag)
            game = Game(self.emit, app)
            game.load_tiles()
            #  shuffle works in place
            random.shuffle(self.players)
            #  add players
            for i in self.players:
                game.add_player(i['name'], i['money'], i['key'], i['sid'])

            self.emit('game_start', data='')
            game.start()
            self.game = game
            #  emit to tell draw 14 to blah blah blah ya
        else:
            print('Not enough players to start')
            self.emit('error', data=f'Player Count: {len(self.players)}')

    def on_throw_tile(self, data):
        player = [i for i in self.game.players if i.key == data['key']][0]
        tile = player.throw_tile(data['tile'])
        self.game.ffa.append(tile)
        self.game.send_status(do_thread=True)

    def on_call_chi_check(self, data: dict):
        #  Conditions
        #  1) Player whom threw the tile is unable to call (self.game.curTurnPlayer)
        player = [i for i in self.game.players if i.key == data['key']][0]
        if self.game.curTurnPlayer == player:
            self.emit('error', 'You fking kidding me? You threw a tile and called chi?', room=player.sid)
            return

        #  2) Unable to call chi after lock (Timer)
        if not self.game.lock:
            self.emit('error', 'Timer is over/no one threw a tile yet', room=player.sid)
            return

        #  3) Tile is not Big Tile
        previous_tile = self.game.curTurnPlayer.lastThrow
        if previous_tile.type in ['big', 'animal', 'flower']:
            self.emit('error', 'You call Chi on Big tiles? you brainless?', room=player.sid)
            return

        #  3)  Left side player threw the tile (You are on the right to chi)
        if self.game.nextTurn[self.game.curTurnPlayer.wind] != player.wind:
            self.emit('error', 'You retard? You think you can eat any time is it? idiot', room=player.sid)
            return

        #  4) No one called Superior (Pong, Kang, Hu)
        if self.game.btn_detect['type'] == 'hu':
            self.emit('error', 'Someone called Hu. You suck', room=player.sid)
            return
        elif self.game.btn_detect['type'] == 'kang':
            self.emit('error', 'Someone called Kang. You suck', room=player.sid)
            return
        elif self.game.btn_detect['type'] == 'pong':
            self.emit('error', 'Someone called Pong. You suck', room=player.sid)
        elif self.game.btn_detect['type'] == 'chi':
            self.emit('error', 'YOU ALREADY CALLED CHI YOU FUCKER! JUST WAIT 3 SECOND', room=player.sid)
            return

        #  5) Tiles must match Mahjong Rules
        previous_tile = self.game.curTurnPlayer.lastThrow
        rule_match = player.call_chi_check(previous_tile)
        if rule_match:
            print(f'Player Chi: {player.name}')
            if type(rule_match) == dict:
                del self.game.ffa[-1]
                self.game.btn_detect = {'type': 'chi', 'target': player, 'draw': False,
                                        'extra': {'multiple': False, 'call': True, 'remove': rule_match,
                                                  'remove_ffa': True}}
            else:
                self.game.btn_detect = {'type': 'chi', 'target': player, 'draw': False,
                                        'extra': {'call': True, 'multiple': True,
                                                  'pattern': rule_match, 'room': player.sid,
                                                  'player': player, 'previous_tile': previous_tile}}
        else:
            self.emit('error', 'You sure you got the required tiles? bloody idiot', room=player.sid)

    def on_call_chi_after(self, data):
        self.game.skipTurn = True
        player = self.game.savedPattern['player']
        previous_tile = self.game.savedPattern['previous_tile']
        pattern = self.game.savedPattern['pattern']
        self.game.savedPattern = None
        data = player.call_chi(pattern[data['select']], previous_tile, True)
        target, draw, extra = data['target'], data['draw'], data['extra']
        del self.game.ffa[-1]
        self.game.next_turn(target=target, draw=draw, extra=extra)

    def on_call_pong(self, data: dict):
        #  Conditions
        #  1) Player whom threw the tile is unable to call (self.game.curTurnPlayer)
        player = [i for i in self.game.players if i.key == data['key']][0]
        if self.game.curTurnPlayer == player:
            self.emit('error', 'You fking kidding me? You threw a tile and called pong?', room=player.sid)
            return

        #  2) Unable to call pong after lock (timer)
        if not self.game.lock:
            self.emit('error', 'Timer is over/no one threw a tile yet', room=player.sid)
            return

        #  3) No one called Superior (Kang, Hu)
        if self.game.btn_detect['type'] == 'hu':
            self.emit('error', 'Someone called Hu. You suck', room=player.sid)
            return
        elif self.game.btn_detect['type'] == 'kang':
            self.emit('error', 'Someone called Kang. You suck', room=player.sid)
            return
        elif self.game.btn_detect['type'] == 'pong':
            self.emit('error', 'YOU ALREADY CALLED PONG YOU FUCKER! JUST WAIT 3 SECOND', room=player.sid)
            return

        #  4) Tiles must match Mahjong Rules
        previous_tile = self.game.curTurnPlayer.lastThrow
        rule_match = player.call_pong(previous_tile)
        if rule_match:
            print(f'Player Pong: {player.name}')
            #  Remove from FFA
            del self.game.ffa[-1]
            self.game.btn_detect = {'type': 'pong',
                                    'target': player,
                                    'draw': False,
                                    'extra': {'call': True, 'remove': rule_match, 'remove_ffa': True}}
        else:
            self.emit('error', 'You sure you got the required tiles? bloody idiot', room=player.sid)

    def on_call_kang(self, data):
        #  Conditions
        #  1) Player whom threw the tile is unable to call (self.game.curTurnPlayer)
        player = [i for i in self.game.players if i.key == data['key']][0]
        is_self_turn = False
        if self.game.curTurnPlayer == player:
            is_self_turn = True

        #  2) Unable to call pong after lock (timer)
        #     Do not need to check self.game.lock if it is currently your turn and you called kang.
        if is_self_turn is False:
            if not self.game.lock:
                self.emit('error', 'Timer is over/no one threw a tile yet', room=player.sid)
                return

        #  3) No one called Superior (Hu)
        if self.game.btn_detect['type'] == 'hu':
            self.emit('error', 'Someone called Hu. You suck', room=player.sid)
            return
        elif self.game.btn_detect['type'] == 'kang':
            self.emit('error', 'YOU ALREADY CALLED KANG YOU FUCKER! JUST WAIT 3 SECOND', room=player.sid)
            return
        #  4) Tiles must match Mahjong Rules
        if is_self_turn:
            rule_match = player.call_kang(None)
            if rule_match:
                print(f'Player Kang: {player.name}')
                self.game.next_turn(target=player, draw=True, extra={'call': True, 'remove': rule_match})
        else:
            previous_tile = self.game.curTurnPlayer.lastThrow
            rule_match = player.call_kang(previous_tile)
            if rule_match:
                print(f'Player Kang: {player.name}')
                del self.game.ffa[-1]
                self.game.btn_detect = {'type': 'kang', 'target': player, 'draw': True,
                                        'extra': {'call': True, 'remove': rule_match, 'remove_ffa': True}}
            else:
                self.emit('error', 'You sure you got the required tiles? bloody idiot', room=player.sid)

    def on_call_hu(self, data: dict):
        player = [i for i in self.game.players if i.key == data['key']][0]
        is_self_turn = False
        if self.game.curTurnPlayer == player:
            is_self_turn = True

        #  1) Unable to call pong after lock (timer)
        if is_self_turn is False:
            if not self.game.lock:
                self.emit('error', 'Timer is over/no one threw a tile yet', room=player.sid)
                return

        #  2) self.game.btn_detect['type'] is None
        if not self.game.btn_detect['type'] is None:
            self.emit('error', 'Dont fking call Hu when you call Chi/Kang idiot', room=player.sid)
            return

        #  3) Players will decide if Allow to Hu or not
        print('Player Call Hu!')
        data = {'info': player.get_info(),
                'tiles': [str(i) for i in player.hand] + [str(i) for i in player.board]}
        self.game.hu_count['yes'] = 0
        self.game.hu_count['no'] = 0
        self.game.btn_detect = {'type': 'hu', 'player': player}
        self.emit('player_hu', data)

    def on_call_hu_choice(self, data):
        if data['choice']:
            self.game.hu_count['yes'] += 1
        else:
            self.game.hu_count['no'] += 1

        if self.game.hu_count['yes'] + self.game.hu_count['no'] == 3:
            if self.game.hu_count['yes'] > self.game.hu_count['no']:
                print('Hu succeed')
                win = True
            else:
                print('Hu Fail')
                win = False
            caller = self.game.btn_detect['player']
            self.game.btn_detect = {'type': None, 'target': None, 'draw': False, 'extra': {}}
            self.game.next_game(caller, win)

    def on_start(self, _):
        self.restart_count += 1
        if self.restart_count >= 4:
            self.restart_count = 0
            self.game.start()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-port', help='Set Port Number', type=int, default=5000)
    args = parser.parse_args()
    print('Server Running...')
    socketio.on_namespace(Interactive('/game'))
    socketio.run(app, port=args.port, debug=False)
