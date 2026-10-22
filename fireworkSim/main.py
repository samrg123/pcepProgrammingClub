import py5
import numpy as np

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


class FireworkSim(py5.Sketch):
    viewportWidth :int = 1000
    viewportHeight:int = 1000

    backgroundColor:Color = Color('black')

    lastUpdateMs:float = 0
    particles:list[Particle]

    gravity:py5.Py5Vector2D = py5.Py5Vector2D(0, 100)

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

        self.particles = []


    def settings(self) -> None:
        self.size(self.viewportWidth, self.viewportHeight)

    def setup(self) -> None:
        self.window_title('Particle Physics')
        self.color_mode(py5.RGB, 1, 1, 1, 1)


    def mouse_pressed(self) -> None:
        if self.mouse_button == py5.LEFT:
            self.spawnFirework(self.mouse_x, self.mouse_y)

    def spawnFirework(self, x:float, y:float) -> None:
        position = py5.Py5Vector2D(x, y)
        numberOfParticles = py5.random_int(self.minParticlesPerExplosion, self.maxParticlesPerExplosion)

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
                position      = position,
                velocity      = velocity,
                acceleration  = self.gravity,
                airResistance = airResistance,
                lifetime      = lifetime,
                startRGBA     = startRGBA,
                endRGBA       = endRGBA,
                startSize     = startSize,
                endSize       = endSize,
            )

            self.particles.append(particle)

        # advance color hue for next firework
        self.nextFireworkHue = (self.nextFireworkHue + self.fireworkHueStride) % 1


    def updateParticles(self, deltaS:float) -> None:

        # TODO: optimize this so we don't have to create a new list on each update
        survivingParticles = []
        for particle in self.particles:
            if particle.age >= particle.lifetime:
                continue

            particle.update(deltaS)
            survivingParticles.append(particle)

        self.particles = survivingParticles

    def drawParticles(self) -> None:
        for particle in self.particles:
            particle.draw(self)

    def update(self) -> None:
        updateMs = py5.millis()
        deltaS = (updateMs - self.lastUpdateMs) / 1000

        self.updateParticles(deltaS)

        self.lastUpdateMs = updateMs

    def draw(self) -> None:
        self.background(self.backgroundColor)

        self.update()

        self.drawParticles()

def main() -> None:
    fireworkSim = FireworkSim()
    fireworkSim.run_sketch()

if __name__ == '__main__':
    main()

