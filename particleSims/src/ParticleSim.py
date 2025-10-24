from typing import Type

import debugpy
import py5
from colour import Color

from src.particles import *


class ParticleSim(py5.Sketch):
    backgroundColor   :Color
    messageBarColor   :Color
    selectedTextColor :Color
    defaultTextColor  :Color

    gridSize           :int
    viewportGridWidth  :int
    viewportGridHeight :int
    viewportWidth      :int
    viewportHeight     :int    
    
    gridParticleDict    :dict[int, Particle]
    keyParticleTypeDict :dict[str|int, Type[Particle]]
    selectedParticleKey :str|int

    lastDrawMs       :int = 0
    mouseWasPressed  :bool = False
    messageBarHeight :float = 20

    def __init__(self, gridSize:int, viewportGridWidth:int, viewportGridHeight:int):
        super().__init__()

        self.backgroundColor   = Color("black")
        self.messageBarColor   = Color("black")
        self.selectedTextColor = Color("yellow")
        self.defaultTextColor  = Color("white")

        self.gridSize            = gridSize
        self.viewportGridWidth   = viewportGridWidth
        self.viewportGridHeight  = viewportGridHeight
        self.viewportWidth       = gridSize * viewportGridWidth
        self.viewportHeight      = gridSize * viewportGridHeight 
        
        self.gridParticleDict    = {}

        self.keyParticleTypeDict = {
            "1": Sand,
            "2": RainbowSand,
            "3": Fire,
        }
        self.selectedParticleKey = "1"

        
    def enterPy5Thread(self) -> None:
        # attach the debugger to threads created from py5
        if debugpy.is_client_connected():
            debugpy.debug_this_thread()

    def settings(self) -> None:
        self.enterPy5Thread()

        # initialize the window size
        width  = self.viewportWidth
        height = self.viewportHeight + self.messageBarHeight

        self.size(width, height)

    def setup(self) -> None:
        self.enterPy5Thread()

        self.window_title("ParticleSim")

        # setup text
        self.text_font(self.create_font("consolas", 12))
        
        # setup drawing settings
        self.rect_mode(self.CORNER)
        self.color_mode(self.RGB)
        self.no_stroke()

    def draw(self) -> None:
        self.enterPy5Thread()

        # compute deltaT
        drawMs = py5.millis()
        deltaT = 1e-3 * (drawMs - self.lastDrawMs)
    
        # clear the screen
        self.background(self.backgroundColor)

        # update inputs
        self.processInput()

        # update and draw particles
        self.updateParticles(deltaT)
        self.drawParticles()

        # draw UI
        self.drawMessageBar()

        self.lastDrawMs = drawMs

    def updateParticles(self, deltaT:float) -> None:

        # Note: we cache the items in a list to allow modification to particleDict while in the loop
        for index, particle in list(self.gridParticleDict.items()):

            # lazy cleanup of destroyed particles
            if particle.destroyed:
                del self.gridParticleDict[index]
                continue

            particle.update(deltaT)

            # update our particle index if needed
            newIndex = self.getGridIndex(particle.gridX, particle.gridY)
            if newIndex != index:
                
                # check to make sure we aren't overwriting an existing particle
                overwrittenParticle = self.gridParticleDict.get(newIndex, None)
                if (overwrittenParticle is not None) and (overwrittenParticle.destroyed == False):
                    raise Exception(f"Illegal particle movement! Position for {particle} overlaps non destroyed particle: {overwrittenParticle}")

                # update the particle dict for the new index
                self.gridParticleDict[newIndex] = particle
                del self.gridParticleDict[index] 


    def drawParticles(self) -> None:
        for particle in self.gridParticleDict.values():
            if particle.destroyed:
                continue
            
            self.fill(particle.color)
            self.square(
                particle.gridX * self.gridSize, 
                particle.gridY * self.gridSize, 
                self.gridSize
            )

    def drawMessageBar(self) -> None:
        barWidth  = self.width
        barHeight = self.messageBarHeight
        barY      = self.height - barHeight

        textBoxCount  = len(self.keyParticleTypeDict)
        textBoxWidth  = barWidth / textBoxCount
        textBoxHeight = .75 * barHeight
        textBoxY      = barY + .5*(barHeight - textBoxHeight)

        # draw bar background
        self.fill(self.messageBarColor)
        self.rect(0, barY, barWidth, barHeight)

        # draw textBoxes
        self.text_align(self.CENTER)
        for i, (key, particleType) in enumerate(self.keyParticleTypeDict.items()):
            textBoxX = i*textBoxWidth
            
            text = f"{key}: {particleType.__name__}"
            textColor = self.selectedTextColor if (key == self.selectedParticleKey) else self.defaultTextColor

            # compute optimal text size to fit on one line
            self.text_size(textBoxHeight)
            textWidth = self.text_width(text)
            optimalTextSize = textBoxHeight if (textWidth < textBoxWidth) else (textBoxHeight * textBoxWidth/textWidth) 
            
            # draw text
            self.fill(textColor)
            self.text_size(optimalTextSize)
            self.text(
                text,
                textBoxX,
                textBoxY,
                textBoxWidth,
                textBoxHeight
            )

    def spawnParticle(self, gridX:int, gridY:int, particleType:Type[Particle]) -> Particle:
        # destroy existing particle if there 
        self.destroyParticle(gridX, gridY)

        # spawn a new one
        gridIndex = self.getGridIndex(gridX, gridY)
        newParticle = particleType(self, gridX, gridY)
        self.gridParticleDict[gridIndex] = newParticle

        return newParticle
        
    def destroyParticle(self, gridX:int, gridY:int) -> Particle | None:
        gridIndex = self.getGridIndex(gridX, gridY)
        gridParticle = self.gridParticleDict.get(gridIndex, None) 
        
        if gridParticle is not None:
            # destroy & cleanup particle at that location

            if not gridParticle.destroyed:
                gridParticle.destroy()

            del self.gridParticleDict[gridIndex]

        return gridParticle


    def getGridIndex(self, gridX:int, gridY:int) -> int:
        return hash((gridX, gridY))
    
    def getActiveGridParticle(self, gridX:int, gridY:int) -> Particle | None:
        gridIndex = self.getGridIndex(gridX, gridY)
        gridParticle = self.gridParticleDict.get(gridIndex, None)
    
        return None if (gridParticle is None or gridParticle.destroyed) else gridParticle
     
    def getActiveGridNeighbors(self, particle:Particle) -> ParticleNeighbors:
        return ParticleNeighbors(
            up         = self.getActiveGridParticle(particle.gridX,   particle.gridY-1),
            down       = self.getActiveGridParticle(particle.gridX,   particle.gridY+1),
            left       = self.getActiveGridParticle(particle.gridX-1, particle.gridY  ),
            right      = self.getActiveGridParticle(particle.gridX+1, particle.gridY  ),
            
            lowerLeft  = self.getActiveGridParticle(particle.gridX-1, particle.gridY+1),
            lowerRight = self.getActiveGridParticle(particle.gridX+1, particle.gridY+1),

            upperLeft  = self.getActiveGridParticle(particle.gridX-1, particle.gridY-1),
            upperRight = self.getActiveGridParticle(particle.gridX+1, particle.gridY-1),
        )

    def processMouseInput(self) -> None:
        if self.is_mouse_pressed == False:
            self.mouseWasPressed = False        
            return
        
        mouseGridX = (self.viewportGridWidth  * self.mouse_x) // self.viewportWidth
        mouseGridY = (self.viewportGridHeight * self.mouse_y) // self.viewportHeight

        if mouseGridX < 0 or mouseGridX >= self.viewportGridWidth or \
           mouseGridY < 0 or mouseGridY >= self.viewportGridHeight:
            # mouse is out of viewport bounds
            return

        # spawn / delete particles
        selectedParticleType = self.keyParticleTypeDict[self.selectedParticleKey]

        match self.mouse_button:
            case self.LEFT:
                self.spawnParticle(mouseGridX, mouseGridY, selectedParticleType)

            case self.RIGHT:
                self.destroyParticle(mouseGridX, mouseGridY)
            
            case self.CENTER:
                # drop a single particle
                if self.mouseWasPressed == False:
                    self.spawnParticle(mouseGridX, mouseGridY, selectedParticleType)

        self.mouseWasPressed = True

    def processKeyboardInput(self) -> None:
        if not self.is_key_pressed:
            return
        
        keyVal = self.key_code if (self.key == self.CODED) else self.key
        if keyVal in self.keyParticleTypeDict:
            self.selectedParticleKey = keyVal

    def processInput(self) -> None:
        self.processKeyboardInput()
        self.processMouseInput()

    # bind mouse listeners to a single handler for simplicity
    def handleMouseEvent(self, mouseEvent:py5.Py5MouseEvent) -> None:
        self.enterPy5Thread()
        self.processMouseInput()
    
    def mouse_pressed(self, mouseEvent:py5.Py5MouseEvent) -> None:
        self.handleMouseEvent(mouseEvent)

    def mouse_released(self, mouseEvent:py5.Py5MouseEvent) -> None:
        self.handleMouseEvent(mouseEvent)

    def mouse_dragged(self, mouseEvent:py5.Py5MouseEvent) -> None:
        self.handleMouseEvent(mouseEvent)

    def mouse_wheel(self, mouseEvent:py5.Py5MouseEvent) -> None:
        self.handleMouseEvent(mouseEvent)

    # bind key listeners to a single handler for simplicity
    def handleKeyEvent(self, keyEvent:py5.Py5KeyEvent) -> None:
        self.enterPy5Thread()
        self.processKeyboardInput()

    def key_pressed(self, keyEvent:py5.Py5KeyEvent) -> None:
        self.handleKeyEvent(keyEvent)

    def key_released(self, keyEvent:py5.Py5KeyEvent) -> None:
        self.handleKeyEvent(keyEvent)
