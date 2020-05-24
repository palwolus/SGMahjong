from module.Player import Player
from module.Tile import Character, Dot, Bamboo, Big, Flower, Animal
import random
import threading
import time


DEBUG = True


def debug(txt):
    if DEBUG:
        print(txt)


class Game:
    def __init__(self, emit, app):
        super().__init__()
        self.hu_count = {'yes': 0, 'no': 0}
        self.count = 0
        self.app = app
        self.emit = emit
        self.tiles = []
        self.players = []
        self.ffa = []
        self.table_wind = 'east'
        self.curTurnPlayer = None
        self.lock = False
        self.skipTurn = False
        self.nextTurn = {'east': 'south', 'south': 'west', 'west': 'north', 'north': 'east'}
        self.pill = threading.Event()
        self.btn_detect = {'type': None, 'target': None, 'draw': False, 'extra': {}}
        self.savedPattern = None

    def get_player(self):
        return self.players

    def add_player(self, name: str, money, key: str, sid: str):
        if len(self.players) >= 4:
            debug('Max number of players')
            return False

        if len(self.players) == 0:
            wind = 'east'
        elif len(self.players) == 1:
            wind = 'south'
        elif len(self.players) == 2:
            wind = 'west'
        else:
            wind = 'north'
        player = Player(name, money, wind, sid)
        player.key = key
        if wind == 'east':
            player.isDealer = True
            player.dealerBefore = True
            self.curTurnPlayer = player
        self.players.append(player)
        self.emit('player_info', data=player.get_info(), room=player.sid)
        return True

    def load_tiles(self):
        self.tiles = []
        tmp = []
        for i in range(1, 10):
            tmp.append(Character(i))
            tmp.append(Dot(i))
            tmp.append(Bamboo(i))
        tmp = tmp * 4
        self.tiles.extend(tmp)

        tmp.clear()
        for i in range(1, 5):
            tmp.append(Flower(i, 'flower'))
            tmp.append(Flower(i, 'season'))
        self.tiles.extend(tmp)

        tmp = [
            Big('green'), Big('red'), Big('white'),
            Big('north'), Big('south'), Big('east'), Big('west')
        ] * 4
        self.tiles.extend(tmp)

        self.tiles.append(Animal('rooster'))
        self.tiles.append(Animal('rat'))
        self.tiles.append(Animal('cat'))
        self.tiles.append(Animal('centipede'))

        random.shuffle(self.tiles)
        print('Load Finish')

    def draw_tile(self, special=False):
        if special:
            return self.tiles.pop(0)
        else:
            return self.tiles.pop()

    def start(self):
        if len(self.players) != 4:
            debug('Not enough players')
            return False
        for i in self.players:
            draw = 0
            draw_count = 13
            if i.isDealer:
                i.dealerBefore = True
                i.isTurn = True
                draw_count = 14
            while draw < draw_count:
                tile = self.draw_tile()
                if tile.type in ['flower', 'animal']:
                    self.emit('draw_tile', {'tile': str(tile), 'sort': True, 'special': True}, room=i.sid)
                    i.board.append(tile)
                    if tile.type == 'flower':
                        i.board_info['flower'].append(str(tile))
                    else:
                        i.board_info['animal'].append(str(tile))
                else:
                    self.emit('draw_tile', {'tile': str(tile), 'sort': True, 'special': False}, room=i.sid)
                    i.hand.append(tile)
                    draw += 1

        data = {i.wind: i.get_info() for i in self.players}
        self.curTurnPlayer = [i for i in self.players if i.wind == 'east'][0]
        self.emit('first_status', data)
        for i in self.players:
            i.hand.sort(key=lambda x: str(x))
            i.board.sort(key=lambda x: str(x))

        return True

    def send_status(self, do_thread=False, extra=None, room=None):
        data = {i.wind: i.get_info() for i in self.players}
        data['ffa'] = [str(i) for i in self.ffa]
        if type(extra) is dict:
            data.update(extra)

        if room:
            self.emit('status', data, room=room)
        else:
            self.emit('status', data)

        #  start the 3 second check
        if do_thread:
            #  do_check is needed only after throw tile
            thread = threading.Thread(target=self.call_check)
            thread.daemon = True
            thread.start()

    def next_turn(self, target=None, draw=True, extra=None):
        #  check who's the next player
        if target is None:
            self.curTurnPlayer.isTurn = False
            self.curTurnPlayer = [i for i in self.players if i.wind == self.nextTurn[self.curTurnPlayer.wind]][0]
            self.curTurnPlayer.isTurn = True
        else:
            self.curTurnPlayer.isTurn = False
            self.curTurnPlayer = target
            self.curTurnPlayer.isTurn = True
        if draw:
            continue_draw = draw
            while continue_draw:
                tile = self.draw_tile()
                if tile.type in ['flower', 'animal']:
                    self.emit('draw_tile', {'tile': str(tile), 'sort': False, 'special': True}, room=self.curTurnPlayer.sid)
                    self.curTurnPlayer.board.append(tile)
                    if tile.type == ['flower']:
                        self.curTurnPlayer.board_info['flower'].append(str(tile))
                    else:
                        self.curTurnPlayer.board_info['animal'].append(str(tile))

                else:
                    continue_draw = False
                    self.emit('draw_tile', {'tile': str(tile), 'sort': False, 'special': False}, room=self.curTurnPlayer.sid)
                    self.curTurnPlayer.hand.append(tile)
        print(f'Player Turn: {self.curTurnPlayer.name} {self.curTurnPlayer.wind}')

        self.send_status(do_thread=False, extra=extra)

    def next_game(self, caller, win):
        if win:
            if caller.wind == 'east':
                rotate = False
            else:
                rotate = True
        else:
            rotate = True

        # table rotate
        check_all_player_dealer = [i for i in self.players if i.dealerBefore]
        print(check_all_player_dealer)
        if len(check_all_player_dealer) == 4:
            self.table_wind = self.nextTurn[self.table_wind]
            for i in self.players:
                i.dealerBefore = False

        #  clearing of player hand, board and info
        data = {'player': {}}
        for i in self.players:
            i.clear_all(self.nextTurn, rotate=rotate)
            data['player'][i.name] = i.get_info()

        data['table'] = self.table_wind
        self.ffa.clear()
        self.load_tiles()
        self.emit('next_game', data)
        pass

    def call_check(self):
        self.lock = True
        target, draw, extra = None, True, None
        next_turn = True
        lock_count = 3
        while True:
            print(f'Time: {lock_count}')
            time.sleep(1)
            lock_count -= 1
            if lock_count <= 0:
                self.lock = False
                if self.btn_detect['type'] == 'hu':
                    next_turn = False
                    break
                elif self.btn_detect['type'] == 'kang':
                    target, draw, extra = self.btn_detect['target'], self.btn_detect['draw'], self.btn_detect['extra']
                    self.btn_detect = {'type': None, 'target': None, 'draw': False, 'extra': {}}
                    break
                elif self.btn_detect['type'] == 'pong':
                    target, draw, extra = self.btn_detect['target'], self.btn_detect['draw'], self.btn_detect['extra']
                    self.btn_detect = {'type': None, 'target': None, 'draw': False, 'extra': {}}
                    break
                elif self.btn_detect['type'] == 'chi':
                    if self.btn_detect['extra']['multiple']:
                        self.savedPattern = {'pattern': self.btn_detect['extra']['pattern'],
                                             'player': self.btn_detect['extra']['player'],
                                             'previous_tile': self.btn_detect['extra']['previous_tile']}
                        #  Deleting information that is used for savedPattern
                        del self.btn_detect['extra']['previous_tile']
                        del self.btn_detect['extra']['player']
                        #  Converting Tiles (class) to String
                        tmp = []
                        for pat in self.btn_detect['extra']['pattern']:
                            tmp.append([str(i) for i in pat])
                        self.btn_detect['extra']['pattern'] = tmp
                        extra, room = self.btn_detect['extra'], self.btn_detect['extra'].get('room', False)
                        self.btn_detect = {'type': None, 'target': None, 'draw': False, 'extra': {}}
                        self.send_status(do_thread=True, extra=extra, room=room)
                        next_turn = False
                        break
                    else:
                        target, draw, extra = self.btn_detect['target'], self.btn_detect['draw'], self.btn_detect['extra']
                        self.btn_detect = {'type': None, 'target': None, 'draw': False, 'extra': {}}
                        break
                elif self.savedPattern is not None:
                    if self.skipTurn:
                        self.skipTurn = False
                        next_turn = False
                        break
                    else:
                        player = self.savedPattern['player']
                        data = player.call_chi(random.choice(self.savedPattern['pattern']), self.savedPattern['previous_tile'], True)
                        target, draw, extra = data['target'], data['draw'], data['extra']
                        self.savedPattern = None
                        del self.ffa[-1]
                    break
                elif self.skipTurn:
                    self.skipTurn = False
                    next_turn = False
                    break
                break
        if next_turn:
            self.next_turn(target, draw, extra)
        self.count += 1
        print(f'Time: End: {self.count}')