import argparse

from src.ParticleSim import ParticleSim
from src.particles import *

class MyParticle(Particle):
    def __post_init__(self) -> None:
        
        # TODO:implement your own initialization
        pass

    def update(self, deltaT:float) -> None:

        # TODO:implement your own update function
        pass


def main() -> None:

    # build arguments
    argParser = argparse.ArgumentParser(
        description="An interactive particle simulation App"        
    )

    argParser.add_argument("--width"  , type=int, default=100, help="The width of the viewport in grid units")
    argParser.add_argument("--height" , type=int, default=100, help="The height of the viewport in grid units")
    argParser.add_argument("--size"   , type=int, default=10,  help="The size of each grid in pixels")

    args = argParser.parse_args()

    # parse screen dimensions
    minGridDimension = 10
    gridWidth:int  = args.width
    gridHeight:int = args.height
    if gridWidth < minGridDimension or gridHeight < minGridDimension:
        print(f"Invalid grid dimensions {gridWidth}x{gridHeight}. Minimum dimensions are: {minGridDimension}x{minGridDimension}")
        return

    # parse square size
    minGridSize = 1
    gridSize:int = args.size
    if gridSize < minGridSize:
        print(f"Invalid grid size: {gridSize}. Minium grid size is: {minGridSize}")
        return


    # Create simulation
    particleSim = ParticleSim(gridSize, gridWidth, gridHeight)

    # inject our particle into the simulation
    particleSim.keyParticleTypeDict["4"] = MyParticle

    # run the simulation!
    particleSim.run_sketch()


if __name__ == "__main__":
    main()