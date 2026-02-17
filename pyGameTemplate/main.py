from abc import abstractmethod
import bisect
from copy import copy, deepcopy
from dataclasses import dataclass
from enum import IntEnum, IntFlag
import enum
from itertools import chain
import math
import sys
from typing import Self, overload, override
import pygame

Rect    = pygame.Rect
vec2    = pygame.math.Vector2
Color   = pygame.Color
vec2Arg = tuple[float,float]


def Log(msg:str) -> None:

    # TODO: print to in game console!
    print(f"LOG -> {msg}")


class RenderSurface:
    viewport: "Viewport"

    width : float
    height: float
    
    surface: pygame.surface

    def blit(self, dstX:float, dstY:float) -> None:
        """
            Blits the content of surface to the viewport backbuffer at (dstX, dstY)  
        """
        destPixelCoords = self.viewport.getPixelCoords(dstX, dstY) 
        self.viewport.backbuffer.blit(self.surface, destPixelCoords)

    def replaceSurface(self) -> None:
        """
            Discards old surface and replaces it with a new one of viewport size (width, height).
        """
        pixelSize = self.viewport.getPixelCoords(self.width, self.height)
        self.surface = pygame.Surface(pixelSize, pygame.SRCALPHA)        

    def setSize(self, width:float, height:float) -> None:
        """
            Changes the size of the RenderSurface. This is destroys the content of surface 
        """
        self.width  = width
        self.height = height

        self.replaceSurface()

    def resize(self, width:float, height:float) -> None:
        """
            Resizes the RenderSurface and scales the content of surface accordingly
        """
        self.width  = width
        self.height = height
        
        pixelSize = self.viewport.getPixelCoords(width, height)
        self.surface = pygame.transform.scale(self.surface, pixelSize)        


class ViewportMode(IntEnum):

    # Viewport is manually configured and doesn't change with screen size 
    Fixed   = enum.auto()

    # Preserves viewport unit sizes and adjusts height to fill screen without cropping.
    # Sets screenX and screenY to 0
    Cover   = enum.auto()

    # Preserves viewport width and height and adjusts unit aspect ratio to fill screen 
    # Sets screenX and screenY to 0
    Stretch = enum.auto()

    # Preserves viewport width and height and uses a 1:1 unit aspect ratio fit screen without cropping.
    # Adjusts screenX and screenY to center viewport
    Fit     = enum.auto()

    # Preserves viewport width and height and uses a 1:1 unit aspect ratio fill screen with cropping if needed.
    # Adjusts screenX and screenY to center viewport
    Fill    = enum.auto()


class Viewport:
    mode: ViewportMode

    width : float
    height: float

    unitSizeX: float
    unitSizeY: float
    
    screenX: int
    screenY: int

    screenSurface: pygame.Surface

    backbuffer: pygame.Surface
    renderSurfaces: set[RenderSurface]

    def __init__(self, mode:ViewportMode, screenSurface:pygame.Surface, width:int, height:int, unitSizeX:float=1, unitSizeY:float=1, screenX:int=0, screenY:int=0):        
        self.mode = mode

        self.screenSurface  = screenSurface
        self.renderSurfaces = set()

        self.width  = width
        self.height = height

        self.unitSizeX = unitSizeX
        self.unitSizeY = unitSizeY

        if mode == ViewportMode.Fixed:
            self.screenX = screenX
            self.screenY = screenY

            self.setSize(width, height)

        else:
            self.updateScreenSize()


    def getPixelCoords(self, x:float, y:float) -> tuple[int, int]:
        return (
            math.ceil(x * self.unitSizeX),
            math.ceil(y * self.unitSizeY)
        )

    def getPixelRect(self, origin:vec2Arg, size:vec2Arg) -> Rect:
        return Rect(
            self.getPixelCoords(*origin),
            self.getPixelCoords(*size)
        )

    def setSize(self, width:float, height:float) -> None:
        self.width  = width
        self.height = height
        
        backBufferSize = self.getPixelCoords(width, height)

        self.backbuffer = pygame.Surface(backBufferSize)


    def setUnitSize(self, unitSizeX:int, unitSizeY:int) -> None:
        self.unitSizeX = unitSizeX
        self.unitSizeY = unitSizeY

        backBufferSize = self.getPixelCoords(self.width, self.height)

        self.backbuffer = pygame.Surface(backBufferSize)

        # recreate child surfaces for new pixel size
        for renderSurface in self.renderSurfaces:   
            renderSurface.replaceSurface()


    def setMode(self, mode:ViewportMode) -> None:
        self.mode = mode
        self.updateScreenSize() 

    def updateScreenSize(self) -> None:
        """
            Adjusts viewport width, height, unit size, and screen position in accordance to the current viewport mode 
        """

        if self.mode == ViewportMode.Fixed:
            return
        
        screenWidth, screenHeight = self.screenSurface.get_size()

        if self.mode == ViewportMode.Cover:
            newWidth  = screenWidth  / self.unitSizeX
            newHeight = screenHeight / self.unitSizeY

            self.setSize(newWidth, newHeight)

            self.screenX = 0
            self.screenY = 0

        else:

            maxUnitSizeX = screenWidth  / self.width
            maxUnitSizeY = screenHeight / self.height

            if self.mode == ViewportMode.Stretch:
                self.setUnitSize(maxUnitSizeX, maxUnitSizeY)

                self.screenX = 0
                self.screenY = 0

            else:
                if self.mode == ViewportMode.Fit:
                    newUnitSize = min(maxUnitSizeX, maxUnitSizeY)
                else:
                    newUnitSize = max(maxUnitSizeX, maxUnitSizeY)

                self.setUnitSize(newUnitSize, newUnitSize)

                # center screen
                pixelsX, pixelsY = self.getPixelCoords(self.width, self.height)

                self.screenX = (screenWidth  - pixelsX) // 2
                self.screenY = (screenHeight - pixelsY) // 2

        Log(f"Updated viewport for screen size:({screenWidth}, {screenHeight}) - {self}")


    def __str__(self) -> str:
        return f"Viewport [mode:{self.mode.name} | screenPos:({self.screenX}, {self.screenY}) | size:({self.width}, {self.height}) | unitSize:({self.unitSizeX}, {self.unitSizeY}) | backbufferSize:{self.backbuffer.get_size()}]"

    def createRenderSurface(self, width:float, height:float) -> RenderSurface:

        renderSurface = RenderSurface()
        renderSurface.viewport = self
        renderSurface.width    = width
        renderSurface.height   = height

        renderSurface.replaceSurface()
        
        self.renderSurfaces.add(renderSurface)

        return renderSurface

    def removeRenderSurface(self, renderSurface:RenderSurface) -> None:
        self.renderSurfaces.remove(renderSurface)

    def blitScreen(self) -> None:
        self.screenSurface.blit(self.backbuffer, (self.screenX, self.screenY))



class SpriteSheet:
    surface    : pygame.Surface
    spriteRects: list[Rect]

    spriteWidth : int
    spriteHeight: int

    _tmpSpriteSurface: pygame.Surface 

    @overload
    def __init__(self, spriteSheetPath:str, spriteWidth:int, spriteHeight:int, /): ...
    
    @overload
    def __init__(self, spriteSheetPath:str, spriteWidth:int, spriteHeight:int, spritesX:int, spritesY:int, /): ...
    
    @overload
    def __init__(self, spriteSheetPath:str, spriteWidth:int, spriteHeight:int, spritesX:int, spritesY:int, spriteOffsetX:int, spriteOffsetY:int, /): ...

    def __init__(self, spriteSheetPath:str, spriteWidth:int, spriteHeight:int, spritesX:int|None=None, spritesY:int|None=None, spriteOffsetX:int|None=None, spriteOffsetY:int|None=None):

        self.spriteWidth = spriteWidth
        self.spriteHeight = spriteHeight

        # load spritesheet
        self.surface = pygame.image.load(spriteSheetPath)
        spriteSheetRect = self.surface.get_rect()

        if spriteOffsetX is None:
            spriteOffsetX = 0

        if spriteOffsetY is None:
            spriteOffsetY = 0

        maxSpritesX = (spriteSheetRect.width  - spriteOffsetX)  // spriteWidth
        maxSpritesY = (spriteSheetRect.height - spriteOffsetY)  // spriteHeight

        if spritesX is None:
            spritesX = maxSpritesX

        if spritesY is None:
            spritesY = maxSpritesY

        assert (spriteWidth <= spriteSheetRect.width) and \
               (spriteHeight <= spriteSheetRect.height) \
        , f"spriteSheet is too small! [path: '{spriteSheetPath}' | spriteSheetSize: ({spriteSheetRect.width}, {spriteSheetRect.height})" + \
          f"| spriteOffset: ({spriteOffsetX}, {spritesY}) | spriteSize: ({spriteWidth}, {spriteHeight}) | numSprites({spritesX}, {spritesY})]"


        # create tmp sprite surface used transformations
        self._tmpSpriteSurface = pygame.Surface((spriteWidth, spriteHeight), pygame.SRCALPHA)

        # compute sprite rects
        self.spriteRects = []
        for y in range(spritesY):
            spriteSheetY = spriteOffsetY + y * spriteHeight

            for x in range(spritesX):
                spriteSheetX = spriteOffsetX + x * spriteWidth
                self.spriteRects.append(Rect(spriteSheetX, spriteSheetY, spriteWidth, spriteHeight))

        Log(f"Loaded {(spritesX*spritesY)} sprites from: '{spriteSheetPath}'")


    def blitSprite(self, spriteIndex:int, dstSurface:pygame.Surface, dstCoords:tuple[int,int]=(0,0)) -> None:
        spriteRect = self.spriteRects[spriteIndex]
        dstSurface.blit(self.surface, dstCoords, spriteRect)


    def stretchSprite(self, spriteIndex:int, dstSurface:pygame.Surface) -> None:


        # TODO: annoying that we cant scale a section of a sprite
        #       reduce the number of blits we need to do by caching sprites to their own surfaces for quick scaling
        #       build cache automatically and allow it to be freed 
        self.blitSprite(spriteIndex, self._tmpSpriteSurface)

        scaleSize = dstSurface.get_size()
        pygame.transform.scale(self._tmpSpriteSurface, scaleSize, dstSurface)


    def scale(self, newSpriteWidth:int, newSpriteHeight:int) -> Self:
        """
            Scales the SpriteSheet surface and spriteRects so that each sprite will be sized (newSpriteWidth, newSpriteHeight)
            # This is a lossy operation and cannot be reversed without destroying information
        """

        # compute new spritesheet dimensions
        scaleX = newSpriteWidth / self.spriteWidth
        scaleY = newSpriteHeight / self.spriteHeight

        surfaceWidth, surfaceHeight = self.surface.get_size()

        scaledSurfaceWidth  = math.ceil(surfaceWidth * scaleX)
        scaledSurfaceHeight = math.ceil(surfaceHeight * scaleY)

        # scale everything up
        self.surface = pygame.transform.scale(self.surface, (scaledSurfaceWidth, scaledSurfaceHeight))
        self._tmpSpriteSurface = pygame.Surface((newSpriteWidth, newSpriteHeight), pygame.SRCALPHA)

        self.spriteWidth  = newSpriteWidth
        self.spriteHeight = newSpriteHeight

        for i in range(len(self.spriteRects)):
            rect = self.spriteRects[i]

            scaledRectX = int(rect.left * scaleX)
            scaledRectY = int(rect.top  * scaleY)

            self.spriteRects[i] = Rect(scaledRectX, scaledRectY, newSpriteWidth, newSpriteHeight)

        return self


class SpriteAnimation:
    spriteSheet: SpriteSheet

    startIndex  : int
    endIndex    : int
    currentIndex: int

    isPaused: bool
    updateSpeed: float

    elapsedTime: float = 0
    
    @overload
    def __init__(self, spriteSheet: SpriteSheet, /): ...
    
    @overload
    def __init__(self, spriteSheet: SpriteSheet, startIndex:int, /): ...
    
    @overload
    def __init__(self, spriteSheet: SpriteSheet, startIndex:int, endIndex:int, /): ...
        
    @overload
    def __init__(self, spriteSheet: SpriteSheet, startIndex:int|None=None, endIndex:int|None=None, updateSpeed:float=.5, isPaused:bool=True, /): ...

    def __init__(self, spriteSheet: SpriteSheet, startIndex:int|None=None, endIndex:int|None=None, updateSpeed:float=.5, isPaused:bool=True):
        self.spriteSheet = spriteSheet

        if startIndex is None:
            startIndex = 0

        if endIndex is None:
            endIndex = len(spriteSheet.spriteRects) - 1

        self.startIndex   = startIndex
        self.endIndex     = endIndex
        self.currentIndex = startIndex

        self.isPaused    = isPaused
        self.updateSpeed = updateSpeed

    def reset(self) -> None:
        self.isPaused = True
        self.currentIndex = self.startIndex

    def update(self, deltaT:float) -> None:
        if self.isPaused:
            return

        self.elapsedTime+= deltaT

        if self.elapsedTime >= self.updateSpeed:
            # advance frame
            self.currentIndex+= 1
            if self.currentIndex > self.endIndex:
                self.currentIndex = self.startIndex

            self.elapsedTime%= self.updateSpeed

    
class Transform:
    translation : vec2
    scale       : vec2

    def __init__(self, translation:vec2Arg=(0,0), scale:vec2Arg=(1,1)):
        self.translation = vec2(*translation)
        self.scale       = vec2(*scale)

    def __str__(self) -> str:
        return f"Transform [translation:{self.translation} | scale:{self.scale}]"

    def applyPoint(self, point:vec2) -> vec2:
        return (self.scale.elementwise() * point) + self.translation

    def applyVector(self, vector:vec2) -> vec2:
        return self.scale.elementwise() * vector

    def applyTransform(self, transform:"Transform") -> vec2:
        return Transform(
            self.translation         + transform.translation,
            self.scale.elementwise() * transform.scale
        )

    def inverse(self) -> "Transform":        
        return Transform(
            -self.translation,
            vec2(
                1/self.scale.x if (self.scale.x != 0) else 0,
                1/self.scale.y if (self.scale.y != 0) else 0
            )
        )


class BoundingBox:
    origin: vec2
    size  : vec2

    @property
    def v1(self) -> vec2:
        return self.origin.copy()

    @property
    def v2(self) -> vec2:
        return vec2(self.origin.x + self.size.x, self.origin.y)
    
    @property
    def v3(self) -> vec2:
        return vec2(self.origin.x, self.origin.y + self.size.y)    

    @property
    def v4(self) -> vec2:
        return self.origin + self.size

    def __init__(self, origin:vec2Arg, size:vec2Arg):
        self.origin = vec2(*origin)
        self.size   = vec2(*size)

    def __str__(self) -> str:
        return f"BoundingBox [origin:{self.origin} | size:{self.size}]"

    def transformed(self, transform:Transform) -> "BoundingBox":
        return BoundingBox(
            transform.applyPoint(self.origin),
            transform.applyVector(self.size)
        )

    def transform(self, transform:Transform) -> None:
        self.origin = transform.applyPoint(self.origin),
        self.size   = transform.applyVector(self.size)


    def getVertices(self) -> tuple[vec2, vec2, vec2, vec2]:

        bottomRight = self.origin + self.size
        return (
            self.origin.copy(), 
            vec2(bottomRight.x, self.origin.y), 
            vec2(self.origin.x, bottomRight.y), 
            bottomRight
        )

    def union(self, boundingBox:"BoundingBox") -> "BoundingBox":
        origin = vec2(
            min(self.origin.x, boundingBox.origin.x),
            min(self.origin.y, boundingBox.origin.y)
        )

        v4   = self.v4
        bbV4 = boundingBox.v4

        size = vec2(
            max(v4.x, bbV4.x) - origin.x,
            max(v4.y, bbV4.y) - origin.y
        )

        return BoundingBox(origin, size)

    def intersection(self, boundingBox:"BoundingBox") -> "BoundingBox":
        origin = vec2(
            max(self.origin.x, boundingBox.origin.x),
            max(self.origin.y, boundingBox.origin.y)
        )

        v4   = self.v4
        bbV4 = boundingBox.v4

        size = vec2(
            min(v4.x, bbV4.x) - origin.x,
            min(v4.y, bbV4.y) - origin.y
        )

        return BoundingBox(origin, size)        


    def contains(self, x:float, y:float) -> bool:
        # check lower bounds
        if (x < self.origin.x) or (y < self.origin.y):
            return False
        
        # check upper bounds
        v4 = self.v4
        if (x > v4.x) or (y > v4.y):
            return False

        return True

    def intersects(self, boundingBox:"BoundingBox") -> bool:
        # check lower bounds
        v4 = self.v4
        if (v4.x < boundingBox.origin.x) or (v4.y < boundingBox.origin.y):
            return False
        
        # check upper bounds
        bbV4 = boundingBox.v4
        if (self.origin.x > bbV4.x) or (self.origin.y > bbV4.y):
            return False

        return True


# Note: pygame uses sprite colliders with integer units, so we implement our own
#       floating point colliders for better granularity
class Collider:
    name  : str    
    debug : bool

    boundingBox            : BoundingBox
    transform              : Transform
    transformedBoundingBox : BoundingBox

    _collisionMaps: set["CollisionMap"]

    def __init__(self, name:str, boundingBox:BoundingBox, transform:Transform|None=None,debug:bool=False):
        self.name        = name
        self.debug       = debug
        self.boundingBox = boundingBox

        self.transform              = transform if transform is not None else Transform()
        self.transformedBoundingBox = boundingBox.transformed(self.transform)

        self._collisionMaps = set()

    def __str__(self) -> str:
        return f"{self.__class__.__name__} ({self.name}) [{self.transformedBoundingBox}]"

    # Note: used for sorting for bisect lookups
    def __lt__(self, collider:"Collider") -> int:
        return id(self) - id(collider)

    def __gt__(self, collider:"Collider") -> int:
        return id(collider) - id(self)

    @abstractmethod
    def intersects(self, collider:"Collider") -> bool: ...

    @abstractmethod
    def draw(self, color:Color, boardWidth:int) -> None: ...    

    def onEnter(self, collisionMap:"CollisionMap", collider:"Collider") -> None:
        if self.debug:
            Log(f"Collision onEnter [{collisionMap} | self:{self} | collider2:{collider}]")

    def onExit(self, collisionMap:"CollisionMap", collider:"Collider") -> None:
        if self.debug:
            Log(f"Collision onExit [{collisionMap} | self:{self} | collider:{collider}]")


    def applyUpdates(self, transform:Transform|None=None, boundingBox:BoundingBox|None=None) -> None:
        oldTransformedBoundingBox = self.transformedBoundingBox

        if transform is None:
            transform = self.transform
        else:
            self.transform   = transform

        if boundingBox is None:
            boundingBox = self.boundingBox
        else:
            self.boundingBox = boundingBox

        self.transformedBoundingBox = boundingBox.transformed(transform)

        for collisionMap in self._collisionMaps:
            collisionMap.updateCollider(self, oldTransformedBoundingBox, self.transformedBoundingBox)


# TODO: Add ellipse collider which can double as a circle collider
class RectangleCollider(Collider):

    def __init__(self, name:str, origin:vec2Arg, size:vec2Arg, transform:Transform|None=None, debug:bool=False):
        super().__init__(name, BoundingBox(origin, size), transform, debug)

    @override
    def intersects(self, collider:Collider) -> bool:
        return self.transformedBoundingBox.intersects(collider.transformedBoundingBox)

    @override
    def draw(self, color:Color, boardWidth:int) -> None:
        colliderPixelRect = Game.instance.viewport.getPixelRect(self.transformedBoundingBox.origin, self.transformedBoundingBox.size)
        pygame.draw.rect(Game.instance.viewport.backbuffer, color, colliderPixelRect, boardWidth)

class EllipseCollider(Collider):
    def __init__(self, name:str, origin:vec2Arg, size:vec2Arg, transform:Transform|None=None, debug:bool=False):
        super().__init__(name, BoundingBox(origin, size), transform, debug)

    @override
    def intersects(self, collider:Collider) -> bool:
        return self.transformedBoundingBox.intersects(collider.transformedBoundingBox)

    @override
    def draw(self, color:Color, boardWidth:int) -> None:
        colliderPixelRect = Game.instance.viewport.getPixelRect(self.transformedBoundingBox.origin, self.transformedBoundingBox.size)        
        pygame.draw.rect(Game.instance.viewport.backbuffer, color, colliderPixelRect, boardWidth)
        pygame.draw.ellipse(Game.instance.viewport.backbuffer, color, colliderPixelRect, boardWidth)




class CollisionMap:
    name     : str
    gridSize : float
    debug    : bool

    debugBoarderWidth  : int = 1
    debugGridColor     : Color = Color("blue")
    debugColliderColor : Color = Color("green")
    debugCollisionColor: Color = Color("red")
   
    _colliderGrid  : dict[int, list[Collider]]
    _collisionDict : dict[Collider, set[Collider]]

    def __init__(self, name:str, gridSize:int, debug:bool=False):
        self.name           = name
        self.gridSize       = gridSize
        self.debug          = debug
        self._colliderGrid  = {}
        self._collisionDict = {}


    def __str__(self) -> str:
        return f"CollisionMap ({self.name}) [gridSize:{self.gridSize}]"

    def coordsToGrid(self, coords:vec2) -> tuple[int, int]:
        return (
            int(coords.x / self.gridSize),
            int(coords.y / self.gridSize)
        )

    def gridToHash(self, x:int, y:int) -> int:
        return (x << 32) | (y & 0xFFFFFFFF)


    def hashToCoords(self, hashValue:int) -> vec2:
        return vec2(
            self.gridSize * (hashValue >> 32),
            self.gridSize * (hashValue & 0xFFFFFFFF)
        )

    def coordsToHash(self, coords:vec2) -> int:
        return (int(coords.x / self.gridSize) << 32) | (int(coords.y / self.gridSize) & 0xFFFFFFFF)


    def _enterCollision(self, collider1:Collider, collider2:Collider) -> None:        
        if self.debug:
            Log(f"Collision Enter Event [{self} | collider1:{collider1} | collider2:{collider2}]")
        
        self._collisionDict[collider1].add(collider2)
        self._collisionDict[collider2].add(collider1)

        collider1.onEnter(self, collider2)
        collider2.onEnter(self, collider1)

    def _exitCollision(self, collider1:Collider, collider2:Collider) -> None:
        if self.debug:
            Log(f"Collision Exit Event [{self} | collider1:{collider1} | collider2:{collider2}]")        

        collider1.onExit(self, collider2)
        collider2.onExit(self, collider1)

        self._collisionDict[collider1].discard(collider2)
        self._collisionDict[collider2].discard(collider1)


    def _insert(self, collider:Collider, hashValue:int) -> None:
        if self.debug:
            Log(f"Inserting collider [{self} | collider:{collider} | coords:{self.hashToCoords(hashValue)}]")

        if hashValue in self._colliderGrid:
            gridColliders = self._colliderGrid[hashValue]

            insertIndex = bisect.bisect_left(gridColliders, collider)
            if insertIndex < len(gridColliders) and gridColliders[insertIndex] == collider:
                # don't insert duplicates
                Log(f"WARNING - Skipping Insertion, collider already present in grid [{self} | collider:{collider} | coords:{self.hashToCoords(hashValue)}]")
                return

            # check for new collisions withing gridCell
            collisionSet = self._collisionDict[collider] 
            for collider2 in gridColliders:
                if (collider2 not in collisionSet) and collider.intersects(collider2):
                    self._enterCollision(collider, collider2)

            gridColliders.insert(insertIndex, collider)

        else:
            self._colliderGrid[hashValue] = [collider]


    def _remove(self, collider:Collider, hashValue:int) -> None:
        gridColliders = self._colliderGrid[hashValue]

        index = bisect.bisect_left(gridColliders, collider)
        if index == len(gridColliders) or gridColliders[index] != collider:
            Log(f"WARNING - Attempting to remove noninserted collider! [{self} | collider:{collider} | coords:{self.hashToCoords(hashValue)}]")
            return

        if self.debug:
            Log(f"Removing collider [{self} | collider:{collider} | coords:{self.hashToCoords(hashValue)}]")

        gridColliders.pop(index)

        # check for collision exit events
        collisionSet  = self._collisionDict[collider]
        numCollisions = len(collisionSet)

        numGridColliders = len(gridColliders)
        collider2Index   = 0
        while (numCollisions > 0) and (collider2Index < numGridColliders):
            collider2 = gridColliders[collider2Index]
            
            if (collider2 in collisionSet) and (not collider.intersects(collider2)):
                self._exitCollision(collider, collider2)        
                numCollisions-= 1

            collider2Index+= 1


        # TODO: really just push this to array of keys to check for deletion on update
        #       so we don't call this when making small moves!
        if(numGridColliders == 0):
            del self._colliderGrid[hashValue]
        

    def insertCollider(self, collider:Collider) -> None:
        if collider not in self._collisionDict:
            self._collisionDict[collider] = set()
        else:
            Log(f"WARNING - Inserted collider already in collisionDict! [{self} | collider:{collider}]")            

        collider._collisionMaps.add(self)

        x1, y1 = self.coordsToGrid(collider.transformedBoundingBox.origin)
        x2, y2 = self.coordsToGrid(collider.transformedBoundingBox.v4)

        for x in range(x1, x2+1):
            for y in range(y1, y2+1):
                self._insert(collider, self.gridToHash(x, y))


    def removeCollider(self, collider:Collider) -> None:
        x1, y1 = self.coordsToGrid(collider.transformedBoundingBox.origin)
        x2, y2 = self.coordsToGrid(collider.transformedBoundingBox.v4)

        for y in range(y1, y2+1):
            for x in range(x1, x2+1):
                self._remove(collider, self.gridToHash(x, y))

        if collider in self._collisionDict:
            del self._collisionDict[collider]
            
        else:
            Log(f"WARNING - Removed collider missing from collisionDict! [{self} | collider:{collider}]")

        collider._collisionMaps.discard(self)

    def updateCollider(self, collider:Collider, oldTransformedBoundingBox:BoundingBox, newTransformedBoundingBox:BoundingBox) -> None:
        
        # TODO: clean this up ... we rely on coordsToGrid a lot... really should just return a rect with a single call?
        #       pygame Rect may be heavy and also my not allow for proper intersections

        oldX1, oldY1 = self.coordsToGrid(oldTransformedBoundingBox.origin)
        oldX2, oldY2 = self.coordsToGrid(oldTransformedBoundingBox.v4)

        newX1, newY1 = self.coordsToGrid(newTransformedBoundingBox.origin)
        newX2, newY2 = self.coordsToGrid(newTransformedBoundingBox.v4)
 
        
        # remove collider from exclusively old grid cells
        for y in range(oldY1, oldY2+1):
            for x in range(oldX1, oldX2+1):
                
                if y >= newY1 and y <= newY2 and x >= newX1 and x <= newX2:
                    # skip intersection of old and new grid cells
                    continue

                self._remove(collider, self.gridToHash(x, y))


        collisionSet = self._collisionDict[collider]

        for y in range(newY1, newY2+1):
            for x in range(newX1, newX2+1):
                gridHash = self.gridToHash(x, y)

                if y >= oldY1 and y <= oldY2 and x >= oldX1 and x <= oldX2:
                    
                    # update collisions within intersecting grid cell
                    for gridCollider in self._colliderGrid[gridHash]:
                        if gridCollider == collider:
                            continue

                        isIntersecting = collider.intersects(gridCollider)

                        if gridCollider in collisionSet:                            
                            if not isIntersecting:
                                self._exitCollision(collider, gridCollider)

                        else:
                            if isIntersecting:
                                self._enterCollision(collider, gridCollider)

                else:
                    # insert collider into exclusively new grid cell
                    self._insert(collider, gridHash)


    def hasCollision(self, collider:Collider) -> bool:
        return (collider in self._collisionDict) and (len(self._collisionDict[collider]) > 0) 


    def render(self) -> None:        

        # TODO: NEED TO REPLACE RENDERING LOGIC WITH SOMETHING THAT SUPPORTS WORLD COORDS!
        #       something like renderer.pushRect(worldOrigin, worldSize) and renderer.pushSprite()
        #       then maybe these functions get renamed to draw?

        if self.debug:
            # draw the collision map grids
            for gridHash in self._colliderGrid.keys():

                gridCoords = self.hashToCoords(gridHash)
                gridPixelRect = Game.instance.viewport.getPixelRect(gridCoords, (self.gridSize, self.gridSize))
                
                pygame.draw.rect(Game.instance.viewport.backbuffer, self.debugGridColor, gridPixelRect, self.debugBoarderWidth)

        # render colliders
        for (collider, collisionSet) in self._collisionDict.items():
            if not collider.debug:
                continue

            colliderColor = self.debugCollisionColor if (len(collisionSet) > 0) else self.debugColliderColor
            collider.draw(colliderColor, self.debugBoarderWidth)

            for collisionCollider in collisionSet:
                collisionCollider.draw(self.debugCollisionColor, self.debugBoarderWidth)


class MapTile:
    name           : str
    spriteAnimation: SpriteAnimation
    collider       : Collider|None

    def __init__(self, name:str, spriteAnimation:SpriteAnimation, collider:Collider|None=None):
        self.name            = name
        self.spriteAnimation = spriteAnimation
        self.collider        = collider

        Log(f"Created {self}")


    def Instantiate(self, transform:Transform) -> "MapTile":
        if self.collider is None:
            return self
        
        collider = deepcopy(self.collider)
        collider.applyUpdates(transform=transform)
        
        return MapTile(
            self.name,
            self.spriteAnimation,
            collider
        )

    def update(self, deltaT:float) -> None:
        self.spriteAnimation.update(deltaT)

    def __str__(self) -> str:
        return f"MapTile ({self.name}) [collider:{self.collider}]"


class Map:
    name   : str
    origin : vec2
    debug  : bool

    tileSize : vec2
    tilesX   : int
    tilesY   : int   
    tiles    : list[MapTile]

    debugBorderWidth: int = 1
    debugBorderColor: Color = Color("black")
    
    _tileRenderSurface: RenderSurface

    def __init__(self, name:str, tilesX:int, tilesY:int, tiles:list[MapTile], tileSize:vec2Arg=(1,1), origin:vec2Arg=(0,0), debug:bool=False):
        numTiles = tilesX * tilesY
        assert (numTiles == len(tiles)), f"Failed to create map: '{name}' with dimensions: ({tilesX}, {tilesY}). Expected tiles array of length:{numTiles}, got:{len(tiles)}!"

        self.name   = name
        self.origin = origin
        self.debug  = debug

        self.tilesX   = tilesX
        self.tilesY   = tilesY
        self.tileSize = vec2(tileSize)
        self.tiles    = tiles

        self._tileRenderSurface = Game.instance.viewport.createRenderSurface(self.tileSize.x, self.tileSize.y)

        # dynamically move collider to correct world coordinates!
        # TODO: this is messy ... can we clean this up a bit!
        for i, tile in enumerate(tiles):

            if tile.collider is not None:
                newTile = tile.Instantiate(Transform(self.getTileCoords(i), tileSize))
                Game.instance.collisionMap.insertCollider(newTile.collider)

                self.tiles[i] = newTile


        Log(f"Created Map: '{name}' with {numTiles} tiles [dimensions:({tilesX}, {tilesY}) | origin:{self.origin}]")

    def getTile(self, x:int, y:int) -> MapTile:
        return self.tiles[y*self.tilesX + x]

    def getTileCoords(self, index:int) -> vec2:
        return (
            self.tileSize.x * (index %  self.tilesX),
            self.tileSize.y * (index // self.tilesX)            
        )

    def setTileSize(self, tileWidth:float, tileHeight:float) -> None:

        self.tileSize = vec2(tileWidth, tileHeight)
        self._tileRenderSurface.setSize(tileWidth, tileHeight)

        for i, tile in enumerate(self.tiles):
            if tile.collider is not None:
                tile.collider.transform = Transform(
                    translation = self.getTileCoords(i),
                    scale       = self.tileSize
                )        
                

    def render(self) -> None:

        # TODO: REPLACE THIS HACKED CODE WITH SOMETHIHNG THAT SUPPORTS CAMERA!
        
        for tileY in range(self.tilesY):
            for tileX in range(self.tilesX):

                tile = self.tiles[tileY*self.tilesX + tileX]
                tileAnimation = tile.spriteAnimation
                tileSpriteSheet = tileAnimation.spriteSheet

                dstX = tileX * self.tileSize.x
                dstY = tileY * self.tileSize.y
            
                tileSpriteSheet.stretchSprite(tileAnimation.currentIndex, self._tileRenderSurface.surface)
                self._tileRenderSurface.blit(dstX, dstY)

                # TODO: clean this up!
                if self.debug:
                    dstRect = self._tileRenderSurface.viewport.getPixelRect((dstX, dstY), self.tileSize) 
                    pygame.draw.rect(self._tileRenderSurface.viewport.backbuffer, self.debugBorderColor, dstRect, self.debugBorderWidth)


    
    def update(self, deltaT:float) -> None:
        for tile in self.tiles:
            tile.update(deltaT)

class SpriteEntity:
    size     : vec2
    transform: Transform
    velocity : vec2

    collider: Collider|None = None

    currentAnimation : SpriteAnimation|None = None

    renderSurface: RenderSurface


    def __init__(self, transform:Transform|None=None, size:vec2Arg=(1,1), velocity:vec2Arg=(0,0)):
        self.size      = vec2(*size)
        self.transform = transform if transform is not None else Transform()
        self.velocity  = vec2(*velocity)

        renderSize = self.transform.scale.elementwise() * self.size
        self.renderSurface = Game.instance.viewport.createRenderSurface(renderSize.x,  renderSize.y)

    def update(self, deltaT) -> None:
        self.transform.translation += self.velocity * deltaT

        if self.collider is not None:
            self.collider.applyUpdates(transform=self.transform)

        if self.currentAnimation is not None:
            self.currentAnimation.update(deltaT)

    def render(self) -> None:

        if self.currentAnimation is not None:

            # TODO: we need to offset position by the current camera / world coordinates!

            self.currentAnimation.spriteSheet.stretchSprite(self.currentAnimation.currentIndex, self.renderSurface.surface)
            self.renderSurface.blit(self.transform.translation.x, self.transform.translation.y)



class Cactus(SpriteEntity):
    spriteSheet = SpriteSheet("resources/sprites/cactus.png", 20, 20)

    damage: float = 20

    def __init__(self, transform:Transform|None=None, size:vec2Arg=(1,1), velocity:vec2Arg=(0,0)):
        super().__init__(transform, size, velocity)

        self.currentAnimation = SpriteAnimation(Cactus.spriteSheet, isPaused=False)


class SpriteDirection(IntEnum):
    Up    = enum.auto()
    Down  = enum.auto()
    Left  = enum.auto()
    Right = enum.auto()

class SpriteAnimationId(IntEnum):
    WalkUp    = SpriteDirection.Up
    WalkDown  = SpriteDirection.Down
    WalkLeft  = SpriteDirection.Left
    WalkRight = SpriteDirection.Right

class SpriteCharacter(SpriteEntity):

    animations: dict[SpriteAnimationId, SpriteAnimation]

    health : float = 100

    isWalking: bool = False

    walkingSpeed : float = 1

    heading: vec2

    def __init__(self, transform:Transform|None=None, size:vec2Arg=(1,1), velocity:vec2Arg=(0,0)):
        super().__init__(transform, size, velocity)
        self.heading = vec2(0, 1)

    def getSpriteDirection(self) -> SpriteDirection:
        headingSquaredX = self.heading.x * self.heading.x 
        headingSquaredY = self.heading.y * self.heading.y 

        if headingSquaredX > headingSquaredY:
            return SpriteDirection.Right if (self.heading.x > 0) else SpriteDirection.Left
        else:
            return SpriteDirection.Down if (self.heading.y > 0) else SpriteDirection.Up


    def update(self, deltaT:float) -> None:
        
        spriteDirection = self.getSpriteDirection()
        spriteAnimation = self.animations[spriteDirection]

        walkingVelocity:vec2
        if self.isWalking:
            walkingVelocity = self.walkingSpeed * self.heading
            spriteAnimation.isPaused = False

        else:
            walkingVelocity = vec2(0, 0)

            if not spriteAnimation.isPaused:
                spriteAnimation.isPaused = True
                spriteAnimation.reset()


        self.currentAnimation = spriteAnimation

        # TODO: add kickback and such here
        self.velocity = walkingVelocity

        super().update(deltaT)

    # TODO: take damage and all that jazz here!


class Ghost(SpriteCharacter):
    spriteSheet = SpriteSheet("resources/sprites/magic.png", 20, 20)

    def __init__(self, transform:Transform|None=None, size:vec2Arg=(1,1), velocity:vec2Arg=(0,0)):
        super().__init__(transform, size, velocity)

        self.animations = {
            SpriteAnimationId.WalkUp   : SpriteAnimation(Ghost.spriteSheet, 0, 1),
            SpriteAnimationId.WalkDown : SpriteAnimation(Ghost.spriteSheet, 4, 5),
            SpriteAnimationId.WalkLeft : SpriteAnimation(Ghost.spriteSheet, 6, 7),
            SpriteAnimationId.WalkRight: SpriteAnimation(Ghost.spriteSheet, 2, 3),
        }

    # TODO: follow human if they are in bounds... otherwise, play animation even if not moving


@dataclass(init=False, frozen=True)
class DesertTiles:
    spriteSheet = SpriteSheet("resources/sprites/desertGroundTextures.png", 200, 200, 5, 2)

    ground    = MapTile("DesertGround",    SpriteAnimation(spriteSheet, 1, 1))
    pit       = MapTile("DesertPit",       SpriteAnimation(spriteSheet, 5, 5), collider=EllipseCollider("pit", origin=(.18, .15), size=(.55, .75), debug=True))
    quickSand = MapTile("DesertQuickSand", SpriteAnimation(spriteSheet, 6, 7, updateSpeed=1, isPaused=False), collider=RectangleCollider("slowdown", origin=(0,0), size=(1,1)))


class DesertMap1(Map):
    ghosts: list[Ghost]
    cacti : list[Cactus]

    def __init__(self, debug:bool=False):
        super().__init__(
            name     = "DesertMap1", 
            debug    = debug,
            tileSize = (2, 2),
            tilesX   = 5, 
            tilesY   = 5,
            tiles    = [
              DesertTiles.ground,    DesertTiles.ground, DesertTiles.ground, DesertTiles.ground,    DesertTiles.ground,
              DesertTiles.ground,    DesertTiles.pit,    DesertTiles.ground, DesertTiles.quickSand, DesertTiles.ground,
              DesertTiles.quickSand, DesertTiles.ground, DesertTiles.ground, DesertTiles.ground,    DesertTiles.ground,
              DesertTiles.ground,    DesertTiles.ground, DesertTiles.ground, DesertTiles.pit,       DesertTiles.ground,
              DesertTiles.ground,    DesertTiles.ground, DesertTiles.ground, DesertTiles.ground,    DesertTiles.ground,
            ]
        )

        self.cacti = [
            Cactus(Transform((1, 2))),
            Cactus(Transform((7, 4))),
            Cactus(Transform((5, 8))),
        ]

        self.ghosts = []
        

    def update(self, deltaT:float) -> None:
        super().update(deltaT)

        for cactus in self.cacti:
            cactus.update(deltaT)

        # TODO: spawn a new ghosts as time progresses!

        for ghost in self.ghosts:
            ghost.update(deltaT)


    def render(self) -> None:
        super().render()

        for cactus in self.cacti:
            cactus.render()

        for ghost in self.ghosts:
            ghost.render()




class MagicBlast(SpriteEntity):
    spriteSheet = SpriteSheet("resources/sprites/magic.png", 20, 20)
    damage: float = 20

    def __init__(self, transform:Transform|None=None, size:vec2Arg=(1,1), velocity:vec2Arg=(0,0)):
        super().__init__(transform, size, velocity)
    
        self.currentAnimation = SpriteAnimation(MagicBlast.spriteSheet, isPaused=False) 

    # TODO: check to see if we hit an entity if we did give it damage and despawn


class Player(SpriteCharacter):
    spriteSheet = SpriteSheet("resources/sprites/cowboy.png", 20, 20)

    def __init__(self, transform:Transform|None=None, size:vec2Arg=(1,1), velocity:vec2Arg=(0,0)):
        super().__init__(transform, size, velocity)
    
        self.animations = {
            SpriteAnimationId.WalkUp   : SpriteAnimation(Player.spriteSheet, 0, 1, updateSpeed=.15),
            SpriteAnimationId.WalkDown : SpriteAnimation(Player.spriteSheet, 4, 5, updateSpeed=.15),
            SpriteAnimationId.WalkLeft : SpriteAnimation(Player.spriteSheet, 6, 7, updateSpeed=.15),
            SpriteAnimationId.WalkRight: SpriteAnimation(Player.spriteSheet, 2, 3, updateSpeed=.15),
        }

        self.collider = RectangleCollider(
            name   = "playerFeet", 
            origin = (.25,.75), 
            size   = (.50,.25), 
            debug  = True
        )


        Game.instance.collisionMap.insertCollider(self.collider)


class GameCommands(IntFlag):
    MoveUp    = enum.auto()
    MoveDown  = enum.auto()
    MoveLeft  = enum.auto()
    MoveRight = enum.auto()

    MoveMask = MoveUp|MoveDown|MoveLeft|MoveRight

class Game:
    instance: "Game"

    font: pygame.font.Font

    collisionMap: CollisionMap
    map: Map

    player: Player

    commands: GameCommands = 0

    framerate: float

    viewport: Viewport 
    windowSurface: pygame.Surface
    
    def __init__(self, title:str, width:int, height:int, frameRate:float = 60):
        Game.instance = self

        pygame.init()

        self.windowSurface = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(title)

        self.viewport = Viewport(ViewportMode.Fit, self.windowSurface, 10, 10)

        self.font = pygame.font.SysFont("Consolas", 12)

        self.collisionMap = CollisionMap("GameCollisionMap", 1, debug=True)
        self.map          = DesertMap1(debug=True)
        
        self.player = Player()

        self.framerate = frameRate
        self.loopClock = pygame.time.Clock()




    def start(self) -> None:

        deltaT:float = 0
        loopClock = pygame.time.Clock()
        while True:

            self.update(deltaT)
            self.render()
 
            deltaMs = loopClock.tick(self.framerate)
            deltaT = .001 * deltaMs
                

    def update(self, deltaT:int) -> None:       
        
        self.processEvents()
        
        self.map.update(deltaT)

        self.player.update(deltaT)

    def processEvents(self) -> None:
        for event in pygame.event.get():

            match(event.type):
                case pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                
                case pygame.WINDOWSIZECHANGED:
                    self.viewport.updateScreenSize()

                case pygame.KEYUP:
                    self.processKeyEvent(event)

                case pygame.KEYDOWN:
                    self.processKeyEvent(event)


    def processKeyEvent(self, event:pygame.event.Event) -> None:
    
        isKeyDownEvent = (event.type == pygame.KEYDOWN)

        match(event.key):
            case pygame.K_w:                            
                if isKeyDownEvent:
                    self.commands|= GameCommands.MoveUp
                else:
                    self.commands&= ~GameCommands.MoveUp
                
            case pygame.K_a:
                if isKeyDownEvent:
                    self.commands|= GameCommands.MoveLeft
                else:
                    self.commands&= ~GameCommands.MoveLeft

            case pygame.K_s:
                if isKeyDownEvent:
                    self.commands|= GameCommands.MoveDown
                else:
                    self.commands&= ~GameCommands.MoveDown

            case pygame.K_d:
                if isKeyDownEvent:
                    self.commands|= GameCommands.MoveRight
                else:
                    self.commands&= ~GameCommands.MoveRight

            case _: return 


        # TODO: CLEAN THIS AND ABSTRACT CONTROLS TO A COMMON CLASS
        #       THAT CAN HAVE KEY BINDINGS OVERRIDED
        #       ALSO - FIX SPRITE ANIMATIONS NOT WORKING FOR PLAYER WHILE MOVING!

        moveDirection = vec2(0, 0)
        if self.commands & GameCommands.MoveUp:
            moveDirection.y-= 1

        if self.commands & GameCommands.MoveDown:
            moveDirection.y+= 1 

        if self.commands & GameCommands.MoveLeft:
            moveDirection.x-= 1

        if self.commands & GameCommands.MoveRight:
            moveDirection.x+= 1

        isMoving = (moveDirection.magnitude_squared() != 0)

        self.player.isWalking = isMoving

        if isMoving:
            self.player.heading = moveDirection.normalize()


    def render(self) -> None:
        self.map.render() 
        self.player.render()        
        self.collisionMap.render()

        # TODO: render the UI

        self.viewport.blitScreen()
        pygame.display.flip()


def main() -> None:
    game = Game("My Game", 600, 600)
    game.start()


if __name__ == "__main__":
    main()
