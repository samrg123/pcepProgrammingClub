import random
from typing import Final

from src.utils import Position


class Board:
    kEmptySymbol:Final = " "
    kBoarderSize:Final = 1

    width:int
    height:int
    paddedWidth:int
    paddedHeight:int

    grid:list[str]
    emptyIndices:set[int]

    def __init__(self, width, height):
        
        self.width  = width
        self.height = height

        # padding for left/right and top/bottom
        self.paddedWidth  = width  + 2*Board.kBoarderSize
        self.paddedHeight = height + 2*Board.kBoarderSize

        # Initialize grid
        self.grid = []
        self.emptyIndices = set()
        for y in range(self.paddedHeight):
            for x in range(self.paddedWidth):

                symbol = self.GetDefaultSymbol(x, y)
                self.grid.append(symbol)

                if symbol == Board.kEmptySymbol:
                    self.emptyIndices.add(y * self.paddedWidth + x)


    def __str__(self):
        result = ""
        for y in range(self.paddedHeight):
            for x in range(self.paddedWidth):
                result+= self.grid[y * self.paddedWidth + x] 
            
            result+= "\n"

        return result

    def GetDefaultSymbol(self, x:int, y:int) -> str:
        if x < Board.kBoarderSize:
            if y < Board.kBoarderSize:
                # upper left boarder
                return "╔"
        
            if y >= self.height + self.kBoarderSize:
                # lower left boarder
                return "╚"

            # left boarder
            return "║"

        if x >= self.width + self.kBoarderSize:
            if y < Board.kBoarderSize:
                # upper right boarder
                return "╗"

            if y >= self.height + self.kBoarderSize:
                # lower right boarder
                return "╝"

            # right boarder
            return "║"
        
        if y < Board.kBoarderSize or y >= self.height + self.kBoarderSize:
            # top/bottom boarder
            return "═"

        # generic space
        return Board.kEmptySymbol

    def GetSymbol(self, position:Position) -> str:
        return self.grid[self.PositionToIndex(position)]

    def SetSymbol(self, position:Position, symbol:str) -> None:
        index = self.PositionToIndex(position)
        self.grid[index] = symbol
        
        if symbol == Board.kEmptySymbol:
            self.emptyIndices.add(index)
        else:
            self.emptyIndices.discard(index)

    def InBounds(self, position:Position) -> bool:
        return (0 <= position.x < self.width) and (0 <= position.y < self.height)

    def GetEmptyPosition(self) -> Position | None:
        if len(self.emptyIndices) == 0:
            return None

        index = random.choice(list(self.emptyIndices))
        return self.IndexToPosition(index)

    def IndexToPosition(self, index:int) -> Position:
        y = index // self.paddedWidth
        x = index - y * self.paddedWidth
        return Position(x - Board.kBoarderSize, y - Board.kBoarderSize)

    def PositionToIndex(self, position:Position) -> int:
        return (position.y + Board.kBoarderSize) * self.paddedWidth + (position.x + Board.kBoarderSize)

