from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generator

from colour import Color

from src.utils import *

if TYPE_CHECKING:
    from src.ParticleSim import ParticleSim

@dataclass
class Particle:
    sim:"ParticleSim"
    gridX:int
    gridY:int
    color:Color    = field(init=False, default_factory=lambda:Color("pink"))
    destroyed:bool = field(init=False, default=False)

    def update(self, deltaT:float) -> None:
        pass

    def destroy(self) -> None:
        self.destroyed = True


@dataclass
class ParticleNeighbors(list):
    up         :Particle|None
    down       :Particle|None
    left       :Particle|None
    right      :Particle|None
    lowerLeft  :Particle|None
    lowerRight :Particle|None
    upperLeft  :Particle|None
    upperRight :Particle|None

    def __iter__(self) -> Generator[Particle|None, None, None]:
        for value in self.__dict__.values():
            yield value


@dataclass
class Sand(Particle):
    def __post_init__(self) -> None:
        self.color = Color("beige")

    def update(self, deltaT:float) -> None:

        if self.gridY >= (self.sim.viewportGridHeight - 1):
            # already on the ground - nothing to do
            return

        neighbors = self.sim.getActiveGridNeighbors(self)

        if neighbors.down is None:
            # fall straight down
            self.gridY+= 1

        elif self.gridX > 0 and neighbors.lowerLeft is None:
            # fall to the left
            self.gridY+= 1
            self.gridX-= 1

        elif self.gridX < (self.sim.viewportGridWidth-1) and neighbors.lowerRight is None:
            # fall to the right
            self.gridY+= 1
            self.gridX+= 1

@dataclass
class RainbowSand(Sand):
    def update(self, deltaT) -> None:
        super().update(deltaT)

        self.color = Color(
            red   = lerp(self.gridX / (self.sim.viewportGridWidth-1 ), 0, 1), 
            green = lerp(self.gridY / (self.sim.viewportGridHeight-1), 0, 1), 
            blue  = .5
        )

@dataclass
class Fire(Particle):
    def __post_init__(self) -> None:
        self.timeAlive           = 0
        self.lifetime            = 1
        self.propagationDelay    = .1
        self.lastPropagationTime = 0


    def update(self, deltaT:float):
        if self.timeAlive >= self.lifetime:
            # burn ourselves out
            self.destroy()
            return
        
        # set color 
        self.color = Color(
            "red",
            luminance = lerp((self.lifetime - self.timeAlive) / self.lifetime, .1, .8) 
        )

        # check to see if enough time has passed for fire to spread
        timeSinceLastPropagation = self.timeAlive - self.lastPropagationTime
        if timeSinceLastPropagation >= self.propagationDelay:

            # propagate fire to up, down, left, right neighbors
            neighbors = self.sim.getActiveGridNeighbors(self)

            for neighbor in (neighbors.up, neighbors.down, neighbors.left, neighbors.right):
                if (neighbor is not None) and (not isinstance(neighbor, Fire)):
                    self.sim.spawnParticle(neighbor.gridX, neighbor.gridY, Fire)

            self.lastPropagationTime = self.timeAlive

        self.timeAlive+= deltaT
        