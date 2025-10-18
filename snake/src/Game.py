import random
import os
from time import sleep

from pynput import keyboard

from src.apples import *
from src.Board import Board
from src.Snake import Snake
from src.utils import ControlCodes, Direction, Position

class Game:

    board:Board
    snake:Snake

    apples:dict[Position, Apple] = {}

    score:int = 0
    updateInterval = 1/2

    appleClasses = [
        Apple, SuperApple
    ]
    
    def __init__(self, width:int, height:int):
        self.board = Board(width, height)
        self.snake = Snake(
            self.board, 
            Direction.Right, 
            Position(width//2, height//2)
        )

        self.SpawnApple()

    def Draw(self) -> None:
        # clear the screen
        displayStr = ControlCodes.ClearScreen

        # score header
        displayStr+= f"Score: {self.score}\n"

        # board
        displayStr+= str(self.board)
    
        print(displayStr, end="")


    def ProcessInput(self, key:keyboard.Key) -> None:

        # Update Snake direction
        match key:
            case keyboard.Key.up:
                self.snake.direction = Direction.Up

            case keyboard.Key.down:
                self.snake.direction = Direction.Down

            case keyboard.Key.left:
                self.snake.direction = Direction.Left

            case keyboard.Key.right:
                self.snake.direction = Direction.Right

            case keyboard.Key.esc | keyboard.KeyCode(char="q"):
                self.GameOver("Goodbye")
                os._exit(0)


    def GameOver(self, message:str) -> None:
        self.Draw()
        print(f"! GAME OVER !\n~ {message}\n")

    def SpawnApple(self) -> bool:
        applePosition = self.board.GetEmptyPosition()
        if applePosition is None:
            # board has no free space
            return False

        # create a random apple 
        appleClass = random.choice(self.appleClasses)
        self.apples[applePosition] = appleClass(self, applePosition)

        return True


    def Update(self) -> bool:
        """Updates the game state and returns true if the game is still running, or false if the game has ended"""

        snakePosition, consumedSymbol = self.snake.Move()
        
        # check if we hit an apple and eat it
        if snakePosition in self.apples:
            apple = self.apples.pop(snakePosition)
            apple.Eat()
            
            # spawn a new apple
            if not self.SpawnApple():
                self.GameOver("You Win!")

        # check if the snake intersects its body
        if consumedSymbol == Snake.kBodySymbol:
            self.snake.Kill()
            self.GameOver("Ouch!")
            return False

        # check if the snake's head is out of bounds
        if not self.board.InBounds(snakePosition):
            self.snake.Kill()
            self.GameOver("Don't Run Away!")
            return False

        return True



    def Start(self) -> None:

        # install keyboard listener
        keyboardListener = keyboard.Listener(on_press=self.ProcessInput)
        keyboardListener.start()

        while True:
            self.Draw()
            sleep(self.updateInterval)
            if not self.Update():
                break

        keyboardListener.stop()
