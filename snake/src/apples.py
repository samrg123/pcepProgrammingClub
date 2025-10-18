from copy import copy
from typing import TYPE_CHECKING

from src.Board import Board
from src.utils import ControlCodes, Position

if TYPE_CHECKING:
    from src.Game import Game

class Apple:
    game:"Game"
    symbol = f"{ControlCodes.FG_Red}O{ControlCodes.Reset}"
    position:Position

    def __init__(self, game:"Game", position:Position):
        self.game = game

        self.position = copy(position)
        self.game.board.SetSymbol(position, self.symbol)


    def SetPosition(self, position:Position) -> None:       
        oldPosition = self.position
        self.game.board.SetSymbol(oldPosition, Board.kEmptySymbol)

        self.position = copy(position)
        self.game.board.SetSymbol(position, self.symbol)

    def Eat(self) -> None:
        self.game.score+= 1
        self.game.snake.SetSize(self.game.snake.Size() + 4)

    def Update(self) -> None:
        pass

class SuperApple(Apple):
    symbol = f"{ControlCodes.FG_Cyan}S{ControlCodes.Reset}"

    def Eat(self):
        self.game.score+= 10
        self.game.updateInterval*= .9
        self.game.snake.SetSize(self.game.snake.Size() + 3)