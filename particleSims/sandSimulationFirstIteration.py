import py5
import random
import math

gridWidth = 50
gridHeight = 50
#board = [[[random.randint(0,255),random.randint(0,255),random.randint(0,255)] for y in range(gridHeight)] for x in range(gridWidth)]
board = [[[0,0,0] for y in range(gridHeight)] for x in range(gridWidth)]
margin = 0
squareSize = 5

#tileSet = {[0,0,0] : "air", [255, 247, 153] : "sand"}

def setup():
    global gridWidth
    global gridHeight
    global squareSize
    global margin

    py5.size(gridWidth * (squareSize + margin) + margin, gridHeight * (squareSize + margin) + margin)
    py5.no_stroke()
    py5.frame_rate(60)

def boardUpdater():
    global board
    global gridWidth
    global gridHeight

    for dx in range(gridWidth):
        for dy in range(gridHeight - 1, -1, -1):

            #sand rules
            if board[dx][dy] == [255, 247, 153] and dy + 1 < gridHeight:
                if board[dx][dy+1] == [0,0,0]:
                    board[dx][dy + 1] = board[dx][dy]
                    board[dx][dy] = [0,0,0]
                elif dx - 1 >= 0 and board[dx - 1][dy+1] == [0,0,0]:
                    board[dx - 1][dy + 1] = board[dx][dy]
                    board[dx][dy] = [0,0,0]
                elif dx + 1 < gridWidth and board[dx + 1][dy+1] == [0,0,0]:
                    board[dx + 1][dy + 1] = board[dx][dy]
                    board[dx][dy] = [0,0,0]

def draw():
    py5.background(0)

    global gridWidth
    global gridHeight
    global board
    global margin
    global squareSize

    x = margin
    y = margin

    for dx in range(gridWidth):
        for dy in range(gridHeight):
            py5.fill(board[dx][dy][0], board[dx][dy][1], board[dx][dy][2])
            py5.square(x, y, squareSize)
            y+= squareSize + margin
        x += squareSize + margin
        y = margin

    boardUpdater()

def mouse_dragged():
    # Check if the mouse was clicked inside the square
    global margin
    global board
    global squareSize
    global gridWidth
    global gridHeight

    #tile approximation
    mouseTileX = math.floor((py5.mouse_x - (margin/2)) / (margin + squareSize))
    mouseTileY = math.floor((py5.mouse_y - (margin/2)) / (margin + squareSize))

    if mouseTileX >= gridWidth: mouseTileX = gridWidth - 1
    if mouseTileY >= gridHeight: mouseTileY = gridHeight - 1
    if mouseTileX < 0: mouseTileX = 0
    if mouseTileY < 0: mouseTileY = 0

    if py5.mouse_button == py5.LEFT: board[mouseTileX][mouseTileY] = [255, 247, 153]
    if py5.mouse_button == py5.RIGHT: board[mouseTileX][mouseTileY] = [0, 0, 0]

py5.run_sketch()
