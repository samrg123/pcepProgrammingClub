from copy import copy
from typing import Final

from src.Board import Board
from src.utils import ControlCodes, Direction, Position


class Snake:
    kBodySymbol:Final = f"{ControlCodes.FG_Green}∗{ControlCodes.Reset}"
    kDeathSymbol:Final = f"{ControlCodes.FG_Red}∗{ControlCodes.Reset}"

    board:Board
    direction:Direction
    headIndex:int
    segments:list[Position]

    numSegmentsToGrow:int = 0
    isDead = False


    def __init__(self, board:Board, direction:Direction, position:Position):
        self.board = board
        self.direction = direction
        self.headIndex = 0
        self.segments = [position]

    def Kill(self) -> None:
        self.isDead = True
        headPosition = self.segments[self.headIndex]
        self.board.SetSymbol(headPosition, Snake.kDeathSymbol)

    def GetPosition(self, index:int) -> Position:
        return self.segments[index]

    def Size(self) -> int:
        return len(self.segments)

    def SetSize(self, size) -> None:
        numSegments = len(self.segments)

        if size > numSegments:
            
            # add growth
            self.numSegmentsToGrow = size - numSegments

            # Add segments to head
            headPosition = self.segments[self.headIndex]
            for _ in range(self.numSegmentsToGrow):
                self.segments.insert(self.headIndex, copy(headPosition))

        else:
            numSegmentsToDelete = numSegments - size

            # remove growth
            self.numSegmentsToGrow-= numSegmentsToDelete
            if self.numSegmentsToGrow < 0:
                self.numSegmentsToGrow = 0

            # remove segments from tail
            for _ in range(numSegmentsToDelete):

                # make sure the snake is always at least 1 unit long
                if len(self.segments) == 1:
                    break
                
                tailIndex = self.GetTailIndex()
                tailPosition = self.segments.pop(tailIndex)
                self.board.SetSymbol(tailPosition, Board.kEmptySymbol)
    
                # Note: no need to change head index if we're popping segments off in front of it
                if tailIndex < self.headIndex:
                    self.headIndex-= 1


    def GetTailIndex(self) -> int:
        tailIndex = self.headIndex + 1
        if tailIndex >= len(self.segments):
            return 0
        return tailIndex

    def Move(self) -> tuple[Position, str]:
        """Moves the snake in the direction it was going and returns the new position of its head and the symbol it consumed"""
        
        if self.isDead:
            # Don't do anything.
            return self.segments[self.headIndex], ""

        # get new snake head position
        newHeadPosition = copy(self.segments[self.headIndex])
        match self.direction:
            case Direction.Up:
                newHeadPosition.y-= 1

            case Direction.Down:
                newHeadPosition.y+= 1

            case Direction.Left:
                newHeadPosition.x-= 1

            case Direction.Right:
                newHeadPosition.x+= 1

        # erase snake's tail segment
        tailIndex = self.GetTailIndex()
        if self.numSegmentsToGrow > 0:
            self.numSegmentsToGrow-= 1

        else:        
            tailPosition = self.segments[tailIndex]
            self.board.SetSymbol(tailPosition, Board.kEmptySymbol)

        # replace old snake tail with new head segment
        self.segments[tailIndex] = newHeadPosition
        self.headIndex = tailIndex
        consumedSymbol = self.board.GetSymbol(newHeadPosition)
        self.board.SetSymbol(newHeadPosition, Snake.kBodySymbol)

        return newHeadPosition, consumedSymbol
