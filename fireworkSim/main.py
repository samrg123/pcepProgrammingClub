import enum

import numpy as np
import py5
from colour import Color


class Particle:
    position    :py5.Py5Vector2D
    velocity    :py5.Py5Vector2D
    acceleration:py5.Py5Vector2D

    airResistance:float

    age     :float
    lifetime:float

    size     :float
    startSize:float
    endSize  :float

    rgba     :np.ndarray
    startRGBA:np.ndarray
    endRGBA  :np.ndarray

    def __init__(
        self,
        position     :py5.Py5Vector2D,
        velocity     :py5.Py5Vector2D,
        acceleration :py5.Py5Vector2D,
        airResistance:float,
        lifetime     :float,
        startRGBA    :np.typing.ArrayLike, 
        endRGBA      :np.typing.ArrayLike,
        startSize    :float, 
        endSize      :float
    ):
        self.position      = position.copy
        self.velocity      = velocity.copy
        self.acceleration  = acceleration.copy
        self.airResistance = airResistance
        self.lifetime      = lifetime
        self.startRGBA     = np.array(startRGBA)
        self.endRGBA       = np.array(endRGBA)
        self.startSize     = startSize
        self.endSize       = endSize

        self.age   = 0
        self.size  = startSize
        self.rgba  = self.startRGBA

    def update(self, deltaS:float) -> None:
        self.velocity+= deltaS * self.acceleration

        # add air resistance
        speedSquared = self.velocity.mag_sq
        if speedSquared > 0:
            speed = py5.sqrt(speedSquared)            
            newSpeed = speed - (deltaS * self.airResistance * speedSquared)
            if newSpeed < 0:
                newSpeed = 0

            self.velocity.set_mag(newSpeed)

        self.position+= deltaS * self.velocity
        self.age+= deltaS

        ageT = py5.constrain(self.age / self.lifetime, 0, 1)

        self.rgba = py5.lerp(self.startRGBA, self.endRGBA, ageT)
        self.size = py5.lerp(self.startSize, self.endSize, ageT)


    def draw(self, sketch:py5.Sketch) -> None:
        sketch.stroke(*self.rgba)
        sketch.stroke_weight(self.size)
        sketch.point(self.position.x, self.position.y)



class Firework:
    class State(enum.IntEnum):
        Launching = enum.auto()
        Exploding = enum.auto()
        BurnedOut = enum.auto()

    state:State = State.Launching    

    tail           :Particle
    tailTheta      :float
    tailOmega      :float = 25
    tailWiggleForce:float = 700

    fireballParticles:list[Particle]

    minParticlesPerExplosion:int = 100
    maxParticlesPerExplosion:int = 500

    minParticleSpeed:float = 0
    maxParticleSpeed:float = 2000

    minParticleAirResistance:float = .009
    maxParticleAirResistance:float = .01

    minParticleLifetime:float = 2
    maxParticleLifetime:float = 4

    minParticleSize = 1
    maxParticleSize = 10

    gravity:py5.Py5Vector2D = py5.Py5Vector2D(0, 100)

    def __init__(self, 
                 launchPosition :py5.Py5Vector2D, 
                 launchVelocity :py5.Py5Vector2D,
                 tailLifetime   :float,
                 startRGBA      :tuple[float,float,float,float],
                 endRGBA        :tuple[float,float,float,float],
    ):
        self.tail = Particle(
            position      = launchPosition,
            velocity      = launchVelocity,
            acceleration  = py5.Py5Vector2D(0, 0),
            airResistance = 0,
            lifetime      = tailLifetime,
            startRGBA     = startRGBA,
            endRGBA       = endRGBA,
            startSize     = 5,
            endSize       = 5,
        )

        self.tailTheta = py5.random(0, py5.TWO_PI)
        self.fireballParticles = []

    def explode(self) -> None:        
        numberOfParticles = py5.random_int(self.minParticlesPerExplosion, self.maxParticlesPerExplosion)
        for _ in range(numberOfParticles):
            speed     = py5.random(self.minParticleSpeed, self.maxParticleSpeed)
            direction = py5.Py5Vector2D.random()
            velocity  = speed * direction

            airResistance = py5.random(self.minParticleAirResistance, self.maxParticleAirResistance)

            randomT  = py5.random()
            lifetime = py5.lerp(self.minParticleLifetime, self.maxParticleLifetime, randomT)

            startSize = py5.lerp(self.minParticleSize, self.maxParticleSize, randomT)
            endSize   = self.minParticleSize

            particle = Particle(
                position      = self.tail.position,
                velocity      = velocity,
                acceleration  = self.gravity,
                airResistance = airResistance,
                lifetime      = lifetime,
                startRGBA     = self.tail.startRGBA,
                endRGBA       = self.tail.endRGBA,
                startSize     = startSize,
                endSize       = endSize,
            )

            self.fireballParticles.append(particle)


    def updateTail(self, deltaS:float) -> None:
        if self.tail.age > self.tail.lifetime:
            self.state = Firework.State.Exploding
            self.explode()
            return

        # wiggle the burning tail
        wiggleForce     = self.tailWiggleForce * py5.sin(self.tailTheta)
        wiggleDirection = py5.Py5Vector2D(-self.tail.velocity.y, self.tail.velocity.x).normalize()

        self.tailTheta = (self.tailTheta + deltaS * self.tailOmega) % py5.TWO_PI
        self.tail.acceleration = wiggleForce * wiggleDirection

        self.tail.update(deltaS)


    def updateFireball(self, deltaS:float) -> None:
        numParticles = len(self.fireballParticles)
        if numParticles == 0:
            self.state = Firework.State.BurnedOut
            return

        # TODO: optimize this so we don't have to create a new list on each update
        self.fireballParticles = [particle for particle in self.fireballParticles if particle.age <= particle.lifetime]
        for particle in self.fireballParticles:
            particle.update(deltaS)

    def update(self, deltaS:float) -> None:
        match self.state:
            case Firework.State.Launching:
                self.updateTail(deltaS)

            case Firework.State.Exploding:
                self.updateFireball(deltaS)


    def draw(self, sketch:py5.Sketch) -> None:
        match self.state:
            case Firework.State.Launching:
                self.tail.draw(sketch)
            
            case Firework.State.Exploding:
                for particle in self.fireballParticles:
                    particle.draw(sketch)


class FireworkSim(py5.Sketch):
    viewportWidth :int = 1000
    viewportHeight:int = 800

    backgroundColor:Color = Color('black')

    lastUpdateMs:float = 0

    fireworks:list[Firework]

    minTailSpeed:float = 100
    maxTailSpeed:float = 500

    nextFireworkHue  :float = 0
    fireworkHueStride:float = 45/360  
    
    startParticleLightness:float = .6
    endParticleLightness  :float = .1

    startParticleSaturation:float = 1
    endParticleSaturation  :float = 0

    startParticleAlpha:float = 1
    endParticleAlpha  :float = .5


    def __init__(self):
        super().__init__()
        self.fireworks = []


    def settings(self) -> None:
        self.size(self.viewportWidth, self.viewportHeight)

    def setup(self) -> None:
        self.window_title('Particle Physics')
        self.color_mode(py5.RGB, 1, 1, 1, 1)

        self.background(self.backgroundColor)

    def mouse_pressed(self) -> None:
        if self.mouse_button == py5.LEFT:
            self.launchFirework(
                launchX = self.width/2, 
                launchY = self.height, 
                targetX = self.mouse_x, 
                targetY = self.mouse_y
            )

    def launchFirework(self, launchX:float, launchY:float, targetX:float, targetY:float) -> None:
        launchSpeed    = py5.random(self.minTailSpeed, self.maxTailSpeed)
        launchPosition = py5.Py5Vector2D(launchX, launchY)
        trajectory     = py5.Py5Vector2D(targetX - launchX, targetY - launchY)
        
        # estimate lifetime based on launch speed and trajectory to hit the target
        flightDistance = trajectory.mag
        if flightDistance < py5.EPSILON:
            launchVelocity = py5.Py5Vector2D(0, 0)
            tailLifetime   = 0
        else:
            launchVelocity = launchSpeed * trajectory.copy.normalize()
            tailLifetime   = flightDistance / launchSpeed
        
        startColor = Color(hsl=(
            self.nextFireworkHue, 
            self.startParticleSaturation,   
            self.startParticleLightness
        ))
        startRGBA = (*startColor.get_rgb(), self.startParticleAlpha) 

        endColor = Color(hsl=(
            self.nextFireworkHue, 
            self.endParticleSaturation, 
            self.endParticleLightness
        ))
        endRGBA = (*endColor.get_rgb(), self.endParticleAlpha) 

        firework = Firework(
            launchPosition = launchPosition, 
            launchVelocity = launchVelocity,
            tailLifetime   = tailLifetime,
            startRGBA      = startRGBA,
            endRGBA        = endRGBA,        
        )
        self.fireworks.append(firework)

        # advance color hue for next firework
        self.nextFireworkHue = (self.nextFireworkHue + self.fireworkHueStride) % 1


    def updateFireworks(self, deltaS:float) -> None:
        self.fireworks = [firework for firework in self.fireworks if firework.state != Firework.State.BurnedOut]
        for firework in self.fireworks:
            firework.update(deltaS)

    def drawFireworks(self) -> None:
        for firework in self.fireworks:
            firework.draw(self)

    def update(self) -> None:
        updateMs = py5.millis()
        deltaS = (updateMs - self.lastUpdateMs) / 1000

        self.updateFireworks(deltaS)

        self.lastUpdateMs = updateMs

    def draw(self) -> None:
        # TODO: make alpha frametime independent 
        self.fill(*self.backgroundColor.get_rgb(), .1)
        self.rect(0, 0, self.width, self.height)

        self.update()

        self.drawFireworks()

def main() -> None:
    fireworkSim = FireworkSim()
    fireworkSim.run_sketch()

if __name__ == '__main__':
    main()

