import pygame
import glob
import socketio
import socketio.exceptions
import argparse
from module.Tile import Tile
from module.Interact import Interactive
from module.shitty_math import *
from module.Button import Button
from module.Label import Label

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GREY = (128, 128, 128)


class Mahjong:
    """ Initialise the game """
    def __init__(self, player: dict, address, width=1200, height=600):
        #  General info
        self.player = player
        self.address = address
        self.isTurn = False
        self.enemy_pos = {}

        #  Load pygame
        pygame.init()
        pygame.display.set_caption('Mahjong')

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.background = pygame.Surface(self.screen.get_size()).convert()
        self.background.fill(WHITE)

        #  Pygame Label
        self.lblName = Label('', RED, 25, x=910, y=580)
        self.lblTable = Label('', RED, 25, x=1055, y=580)
        self.lblLastThrown = Label('', GREY, 30, x=910, y=550)

        #  Tiles Positioning
        self.tile_gap = 4
        self.tile_width = (self.width - (self.tile_gap * 15)) // 14
        self.tile_height = self.tile_width + 15
        self.position_hand = load_hand_position(self.width, self.height, 60, 75, 4)
        self.position_board = load_board_position(self.width, self.height, 30, 45, 75)
        self.position_enemy = load_enemy_position(self.width, self.height, 30, 45)
        self.position_possibilities = load_possibilities_position()  # list of list
        self.position_hu_tiles = load_hu_position()
        #  Variables
        self.table = 'east'
        self.start = False
        self.sio = socketio.Client()
        self.tiles = {}
        self.hand = []
        self.board = []
        self.ffa = []
        self.hu_tiles = []

        self.enemy_board = {'front': [], 'left': [], 'right': []}  # dict of list
        self.possible_tiles = []
        self.possibleCheck = False
        self.show_hu_btn = False
        self.hu_decision_btn = [
            Button(GREEN, 200, 300, 200, 50, text='Yes', name='yes'),
            Button(RED, 500, 300, 200, 50, text='No', name='no')
        ]

        self.load_tiles()

    def load_tiles(self):
        for i in glob.glob('tile_pack/**'):
            name = i.split('/')[1][:-4]
            self.tiles[name] = Tile(name, i, self.width, self.height)

    def load_socketio(self):
        try:
            self.sio.connect(self.address, namespaces=['/game'])
            self.sio.register_namespace(Interactive(self, '/game'))
        except socketio.exceptions.ConnectionError:
            print(f'Server Address: [{self.address}] Not Found. Have you port forwarded?')
            exit()

    def draw_text(self, text, color, surface, x, y):
        textobj = pygame.font.SysFont(None, 20).render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def run(self):
        running = True
        clock = pygame.time.Clock()
        call_btn = [
            Button(RED, 950, 25, 200, 50, text='Hu', name='hu'),
            Button(RED, 950, 100, 200, 50, text='Kang', name='kang'),
            Button(RED, 950, 175, 200, 50, text='Pong', name='pong'),
            Button(RED, 950, 250, 200, 50, text='Chi', name='chi')
        ]

        while True:
            clock.tick(60)
            self.screen.blit(self.background, (0, 0))
            pygame.draw.rect(self.screen, BLACK, pygame.rect.Rect(50, 50, 800, 415), 1)
            pygame.draw.line(self.screen, BLACK, (900, 0), (900, self.width), 1)
            [i.draw(self.screen) for i in call_btn]
            mx, my = pygame.mouse.get_pos()
            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONUP and event.button == pygame.BUTTON_LEFT:
                    click = True

            #  Throw Tile
            if click and self.isTurn:
                tile = [i for i in self.hand if i.rect.collidepoint(mx, my)]
                if len(tile) == 1:
                    self.hand.remove(tile[0])
                    tile[0].load_ffa()
                    self.ffa.append(tile[0])
                    self.isTurn = False
                    data = {'tile': tile[0].name, 'key': self.player['key']}
                    self.sio.emit('throw_tile', data, namespace='/game')
                    self.hand.sort(key=lambda x: x.name)
                    click = False

            #  Button Hu
            if click:
                btn = [i for i in call_btn if i.collidepoint((mx, my))]
                if len(btn) == 1 and btn[0].name == 'hu':
                    print('Call Hu!')
                    data = {'key': self.player['key']}
                    self.sio.emit('call_hu', data, namespace='/game')

            #  Button Kang
            if click:
                btn = [i for i in call_btn if i.collidepoint((mx, my))]
                if len(btn) == 1 and btn[0].name == 'kang':
                    print('Call Kang!')
                    data = {'key': self.player['key']}
                    self.sio.emit('call_kang', data, namespace='/game')

            #  Button Pong
            if click and not self.isTurn:
                btn = [i for i in call_btn if i.collidepoint((mx, my))]
                if len(btn) == 1 and btn[0].name == 'pong':
                    print(f'Call Pong!')
                    data = {'key': self.player['key']}
                    self.sio.emit('call_pong', data, namespace='/game')

            #  Button Chi
            if click and not self.isTurn:
                btn = [i for i in call_btn if i.collidepoint((mx, my))]
                if len(btn) == 1 and btn[0].name == 'chi':
                    print(f'Call Chi!')
                    data = {'key': self.player['key']}
                    self.sio.emit('call_chi_check', data, namespace='/game')

            #  Select Chi Possibilities
            if click and self.possibleCheck and not self.isTurn:
                select = None
                for idx, tileList in enumerate(self.possible_tiles):
                    if [i for i in tileList if i.rect.collidepoint(mx, my)]:
                        select = idx
                        break
                if select is not None:
                    self.possibleCheck = False
                    self.possible_tiles.clear()
                    data = {'select': select, 'key': self.player['key']}
                    self.sio.emit('call_chi_after', data, namespace='/game')
                    #  emit selection number
                    pass

            #  Select Hu Decision
            if self.show_hu_btn and click:
                btn = [i for i in self.hu_decision_btn if i.collidepoint((mx, my))]
                if len(btn) == 1:
                    if btn[0].name == 'yes' and btn[0].show:
                        data = {'choice': True, 'key': self.player['key']}
                        self.sio.emit('call_hu_choice', data, namespace='/game')
                        for i in self.hu_decision_btn:
                            i.show = False

                    elif btn[0].name == 'no' and btn[0].show:
                        data = {'choice': False, 'key': self.player['key']}
                        self.sio.emit('call_hu_choice', data, namespace='/game')
                        for i in self.hu_decision_btn:
                            i.show = False


            #  Draw Possibilities
            for idx, tList in enumerate(self.possible_tiles):
                for i in range(0, 3):
                    tList[i].position = self.position_possibilities[idx][i]
                    tList[i].update()
                    tList[i].draw(self.screen)
            #  Draw Hand
            for idx, tile in enumerate(self.hand):
                tile.position = self.position_hand[idx]
                tile.update()
                tile.draw(self.screen)
            #  Draw Board
            for idx, tile in enumerate(self.board):
                tile.position = self.position_board[idx]
                tile.update()
                tile.draw(self.screen)
            #  Draw FFA
            for tile in self.ffa:
                tile.update()
                tile.draw(self.screen)
            #  Draw Enemy Board
            for key, pos in self.position_enemy.items():
                for idx, tile in enumerate(self.enemy_board[key]):
                    tile.position = pos[idx]
                    tile.update()
                    tile.draw(self.screen)
            #  Draw Hu Tiles
            for idx, tile in enumerate(self.hu_tiles):
                tile.position = self.position_hu_tiles[idx]
                tile.update()
                tile.draw(self.screen)
            # Draw Hu Button
            if self.show_hu_btn:
                for i in self.hu_decision_btn:
                    if i.show:
                        i.draw(self.screen)
            #  Draw Label
            self.lblName.text = f"{self.player['name']} : {self.player['wind']}"
            self.lblName.update()
            self.lblName.draw(self.screen)

            self.lblTable.text = f"Table Wind: {self.table}"
            self.lblTable.update()
            self.lblTable.draw(self.screen)

            self.lblLastThrown.update()
            self.lblLastThrown.draw(self.screen)

            if running is False:
                self.sio.disconnect()
                pygame.quit()
                return

            pygame.display.flip()
            pass

    def main_menu(self):
        self.load_socketio()
        self.load_tiles()
        clock = pygame.time.Clock()

        btn_ping = Button(RED, 50, 100, 200, 50, text='Ping')
        btn_start = Button(RED, 50, 200, 200, 50, text='Start')

        while True:
            self.screen.blit(self.background, (0, 0))
            self.draw_text('main menu', RED, self.screen, 20, 20)

            mx, my = pygame.mouse.get_pos()
            btn_ping.draw(self.screen)
            btn_start.draw(self.screen)
            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    self.sio.disconnect()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        click = True

            if btn_ping.collidepoint((mx, my)):
                if click:
                    print('Requested Ping')
                    self.sio.emit('request_ping', data=self.sio.sid, namespace='/game')

            if btn_start.collidepoint((mx, my)):
                if click:
                    print('Request Start')
                    self.sio.emit('request_start', data=self.sio.sid, namespace='/game')

            if self.start:
                self.run()
                self.start = False
                print('Next Level')

            clock.tick(60)
            pygame.display.update()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-name', help='Name of player', type=str, required=True)
    parser.add_argument('-key', help='Name of player', type=str, required=True)
    parser.add_argument('-address', help='Server Address (e.g. http://localhost:5000/)', type=str, required=True)
    args = parser.parse_args()
    player = {'name': args.name, 'key': args.key, 'money': 0}
    game = Mahjong(player, args.address)
    game.main_menu()
