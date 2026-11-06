from dataclasses import dataclass
import math
import random
from typing import Callable, override
import numpy as np
import pygame

# -----------------------------------------------------------------------------
# HARDWARE CONFIGURATION & PALETTE (IBM 5151 Green Monochrome Phosphor)
# -----------------------------------------------------------------------------
FPS           = 30
RENDER_SCALE  = 2

SCREEN_WIDTH  = 640
SCREEN_HEIGHT = 400

FONT        = "Mx437_IBM_CGAthin-2y.ttf" 
FONT_HEIGHT = 14
FONT_WIDTH  = 7

SCREEN_CHARS_X = int(SCREEN_WIDTH / FONT_WIDTH)
SCREEN_CHARS_Y = int(SCREEN_HEIGHT / FONT_HEIGHT)

# Green Phosphor Palette
COLOR_BLACK  = (  0,  0,    0)
COLOR_BG     = ( 10, 20,   10)  # Dark background
COLOR_DIM    = ( 20, 100,  30)  # Low intensity phosphor
COLOR_MED    = ( 40, 200,  60)  # Mid intensity phosphor
COLOR_BRIGHT = (100, 255, 120)  # Bright intensity phosphor

NUM_BATS    = 5
NUM_GHOSTS  = 4
NUM_WITCHES = 2

def lerp(t:float, min:float, max:float) -> float:
    return t * (max - min) + min

# -----------------------------------------------------------------------------
# AUDIO EMULATOR (PC Speaker 1-Bit Square Wave Generator)
# -----------------------------------------------------------------------------
class PCSpeaker:
    sampleRate:int = 22050

    sampleType    = np.int16
    bitDepth :int = 16
    maxValue :int = (1 << (bitDepth - 1)) - 1  

    # Note: buffer_samples must be a power of 2
    bufferSamples :int   = 512
    bufferDuration:float = bufferSamples / sampleRate 

    # square waves are hard on the ears so we lower gain!
    gain:float = 0.5

    activeSound:pygame.mixer.Sound|None = None

    def __init__(self):
        self.bufferT = np.linspace(0, self.bufferDuration, self.bufferSamples, False)
        
        pygame.mixer.pre_init(
            frequency      = self.sampleRate,

            # negative to indicate signed values
            size           = -self.bitDepth,

            channels       = 1,
            buffer         = self.bufferSamples,

            # use any device
            devicename     = None,

            # force our settings to be used and convert to compatible format at runtime
            allowedchanges = 0            
        )

    def play(self, frequency:int) -> None:
        """Plays a retro PC speaker square wave for a given frequency (Hz)."""

        # clamp the sound to a positive integer
        intFrequency = 0 if (frequency < 0) else int(frequency)

        # Create square wave [-1.0, 1.0]
        square_wave = np.sign(np.sin((2 * np.pi * intFrequency) * self.bufferT))

        # Convert to 16-bit PCM integer sound
        audio_data = (square_wave * self.maxValue * self.gain).astype(self.sampleType)
        newSound = pygame.sndarray.make_sound(audio_data)

        # swap active sound for new sound that loops until we call stop() or play a new sound
        if self.activeSound is not None:
            self.activeSound.stop()

        # Note: -1 means loop forever
        newSound.play(loops=-1)
        self.activeSound = newSound

    def stop(self) -> None:
        if self.activeSound is None:
            return

        self.activeSound.stop()
        self.activeSound = None

@dataclass
class Note:
    frequency:int
    duration :float

class PCSound:
    notes  :list[Note]

    onStart:Callable[["PCSound"], None] = None
    onEnd  :Callable[["PCSound"], None] = None

    isPlaying        :bool  = False
    currentNoteIndex :int   = 0
    currentNoteOffset:float = 0

    def __init__(self, 
                 notes  :list[Note], 
                 onStart:Callable[["PCSound"], None] = None, 
                 onEnd  :Callable[["PCSound"], None] = None
    ):
        self.notes   = notes
        self.onStart = onStart
        self.onEnd   = onEnd

    def reset(self) -> None:
        self.isPlaying         = False
        self.currentNoteIndex  = 0
        self.currentNoteOffset = 0

    def playbackUpdate(self, pcSpeaker:PCSpeaker, deltaT:float) -> bool:
        """
            returns true if sound is still playing, false if sound has finished
        """

        if (not self.isPlaying) and (self.onStart is not None):
            # Note: we invoke onStart here to make sure it always get's called before onEnd
            self.onStart(self)
       
        # get next note to play
        numNotes   = len(self.notes)
        noteIndex  = self.currentNoteIndex
        noteOffset = self.currentNoteOffset
        remainingT = deltaT
        while True:
            if noteIndex >= numNotes:
                # reached end of sound reset and stop playback
                pcSpeaker.stop()
                if self.onEnd is not None:
                    self.onEnd(self)
                self.reset()
                return False

            note = self.notes[noteIndex]
    
            remainingDuration = note.duration - noteOffset
            if remainingDuration > remainingT:
                # found the note to play!
                break 

            # reached end of note, advance to next one
            remainingT-= remainingDuration
            noteOffset = 0
            noteIndex+= 1

        # play the note if it's not already playing
        if (not self.isPlaying) or (noteIndex != self.currentNoteIndex):
            pcSpeaker.play(note.frequency)

        self.isPlaying         = True
        self.currentNoteIndex  = noteIndex
        self.currentNoteOffset = noteOffset + remainingT
        return True

class PCSoundPlayer:
    pcSoundQueue:list[PCSound]

    def __init__(self, pcSpeaker:PCSpeaker):
        self.speaker      = pcSpeaker
        self.pcSoundQueue = []

    def update(self, deltaT:float) -> None:

        numSounds = len(self.pcSoundQueue)
        if numSounds == 0:
            return

        # update sounds in queue
        soundIndex = 0
        while soundIndex < numSounds:
            sound = self.pcSoundQueue[soundIndex]

            if sound.playbackUpdate(self.speaker, deltaT):
                break

            soundIndex+= 1

        # pop of finished sounds from queue
        self.pcSoundQueue = self.pcSoundQueue[soundIndex:]


# -----------------------------------------------------------------------------
# GRAPHICS & ANIMATION OBJECTS
# -----------------------------------------------------------------------------

class AnimationObject:
    width      = 0
    height     = 0
    animations = [[""]]

    animationSpeed   :float = 1
    animationPosition:float = 0

    color: tuple[float, float, float] = COLOR_MED

    x:float = 0
    y:float = 0

    def reset(self) -> None:
        self.animationPosition = 0

    def inBounds(self) -> bool:
        charX1 = int(self.x)
        charX2 = int(self.x + self.width)

        charY1 = int(self.y)
        charY2 = int(self.y + self.height)

        return (charX2 >= 0) and (charX1 <= SCREEN_CHARS_X) and (charY2 >= 0) and (charY1 <= SCREEN_CHARS_Y)

    def update(self, deltaT:float, halloween:"Halloween"):
        self.animationPosition = (self.animationPosition + deltaT * self.animationSpeed) % 1

    def draw(self, surface, font):
        index = int(self.animationPosition * len(self.animations))
        animation = self.animations[index]

        charX = int(self.x)
        for row, str in enumerate(animation):
            charY = int(self.y + row)

            pixelX = RENDER_SCALE * FONT_WIDTH * charX 
            pixelY = RENDER_SCALE * FONT_HEIGHT * charY

            strSurface = font.render(str, True, self.color)
            surface.blit(strSurface, (pixelX, pixelY))


class SpeechBubble(AnimationObject):
    def __init__(self, text:str, xOffset:int, yOffset:int, isRightFacing:bool=True, anchor:AnimationObject|None=None):
        super().__init__()
        self.xOffset       = xOffset
        self.yOffset       = yOffset
        self.isRightFacing = isRightFacing
        self.anchor        = anchor
        
        self.isOpen = False
        self.setText(text)

    def open(self) -> None:
        self.isOpen = True

    def close(self) -> None:
        self.isOpen = False        

    @override
    def draw(self, surface:pygame.Surface, font:pygame.font.Font) -> None:
        if self.isOpen:
            super().draw(surface, font)

    @override
    def update(self, deltaT:float, halloween:"Halloween") -> None:
        super().update(deltaT, halloween)

        # compute new x and y position
        x = self.xOffset if self.isRightFacing else -self.xOffset
        y = self.yOffset

        if self.anchor is not None:
            y+= self.anchor.y - self.height
            x+= self.anchor.x
            
            if self.isRightFacing:
                x+= self.anchor.width
            else:
                x-= self.width

        self.x = x
        self.y = y

    def setText(self, text:str) -> None:
        lines    = text.split('\n')
        numLines = len(lines)

        # compute dimensions
        maxLineLength = 0
        for line in lines:
            lineLength = len(line)
            if lineLength > maxLineLength:
                maxLineLength = lineLength

        self.height = numLines + 2
        self.width  = max(4, maxLineLength + 2)

        animation = [None]*self.height

        # set top and bottomRows
        dashCount = max(0, self.width - 4)
        animation[0]  = f" ,{"-"*dashCount}. "
        animation[-1] = f" `{"-"*dashCount}' "

        # set the inner rows
        lastI = (numLines - 1)
        for i, line in enumerate(lines): 
            lineLength = len(line)

            deltaMaxLength = (self.width - 2) - lineLength
            leadingSpaces  = (deltaMaxLength // 2)
            trailingSpaces = (deltaMaxLength - leadingSpaces)

            if numLines == 1:
                leadingChar  = '('
                trailingChar = ')'

            elif i == 0:
                leadingChar  = '/'
                trailingChar = '\\'

            elif i == lastI:
                leadingChar  = '\\'
                trailingChar = '/'

            else:
                leadingChar  = '|'
                trailingChar = '|'
            
            animation[i+1] = f'{leadingChar}{" "*leadingSpaces}{line}{" "*trailingSpaces}{trailingChar}'

        self.animations = [animation]


class SoundEffect:
    text :str
    notes:list[Note]

    def __init__(self, text:str, notes:list[Note]):
        self.text  = text
        self.notes = notes

class RandomSoundBubble(SpeechBubble):

    def __init__(self, 
                 soundEffects  :list[SoundEffect],
                 xOffset       :float, 
                 yOffset       :float, 
                 isRightFacing :bool, 
                 anchor        :AnimationObject|None,
                 minDelay      :float,
                 maxDelay      :float,
                 bubbleCooldown:float
    ):
        super().__init__('', xOffset, yOffset, isRightFacing, anchor)

        self.soundEffects   = soundEffects
        self.minDelay       = minDelay
        self.maxDelay       = maxDelay
        self.bubbleCooldown = bubbleCooldown

        self.pcSounds = [
            PCSound(soundEffect.notes, self.onSoundStart, self.onSoundEnd) 
            for soundEffect in soundEffects
        ]

        self.isSoundScheduled = False
        
        self.nextSoundEffect()
        self.reset()

    def onSoundStart(self, sound:PCSound) -> None:
        soundEffect = self.soundEffects[self.currentEffectIndex]
        self.setText(soundEffect.text)
        
        self.open()

        self.nextSoundEffect()

    def onSoundEnd(self, sound:PCSound) -> None:
        self.closeDelay = self.bubbleCooldown   
        self.isSoundScheduled = False

    @override
    def reset(self):
        super().reset()

        # close the bubble immediately
        self.closeDelay = 0

    def nextSoundEffect(self) -> None:
        self.currentEffectIndex = random.randint(0, len(self.soundEffects)-1)
        self.soundDelay         = random.uniform(self.minDelay, self.maxDelay)

    @override
    def update(self, deltaT:float, halloween:"Halloween") -> None:
        super().update(deltaT, halloween)
        
        # schedule sound
        if not self.isSoundScheduled:

            if self.soundDelay <= deltaT:
                self.isSoundScheduled = True
        
                pcSound = self.pcSounds[self.currentEffectIndex]
                halloween.soundPlayer.pcSoundQueue.append(pcSound)

            else:
                self.soundDelay-= deltaT

        # close speech bubble
        if self.closeDelay >= 0:
            if self.closeDelay >= deltaT:
                self.closeDelay-= deltaT

            else:
                # Note" -1 indicates speech bubble is closed
                self.closeDelay = -1        
                self.close()


class Ghost(AnimationObject):
    width  = 5
    height = 4
    animations = [
        [
            R" .-. ", 
            R":o o:", 
            R"|   |", 
            R"`~-~'"
        ],
        [
            R" .-. ", 
            R":o o:", 
            R"|   |", 
            R"`-~-`"
        ],    
        [
            R" .-. ", 
            R":o o:", 
            R"|   |", 
            R"'~~~`"
        ],
    ]

    color = COLOR_MED
    maxX  = SCREEN_CHARS_X
    maxY  = SCREEN_CHARS_Y - height

    minSpeed = 1.0
    maxSpeed = 7.0

    minAnimationSpeed = 1
    maxAnimationSpeed = 2

    soundEffects = [
        SoundEffect(
            text  = "BOoo..",
            notes = [
                Note(300, 45e-3), 
                Note(320, 45e-3), 
                Note(350, 45e-3), 
                Note(380, 45e-3), 
                Note(420, 45e-3), 
                Note(450, 45e-3), 
                Note(480, 45e-3), 
                Note(500, 45e-3), 
                Note(480, 45e-3), 
                Note(450, 45e-3), 
                Note(480, 45e-3), 
                Note(520, 45e-3), 
                Note(500, 45e-3),
            ]
        ),
        SoundEffect(
            text  = "Trick\nor\nTreat",
            notes = [
                Note(440, 70e-3),
                Note(370, 70e-3),
                Note(311, 70e-3),
                Note(220, 70e-3),
            ]
        ),
    ]

    def __init__(self):
        super().__init__()

        self.soundBubble = RandomSoundBubble(            
            soundEffects   = self.soundEffects,
            xOffset        = -2, 
            yOffset        = 1, 
            isRightFacing  = True, 
            anchor         = self,
            minDelay       = 5,
            maxDelay       = 15,
            bubbleCooldown = 2,
        )
        self.soundBubble.color = self.color

        self.reset()


    def isRightFacing(self) -> bool:
        return (self.xVelocity > 0)

    @override
    def reset(self) -> None:
        super().reset()

        self.phaseAmplitude = 2
        self.phase          = random.uniform(0, math.pi * 2)
        self.rads_per_sec   = math.radians(20)

        speedT = random.random()
        speed  = lerp(speedT, self.minSpeed, self.maxSpeed)
        self.xVelocity = random.choice([-1,1]) * speed

        self.animationSpeed = lerp(speedT, self.minAnimationSpeed, self.maxAnimationSpeed)
        
        self.x = 0 if self.xVelocity > 0 else self.maxX
        self.y = random.uniform(0, self.maxY)

        self.base_y = self.y

        self.soundBubble.isRightFacing = self.isRightFacing()
        self.soundBubble.reset()

    @override
    def update(self, deltaT:float, halloween:"Halloween") -> None:
        super().update(deltaT, halloween)

        self.phase = (self.phase + deltaT * self.rads_per_sec) % (2*math.pi)

        self.x+= deltaT * self.xVelocity  # Slow drift left     
        self.y = self.base_y + math.sin(self.phase) * self.phaseAmplitude

        if not self.inBounds():
            self.reset()

        self.soundBubble.update(deltaT, halloween)

    @override
    def draw(self, surface:pygame.Surface, font:pygame.font.Font) -> None:
        super().draw(surface, font)
        self.soundBubble.draw(surface, font)

class Witch(AnimationObject):
    width  = 12
    height = 7

    leftAnimations = [
        [
            R"     ,      ",
            R"   _/(_     ",
            R"   {\\      ",
            R"   /;_)     ",
            R"=='/ <===<<<",
            R"   \__\     ",
            R"     ``     ",
        ]
    ]

    rightAnimations = [
        [
            R"      ,     ",
            R"     _)\_   ",
            R"      //}   ",
            R"     (_;\   ",
            R">>>===> \`==",
            R"     /__/   ",
            R"      ``    ",
        ]
    ]

    color = COLOR_BRIGHT
    speed = 12

    minDelay = 3
    maxDelay = 10

    minY = 0
    maxY = 10

    # start slightly off screen
    minX = -width
    maxX = SCREEN_CHARS_X + 1

    soundEffects = [
        SoundEffect(
            text  = "HA HA HA!",
            notes = [
                Note(600, 40e-3),
                Note(500, 40e-3),
                Note(600, 40e-3),
                Note(500, 40e-3),
                Note(650, 40e-3),
                Note(520, 40e-3),
                Note(650, 40e-3),
                Note(520, 40e-3),
                Note(700, 40e-3),
                Note(550, 40e-3),
                Note(700, 40e-3),
                Note(550, 40e-3),
            ]
        )
    ]

    def __init__(self):
        super().__init__()

        self.soundBubble = RandomSoundBubble(            
            soundEffects   = self.soundEffects,
            xOffset        = -2, 
            yOffset        = 3, 
            isRightFacing  = True, 
            anchor         = self,
            minDelay       = 5,
            maxDelay       = 15,
            bubbleCooldown = 2,
        )
        self.soundBubble.color = self.color

        self.reset()

    @override
    def reset(self) -> None:
        super().reset()

        self.y = random.uniform(self.minY, self.maxY)
        self.x = random.choice([self.minX, self.maxX])

        if self.x == self.minX:
            self.animations = self.rightAnimations
            self.xVelocity  = self.speed
            self.soundBubble.isRightFacing = True
        else:
            self.animations = self.leftAnimations
            self.xVelocity  = -self.speed
            self.soundBubble.isRightFacing = False

        self.delay = random.uniform(self.minDelay, self.maxDelay)
        self.soundBubble.reset()

        
    @override
    def update(self, deltaT:float, halloween:"Halloween") -> None:
        if self.delay > deltaT:
            self.delay-= deltaT
            return

        self.delay = 0
        super().update(deltaT, halloween)

        self.x+= deltaT * self.xVelocity
        
        if not self.inBounds():
            self.reset()

        self.soundBubble.update(deltaT, halloween)

    @override
    def draw(self, surface:pygame.Surface, font:pygame.font.Font) -> None:
        super().draw(surface, font)
        self.soundBubble.draw(surface, font)

class Bat(AnimationObject):
    width  = 3
    height = 1

    animations = [
        ["^O^"],
        ["-O-"],
    ]

    color = COLOR_DIM

    maxX = SCREEN_CHARS_X
    maxY = SCREEN_CHARS_Y

    xMaxForce    = 3
    xMinVelocity = -5
    xMaxVelocity = 5
    yMinVelocity = 1
    yMaxVelocity = 5

    soundEffects = [
        SoundEffect(
            text  = "Chirp!",
            notes = [
                Note(2200, 20e-3),
                Note(2050, 20e-3),
                Note(1900, 20e-3),
                Note(1750, 20e-3),
                Note(1600, 20e-3),
                Note(1450, 20e-3),
                Note(1300, 20e-3),
            ]
        )
    ]

    def __init__(self):
        super().__init__()

        self.soundBubble = RandomSoundBubble(            
            soundEffects   = self.soundEffects,
            xOffset        = -1, 
            yOffset        = 1, 
            isRightFacing  = True, 
            anchor         = self,
            minDelay       = 3,
            maxDelay       = 10,
            bubbleCooldown = 1, 
        )
        self.soundBubble.color = self.color

        self.reset()


    @override
    def reset(self) -> None:
        super().reset()

        self.x = random.randint(0, self.maxX)
        self.y = 0

        self.xAcceleration = 0
        self.xVelocity     = random.uniform(self.xMinVelocity, self.xMaxVelocity)
        self.yVelocity     = random.uniform(self.yMinVelocity, self.yMaxVelocity)

        self.soundBubble.reset()
        

    @override
    def update(self, deltaT:float, halloween:"Halloween") -> None:
        super().update(deltaT, halloween)

        self.xAcceleration+= deltaT * self.xMaxForce * random.choice([-1, 0, 1])
        self.xVelocity+=     deltaT * self.xAcceleration

        if self.xVelocity > self.xMaxVelocity:
            self.xVelocity = self.xMaxVelocity

        elif self.xVelocity < self.xMinVelocity:
            self.xVelocity = self.xMinVelocity            

        self.x+= deltaT * self.xVelocity 
        self.y+= deltaT * self.yVelocity

        if not self.inBounds():
            self.reset()

        self.soundBubble.update(deltaT, halloween)


    @override
    def draw(self, surface:pygame.Surface, font:pygame.font.Font) -> None:
        super().draw(surface, font)
        self.soundBubble.draw(surface, font)

class HalloweenSign(AnimationObject):
    width  = 50
    height = 10
    animations = [
        [
            R"                   ___  ___                       ",
            R"         \  \  /`\ \  \ \  \ \  \                 ",
            R"          \__\ \__\ \__' \__' \__\                ",
            R"           \  \ \  \ \    \     \                 ",
            R"            \  \ \  \ \    \     \                ",
            R"                    ___         ___  ___          ",
            R"\  \  /`\ \    \    \  \ \    \ \    \    \.  \   ",
            R" \__\ \__\ \    \    \  \ \  . \ \__  \__  \`\ \  ",
            R"  \  \ \  \ \    \    \  \ \ |`\\ \    \    \ `\\ ",
            R"   \  \ \  \ \___ \___ \__\ \|  `\ \___ \___ \  `\ "[:-1],
        ]
    ]

    def __init__(self):
        super().__init__()
        self.reset()

    @override
    def reset(self) -> None:
        super().reset()
        
        self.flickerSpeed = 0.25
        self.flickerPos   = 0

        self.color = COLOR_BRIGHT

        self.x = (SCREEN_CHARS_X - self.width) / 2
        self.y = (SCREEN_CHARS_Y - self.height) / 2


    @override
    def update(self, deltaT:float, halloween:"Halloween") -> None:
        super().update(deltaT, halloween)

        self.flickerPos = (self.flickerPos + deltaT * self.flickerSpeed) % 1        
        self.color      = COLOR_DIM if (self.flickerPos < .5) else COLOR_BG
 

def drawScanLines(surface:pygame.Surface, color:tuple[float,float,float] = COLOR_BLACK) -> None:
    # Simulate ScanLines (Horizontal CRT phosphor lines)

    x1 = 0
    x2 = RENDER_SCALE * SCREEN_WIDTH

    for y in range(0, SCREEN_HEIGHT, 4):
        y1 = RENDER_SCALE * y
        y2 = y1

        pygame.draw.line(surface, color, (x1, y1), (x2, y2))    


# -----------------------------------------------------------------------------
# GAME SETUP AND LOOP
# -----------------------------------------------------------------------------

class Halloween:

    def __init__(self):

        # PCSpeaker must be called before pygame.init to configure audio defaults
        self.speaker = PCSpeaker()
        self.soundPlayer = PCSoundPlayer(self.speaker)

        # animation objects     
        self.ghosts = [Ghost() for _ in range(NUM_GHOSTS)]
        self.bats   = [Bat() for _ in range(NUM_BATS)]
        self.signs  = [HalloweenSign()]
        self.witches= [Witch() for _ in range(NUM_WITCHES)]

        self.animationObjects = self.signs + self.bats + self.ghosts + self.witches


    def start(self) -> None:
        pygame.init()
        # self.font = pygame.font.SysFont(FONT, RENDER_SCALE * FONT_HEIGHT, bold=True)
        self.font = pygame.font.Font(FONT, RENDER_SCALE * FONT_HEIGHT)
        self.screen = pygame.display.set_mode((RENDER_SCALE * SCREEN_WIDTH, RENDER_SCALE * SCREEN_HEIGHT))
        pygame.display.set_caption("Halloween Screen Saver")

        self.lastUpdateMs = 0
        while True:
            loopMs = pygame.time.get_ticks()
            deltaT = (loopMs - self.lastUpdateMs) / 1000

            # processInput returns false on exit
            if not self.processInput():
                return

            self.soundPlayer.update(deltaT)

            # update screen
            self.screen.fill(COLOR_BG)
            for animationObject in self.animationObjects:
                animationObject.update(deltaT, self)
                animationObject.draw(self.screen, self.font)

            drawScanLines(self.screen)

            pygame.display.flip()
            self.lastUpdateMs = loopMs


    def processInput(self) -> bool:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    pygame.quit()
                    return False
                    
        return True

def main() -> None:
    halloween = Halloween()
    halloween.start()

    
if __name__ == "__main__":
    main()