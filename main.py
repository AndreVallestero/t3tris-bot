from framegrabber import FrameGrabber
from clicker import Clicker
from PIL import Image
import numpy as np
import cv2
import os
from time import sleep
import subprocess
import copy
from win32api import GetAsyncKeyState
from win32con import VK_ESCAPE

'''
Start full screen terminal, run
python main.py
'''

WINDOW_TITLE = "scrcpy"
WIDTH = 10
HEIGHT = 20
BACKGROUND = (np.array([0,0,0]), np.array([255,28,255]))
AGGR_HGHT_COEF = -0.510066
COMP_LINES_COEF = 0.760666
HOLES_COEF = -0.35663
BUMP_COEF = -0.184483

MOVE_LEFT = (0.1, 0.85)
MOVE_RIGHT = (0.3, 0.85)
ROT_CCLOCK = (0.7, 0.85)
ROT_CLOCK = (0.85, 0.85)
DROP = (0.2, 0.78)

FRAME_SAMPLES = 7
SAMPLE_DELAY = 0.033
ACTION_DELAY = 0.033
POST_DROP_DELAY = 0.8 # .65

class Tetromino():
    def __init__(self, letter, ori_offsets, orientations):
        self.letter = letter
        self.ori_offsets = ori_offsets
        self.orientations = orientations
    def __str__(self):
        return self.letter
    def __repr__(self):
        return self.letter

PIECES = {
        (26, 28): Tetromino("O", [4], [
            ((0, 0), (0, 1), (1, 0), (1, 1))]),
        (134, 135): Tetromino("T", [3, 4, 3, 3], (
            ((1, 0), (0, 1), (1, 1), (2, 1)),
            ((0, 0), (0, 1), (1, 1), (0, 2)),
            ((0, 0), (1, 0), (2, 0), (1, 1)),
            ((1, 0), (0, 1), (1, 1), (1, 2)))),
        (177, 178): Tetromino("Z", [3, 4], (
            ((0, 0), (1, 0), (1, 1), (2, 1)),
            ((1, 0), (0, 1), (1, 1), (0, 2)))),
        (66, 67): Tetromino("S", [3, 4], (
            ((1, 0), (2, 0), (0, 1), (1, 1)),
            ((0, 0), (0, 1), (1, 1), (1, 2)))),
        (13, 14): Tetromino("L", [3, 4, 3, 3], (
            ((2, 0), (0, 1), (1, 1), (2, 1)),
            ((0, 0), (0, 1), (0, 2), (1, 2)),
            ((0, 0), (1, 0), (2, 0), (0, 1)),
            ((0, 0), (1, 0), (1, 1), (1, 2)))),
        (104, 105): Tetromino("J", [3, 4, 3, 3], (
            ((0, 0), (0, 1), (1, 1), (2, 1)),
            ((0, 0), (1, 0), (0, 1), (0, 2)),
            ((0, 0), (1, 0), (2, 0), (2, 1)),
            ((1, 0), (1, 1), (0, 2), (1, 2)))),
        (87, 88): Tetromino("I", [3, 5], (
            ((0, 0), (1, 0), (2, 0), (3, 0)),
            ((0, 0), (0, 1), (0, 2), (0, 3)))),
    }

def save_image(img):
    img = Image.fromarray(hsv)
    img.save("test.png", "PNG")

def print_mask(mask):
    print(
        "\033[2;2H"+
        '\n\033[1C'.join(''.join(' ' if tile else '#' for tile in row) for row in mask),
        end='',
        flush=True
    )

def print_hsv(hsv):
    print("\033[22;1H")
    print('\n'.join(
        ''.join(str(tile[0]).rjust(4) for tile in row) + ' |' +
        ''.join(str(tile[1]).rjust(4) for tile in row) + ' |' +
        ''.join(str(tile[2]).rjust(4) for tile in row)
    for row in hsv))

def hue_to_tetro(hue):
    for bounds in PIECES:
        if bounds[0] <= hue <= bounds[1]:
            return PIECES[bounds]

# On grid, 0 = block, 255 = empty
def get_score(grid, ori, pos):
    ori_height = max(ori, key=lambda block: block[1])[1]

    # Find collision point
    for offset_y in range(HEIGHT - ori_height):
        for block_x, block_y in ori:
            if grid[offset_y + block_y, pos + block_x] == 0:
                offset_y -= 1
                break
        else: continue
        break

    # Clone grid and place piece in lowered position
    grid_clone = copy.deepcopy(grid)
    for block_x, block_y in ori:
        grid_clone[offset_y + block_y, pos + block_x] = 0
    
    # calculate score of that grid
    # https://codemyroad.wordpress.com/2013/04/14/tetris-ai-the-near-perfect-player/
    # Get column heights, useful for many calculations
    col_heights = [-1]*WIDTH
    for x, col in enumerate(grid_clone.T):
        col_ceil = np.argmax(col==0)
        col_heights[x] = HEIGHT - col_ceil if col_ceil > 0 else 0

    # Calculate aggregate height
    agg_hght = sum(col_heights)

    # Calculate completed lines
    comp_lines = sum(not any(row) for row in grid_clone)

    # Calculate holes
    holes = 0
    for x, col in enumerate(grid_clone.T):
        if col_heights[x] > 0:
            holes += sum(col[-col_heights[x]:]==255)

    # Bumpiness
    bumps = np.sum(np.abs(np.subtract(col_heights[1:], col_heights[:-1])))

    #print_mask(grid_clone) # Preview score testing
    #sleep(.1)
    
    # return score
    return agg_hght * AGGR_HGHT_COEF + \
        comp_lines * COMP_LINES_COEF + \
        holes * HOLES_COEF + \
        bumps * BUMP_COEF

fg = FrameGrabber(0.224, 0.227, 0.553, 0.623, WINDOW_TITLE)
clicker = Clicker(WINDOW_TITLE)
subprocess.run('', shell=True) # Required to enable escape codes
os.system('cls') # Clear screen before printing grid
print('+','-'*10,'+\n',('|'*12+'\n')*20,'+','-'*10,'+\n',sep='')

while GetAsyncKeyState(VK_ESCAPE) == 0:
    # Take a multiframe average to reduce noise
    raw_frame = fg.grab()[:,:,:3].astype("uint16")
    for _ in range(FRAME_SAMPLES- 1):
        sleep(SAMPLE_DELAY)
        np.add(raw_frame, fg.grab()[:,:,:3], out=raw_frame)
    if FRAME_SAMPLES > 1:
        raw_frame //= FRAME_SAMPLES
    
    # Process grid
    hsv = cv2.cvtColor(fg.grab()[:,:,:3], cv2.COLOR_BGR2HSV)
    small = cv2.resize(hsv, (WIDTH, HEIGHT));
    mask = cv2.inRange(small, *BACKGROUND)
    print_mask(mask)
    print_hsv(small)
    #save_image(hsv)

    # Get falling tetromono
    highest_blocks = np.argwhere(mask==0)
    if len(highest_blocks) == 0: continue
    highest = highest_blocks[0]
    highest_hue = small[highest[0], highest[1], 0]
    tetromino = hue_to_tetro(highest_hue)
    if tetromino is None: continue

    # Find lowest empty row
    for y in range(HEIGHT-1, -1, -1):
        if all(mask[y]): 
            lowest_empty = y
            break
    else: continue

    # Remove falling piece from virtual grid
    mask[:lowest_empty] = 255

    # Find orientation and position with best score
    max_score = -9999999999
    max_score_pos = -1
    max_score_ori_idx = -1
    for ori_idx, ori in enumerate(tetromino.orientations):
        ori_width = max(ori, key=lambda block: block[0])
        positions = WIDTH - ori_width[0]

        for pos in range(positions):
            score = get_score(mask, ori, pos)
            if score > max_score:
                max_score = score
                max_score_pos = pos
                max_score_ori_idx = ori_idx

    print(max_score_ori_idx, max_score_pos)

    # Set correct orientation
    if max_score_ori_idx != 0:
        if max_score_ori_idx == 3:
            clicker.move_frac(*ROT_CCLOCK)
            sleep(ACTION_DELAY)
            Clicker.click()
            sleep(ACTION_DELAY)
        else:
            clicker.move_frac(*ROT_CLOCK)
            sleep(ACTION_DELAY)
            for i in range(max_score_ori_idx):
                Clicker.click()
                sleep(ACTION_DELAY)
    
    # Move to correct position
    pos_start = tetromino.ori_offsets[max_score_ori_idx]
    pos_delta = max_score_pos - pos_start
    if pos_delta != 0:
        clicker.move_frac(*(MOVE_LEFT if pos_delta < 0 else MOVE_RIGHT))
        sleep(ACTION_DELAY)
        for i in range(abs(pos_delta)):
            Clicker.click()
            sleep(ACTION_DELAY)
    
    # Drop piece
    clicker.move_frac(*DROP)
    sleep(ACTION_DELAY)
    Clicker.click()

    # Wait for animations and particle effects to clear
    sleep(POST_DROP_DELAY)
