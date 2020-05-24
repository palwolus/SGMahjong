class Player:
    def __init__(self, name: str, money: int, wind: str, sid: str):
        self.key = None
        self.name = name
        self.money = money
        self.wind = wind
        self.dealerBefore = False
        self.sid = sid
        self.isDealer = False
        self.hand = []
        self.board = []
        self.board_info = {'pong': [], 'kang': [], 'chi': [], 'flower': [], 'animal': []}
        self.lastThrow = None
        self.isTurn = False

    def __repr__(self):
        return 'Player: ' + self.name + '_' + str(self.key)

    def clear_all(self, next_turn, rotate=True):
        # Set wind to next turn
        if rotate:
            rotate_turn = {v: k for k, v in next_turn.items()}
            self.wind = rotate_turn[self.wind]

        #  clear all hand and board
        self.hand = []
        self.board = []
        self.board_info = {'pong': [], 'kang': [], 'chi': [], 'flower': [], 'animal': []}

        #  clear last throw and turn info
        self.lastThrow = None
        self.isTurn = False
        self.isDealer = False
        if self.wind == 'east':
            self.isDealer = True


    def get_info(self) -> dict:
        return {
            'name': self.name,
            'wind': self.wind,
            'money': self.money,
            'hand': len(self.hand),
            'board': [str(i) for i in self.board],
            'turn': self.isTurn
        }

    def throw_tile(self, tile):
        print(f'Player Throw Tile: {self.name} {self.wind}')
        self.isTurn = False
        for i in range(0, len(self.hand)):
            if str(self.hand[i]) == tile:
                self.lastThrow = self.hand.pop(i)
                return self.lastThrow
        self.hand.sort(key=lambda x: str(x))

    def call_pong(self, previous_tile):
        name = str(previous_tile)
        #  1) Get the tiles on hand that is same name as thrown
        tiles_append = [tile for idx, tile in enumerate(self.hand) if str(tile) == name]

        #  2) Check if len is either 2 or 3 (player might pong instead of kang)
        if len(tiles_append) == 2:
            pass
        elif len(tiles_append) == 3:
            del tiles_append[-1]
        else:
            return False

        #  3) Add to board, remove from hand
        for tile in tiles_append:
            self.board.append(tile)
        self.board.append(previous_tile)
        tmp = [str(i) for i in tiles_append]
        tmp.append(str(previous_tile))
        self.board_info['pong'].append(tmp)
        self.hand = [tile for idx, tile in enumerate(self.hand) if tile not in tiles_append]
        return {'player': self.wind, 'tiles': [str(i) for i in tiles_append]}

    def call_chi_check(self, previous_tile):
        #  1) Check consequent tiles
        tile_type, tile_number = previous_tile.type, previous_tile.number
        csq_tiles = [i.number for i in self.hand if tile_type == i.type and
                     tile_number - 2 <= i.number <= tile_number + 2]

        pattern = []
        try:
            if tile_number - 2 in csq_tiles and tile_number - 1 in csq_tiles:
                t1 = [i for i in self.hand if str(i) == f'{tile_type}_{tile_number - 2}'][0]
                t2 = [i for i in self.hand if str(i) == f'{tile_type}_{tile_number - 1}'][0]
                pattern.append([t1, t2, previous_tile])
        except IndexError:
            print('Index Error @ Pat 2')

        try:
            if tile_number - 1 in csq_tiles and tile_number + 1 in csq_tiles:
                t1 = [i for i in self.hand if str(i) == f'{tile_type}_{tile_number - 1}'][0]
                t2 = [i for i in self.hand if str(i) == f'{tile_type}_{tile_number + 1}'][0]
                pattern.append([t1, previous_tile, t2])
        except IndexError:
            print('Index Error @ Pat 3')

        try:
            if tile_number + 1 in csq_tiles and tile_number + 2 in csq_tiles:
                t1 = [i for i in self.hand if str(i) == f'{tile_type}_{tile_number + 1}'][0]
                t2 = [i for i in self.hand if str(i) == f'{tile_type}_{tile_number + 2}'][0]
                pattern.append([previous_tile, t1, t2])
        except IndexError:
            print('Index Error @ Pat 1')

        #  2) If there's no pattern to it, return False
        if len(pattern) == 0:
            return False

        #  3) If there's only 1 pattern, straight remove from board and hand
        elif len(pattern) == 1:
            return self.call_chi(pattern[0], previous_tile)
        #  3.5) If there's multiple pattern, start timer
        else:
            return pattern
            # res = []
            # for pat in pattern:
            #     out = [str(i) for i in pat]
            #     res.append(out)
            # return res

    def call_chi(self, pattern, previous_tile, req_btn_detect=False):
        tmp = [str(i) for i in pattern]
        self.board_info['chi'].append(tmp)
        for tile in pattern:
            self.board.append(tile)
        pattern.remove(previous_tile)
        
        self.hand = [tile for tile in self.hand if tile not in pattern]
        res = {'player': self.wind, 'tiles': [str(i) for i in pattern]}

        if req_btn_detect:
            data = {'type': 'chi', 'target': self, 'draw': False,
                    'extra': {'check': False, 'call': True, 'remove': res, 'remove_ffa': True, 'random_chi': True}}
            return data
        else:
            return res

    def call_kang(self, previous_tile):
        if previous_tile is None:
            #  1) is SelfTurn, so check hand frequency == 4
            str_hand = [str(i) for i in self.hand]
            tile_freq = {k: str_hand.count(k) for k in str_hand}
            four_tiles = [k for k, c in tile_freq.items() if c == 4]
            #  2) Make sure player have 4 tiles of same
            if len(four_tiles) == 1:
                tiles_append = [tile for tile in self.hand if str(tile) == four_tiles[0]]

                #  3) Add to board, remove from hand
                for tile in tiles_append:
                    self.board.append(tile)
                self.hand = [tile for tile in self.hand if tile not in tiles_append]
                return {'player': self.wind, 'tiles': [str(i) for i in tiles_append]}
            else:
                return False
        else:
            name = str(previous_tile)
            #  1) Get the tiles on hand that is the same name as thrown
            tiles_append = [tile for idx, tile in enumerate(self.hand) if str(tile) == name]
            #  2) Making sure its equal to 3 on hand
            if len(tiles_append) != 3:
                return False

            #  3) Add to board, remove from hand
            for tile in tiles_append:
                self.board.append(tile)
            self.board.append(previous_tile)
            tmp = [str(i) for i in tiles_append]
            tmp.append(str(previous_tile))
            self.board_info['kang'].append(tmp)
            self.hand = [tile for tile in self.hand if tile not in tiles_append]
            return {'player': self.wind, 'tiles': [str(i) for i in tiles_append]}

    def call_hu(self, allow):
        pass
