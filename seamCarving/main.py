import argparse

from src.SeamCarver import SeamCarver
from src.Image import Image

from matplotlib import pyplot as plt
import numpy as np

class MySeamCarver(SeamCarver):
    def pixelEnergy(self, image:Image, x:int, y:int):
        # TODO: Experiment with your own energy function

        return super().pixelEnergy(image, x, y)


def main(argList:list[str]|None=None):

    argParser = argparse.ArgumentParser(prog="seamCarver", description="A slooow python program to visualize seam carving")

    argParser.add_argument("image", type=str)
    argParser.add_argument("--width", type=int, default=None, help="Sets the new image width. If not provide the program will select a suitable size")

    # parse args
    args = argParser.parse_args(argList)

    imagePath:str = args.image
    image = Image(imagePath)

    newWidth:int = args.width if args.width is not None else np.max([1, image.width//2, image.width - 50])
    if newWidth <= 0 or newWidth > image.width:
        print(f"New width must be greater than zero and larger than image width! [newWidth: {newWidth} | imageWidth: {image.width}]")
        return

    # carve it up!
    seamCarver                 = MySeamCarver()
    energyImage                = seamCarver.energyImage(image)
    carvedImage, carvedColumns = seamCarver.carveImage(image, newWidth)
    seamImage                  = seamCarver.seamImage(carvedImage, carvedColumns)

    # plot the results!
    Image.plotImages(
        title     = f"Seam Carving: {imagePath}",
        cmap      = "magma",
        imageDict = {

            image       : f"Original ({image.width}x{image.height})",
            carvedImage : f"Carved ({carvedImage.width}x{carvedImage.height})",
            energyImage : f"Energy",
            seamImage   : f"Seams ({len(carvedColumns)})",
        }
    )

if __name__ == '__main__':
    main()

