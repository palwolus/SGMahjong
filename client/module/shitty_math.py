def load_hand_position(scr_width, scr_height, tile_width, tile_height, tile_gap):
    position_hand = []
    for i in range(1, 15):
        x = (i * tile_gap) + ((i-1) * tile_width)
        y = scr_height - tile_height
        position_hand.append((x, y))
    return position_hand


def load_board_position(scr_width, scr_height, tile_width, tile_height, hand_tile_height):
    #  tile width suppose == 30
    #  max allowed tiles is 30 (12 flowerkks, 18 kang hu)
    position_board = []
    for i in range(1, 31):
        x = (i-1) * tile_width
        y = scr_height - hand_tile_height - tile_height - 10  # pixel overlap if never -10
        position_board.append((x, y))
    return position_board


def load_enemy_position(scr_width, scr_height, enemy_tile_width, enemy_tile_height, player_wind=None):
    #  enemy_tile_width = 30 | enemy_tile_height = 45
    left = []
    right = []
    front = []

    #  front (240 from hardcoded position)
    for i in range(1, 31):
        y = 0
        x = 120 + (i*enemy_tile_width)
        front.append((x, y))

    #  left
    for i in range(1, 31):
        x = 0
        y = i*enemy_tile_width
        left.append((x, y))

    #  right
    for i in range(1, 31):
        x = scr_width - enemy_tile_height - 300
        y = i*enemy_tile_width
        right.append((x, y))

    result = {'front': front, 'left': left, 'right': right}
    return result


def load_possibilities_position():
    res = []
    tile_width = 40
    pos1_x = 920
    pos1_y = 350
    pos1 = [(pos1_x, pos1_y), (pos1_x+tile_width, pos1_y), (pos1_x+(tile_width*2), pos1_y)]
    pos2_x = 1060
    pos2 = [(pos2_x, pos1_y), (pos2_x+tile_width, pos1_y), (pos2_x+(tile_width*2), pos1_y)]

    pos3_x = 990
    pos3_y = 350 + 20 + tile_width + 15
    pos3 = [(pos3_x, pos3_y), (pos3_x+tile_width, pos3_y), (pos3_x+(tile_width*2), pos3_y)]
    res.append(pos1)
    res.append(pos2)
    res.append(pos3)
    return res


def load_hu_position():
    x, y = 50, 225
    tile_width = 30
    res = []
    for i in range(0, 30):
        res.append((x+(tile_width*i), y))
    return res


#  used to get the difference of list
#  most solution online uses sets and if list contain same values,
def compare(a: list, b: list):
    if len(a) > len(b):
        a, b = b, a

    lst3 = a.copy()
    lst4 = b.copy()
    final = []
    for i in a:
        if i in b:
            b.remove(i)
        else:
            final.append(i)
    for i in lst4:
        if i in lst3:
            lst3.remove(i)
        else:
            final.append(i)
    return final
