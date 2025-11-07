from typing import Self, overload

import cv2
import numpy as np
from matplotlib import pyplot as plt


class Image:
    width  :int
    height :int
    depth  :int 

    _pixelBuffer :np.ndarray[np.float32]
    _windowName  :str|None = None

    @staticmethod
    def plotImages(imageDict:dict["Image", str], title:str="", cmap:str="gray") -> None:
        numSubplots = len(imageDict)

        # Note: order matters. We favor larger numSubplotsX over numSubplotsY  
        numSubplotsY = int(np.round(np.sqrt(numSubplots)))
        numSubplotsX = int(np.ceil(numSubplots / numSubplotsY))

        fig = plt.figure(title)
        for i,(image, name) in enumerate(imageDict.items()):
            ax = fig.add_subplot(numSubplotsY, numSubplotsX, i+1)
            ax.title.set_text(name)
            ax.imshow(image.pixelsRGB, cmap=cmap)

        fig.tight_layout()
        
        plt.show()        

    @overload
    def __init__(self, path:str, /): ...

    @overload
    def __init__(self, image:"Image", /): ...

    @overload
    def __init__(self, buffer:np.ndarray, /): ...    

    @overload
    def __init__(self, width:int, height:int, depth:int = 3, /): ...

    def __init__(self, *args):        
        numArgs = len(args)

        if numArgs == 1:        
            arg0 = args[0]
            
            if isinstance(arg0, Image):
                # copy constructor
                self._pixelBuffer = arg0._pixelBuffer.copy()
                self.width        = arg0.width
                self.height       = arg0.height
                self.depth        = arg0.depth
    
            elif isinstance(arg0, str):
                # path constructor
                self._pixelBuffer = np.array(cv2.imread(arg0), dtype=np.float32)
                self.height, self.width, self.depth = self._pixelBuffer.shape
            
            else:
                # buffer constructor
                # Note: we make convert 2D arrays to 3D by appending color dimension
                arg0Shape = arg0.shape
                pixelBufferShape = (arg0Shape[0], arg0Shape[1], 1 if len(arg0Shape) == 2 else arg0Shape[2])

                self._pixelBuffer = np.array(arg0, dtype=np.float32).reshape(pixelBufferShape)
                self.height, self.width, self.depth = self._pixelBuffer.shape

        elif numArgs <= 3:
            # new image constructor
            depth = args[2] if (numArgs == 3) else 3
            self._pixelBuffer = np.zeros((args[1], args[0], depth), dtype=np.float32)
            self.height, self.width, self.depth = self._pixelBuffer.shape

        else:
            raise ValueError(f"Invalid call to Image. Expected 1-3 arguments got {len(args)} ({(args)})")    


    @property
    def bufferView(self):
        return self._pixelBuffer[0:self.height, 0:self.width, :]

    @property
    def pixels(self):
        return self._pixelBuffer[0:self.height, 0:self.width, :].astype(np.uint8)

    @property
    def pixelsRGB(self):
        return self._pixelBuffer[0:self.height, 0:self.width, ::-1].astype(np.uint8)
    

    def isVisible(self) -> bool:
        return (self._windowName is not None) and (cv2.getWindowProperty(self._windowName, cv2.WND_PROP_VISIBLE) == 1)

    def show(self, windowName:str) -> None:
        if self.isVisible():
            return
        
        self._windowName = windowName
        cv2.imshow(windowName, self.pixels)

    def blockUntilClosed(self) -> None:
        while True:
            # check is window is exited out of
            if not self.isVisible():
                self._windowName = None
                return

            # check if ESC is pressed
            key = cv2.waitKey(10)
            if key == 27:
                cv2.destroyWindow(self._windowName)
                return

    def save(self, path:str) -> None:
        cv2.imwrite(path, self.pixels)


    def getNeighbors(self, x:int, y:int) -> np.ndarray:
        """ 
            Returns an 3x3xd array of pixels centered around x, y where d is the color depth of the image (3 for BGR). 
            If the neighbor is outsize of bounds its pixel value is clamped to the value at x,y 
        """

        if x > 0 and y > 0 and x < self.width-1 and y < self.height-1:
            # return a view of the current buffer for speedup
            return self._pixelBuffer[y-1:y+2, x-1:x+2]


        # return a copy of the elements
        neighbors = np.empty((3,3,self.depth), dtype=np.float32)

        for ny in range(3):
            py = y + ny - 1

            # clamp py to be in bounds
            if py < 0 or py >= self.height:
                py = y

            for nx in range(3):
                px = x + nx - 1

                # clamp px to be in bounds
                if px < 0 or px >= self.width:
                    px = x

                neighbors[ny, nx] = self._pixelBuffer[py, px]

        return neighbors

    def normalize(self) -> Self:
        bufferView = self.bufferView
        minVal     = bufferView.min()
        maxVal     = bufferView.max()
        deltaVal   = maxVal - minVal

        if deltaVal == 0:
            # black image
            bufferView.fill(0)

        else:
            # normalize energy into 8 bit values
            bufferView
            return Image((255 / deltaVal) * (bufferView - minVal))

        return self
    
    def resized(self, width:int, height:int) -> "Image":
        return Image(cv2.resize(src = self.bufferView, dsize = (width, height)))