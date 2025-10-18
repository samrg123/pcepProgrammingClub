
import argparse
from src.Game import *

class MyApple(Apple):
    symbol = f"{ControlCodes.FG_Cyan}M{ControlCodes.Reset}"

    def Eat(self):
        # TODO: implement your own rules here!
        game = self.game


def main():

    argParser = argparse.ArgumentParser(
        description="A terminal text based game of snake!"        
    )

    argParser.add_argument("width",  type=int, default=10)
    argParser.add_argument("height", type=int, default=10)

    args = argParser.parse_args()

    width:int = args.width
    height:int = args.height

    minDimension = 5
    if width < minDimension or height < minDimension:
        print(f"Width and height must be at least {minDimension}")
        return

    args = argParser.parse_args()

    game = Game(width, height)

    game.appleClasses.append(MyApple)

    game.Start()


if __name__ == "__main__":
    main()