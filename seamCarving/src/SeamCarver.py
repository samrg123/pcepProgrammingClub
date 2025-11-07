import numpy as np
from src.Image import Image

class SeamCarver:

    def pixelEnergy(self, image:Image, x:int, y:int) -> float:
        # computes the gradient magnitude 'sqrt((d/dx)^2 + (d/dy)^2)' of the pixel at x,y
        
        # Note: neighbors[1,1] == pixels[y,x]
        neighbors = image.getNeighbors(x,y)

        deltaX:np.ndarray = neighbors[1,2] - neighbors[1,0]
        deltaY:np.ndarray = neighbors[2,1] - neighbors[0,1]

        gradX2 = deltaX.dot(deltaX)
        gradY2 = deltaY.dot(deltaY)

        return (gradX2 + gradY2)**.5
    
    def getMinTopSeamCostX(self, image:Image, seamCostBuffer:np.ndarray, width:int, x:int, y:int, useForwardEnergy:bool) -> tuple[float, int]:
        """
            Returns (topCost, topX) where topCost is the minium seam cost to get to (x,y) from (topX, y-1) 
            If useForwardEnergy == True, the the algorithm accounts for the addition energy gained from removing the seam
            For details see: https://web.archive.org/web/20250506201637/https://faculty.runi.ac.il/arik/scweb/vidret/vidret.pdf
            Requires '0 <= x < width' and '1 <= y < height'
        """
        topY = y - 1
        topVal = image._pixelBuffer[topY, x] if useForwardEnergy else None

        # initialize to topCost (traveling straight down)
        topX = x
        minCost = seamCostBuffer[topY, x]
        
        # check if its cheaper from travel from the left
        if x > 0:
            leftX = x-1
            leftCost = seamCostBuffer[topY, leftX]

            if useForwardEnergy:
                leftVal = image._pixelBuffer[y, leftX]
                leftTravelCost:np.ndarray = topVal - leftVal
                leftCost+= leftTravelCost.dot(leftTravelCost)**.5

            if leftCost < minCost:
                topX = leftX
                minCost = leftCost
        
        elif useForwardEnergy:
            # clamp edge to our value
            leftVal = image._pixelBuffer[y, x]

        # check if its cheaper to travel from the right
        rightX = x+1
        if rightX < width:            
            rightCost = seamCostBuffer[topY, rightX]

            if useForwardEnergy:
                rightVal = image._pixelBuffer[y, rightX]
                rightTravelCost:np.ndarray = topVal - rightVal
                rightCost+= rightTravelCost.dot(rightTravelCost)**.5

            if rightCost < minCost:
                topX = rightX
                minCost = rightCost

        elif useForwardEnergy:
            # clamp edge to our value
            rightVal = image._pixelBuffer[y, x]

        if useForwardEnergy:
            # Add the forward cost to travel down a row which applies to all seam directions
            downTravelCost:np.ndarray = rightVal - leftVal
            minCost+= downTravelCost.dot(downTravelCost)**.5

        return minCost, topX

    def computeSeamCost(self, image:Image, seamCostBuffer:np.array, useForwardEnergy:bool):
        # initialize the first seam cost row to its pixel energy
        for x in range(image.width):
            seamCostBuffer[0, x] = self.pixelEnergy(image, x, 0)

        # walk down the rest of the image summing up the minimum energy paths to form seams
        for y in range(1, image.height):
            for x in range(image.width):
                minTopCost, _ = self.getMinTopSeamCostX(image, seamCostBuffer, image.width, x, y, useForwardEnergy)
                seamCostBuffer[y, x] = minTopCost + self.pixelEnergy(image, x, y)        


    def energyImage(self, image:Image) -> Image:
        energyMatrix = np.array(
            object = [[self.pixelEnergy(image, x, y) for x in range(image.width)] for y in range(image.height)],
            dtype  = np.float32, 
        )

        return Image(energyMatrix).normalize()

    def seamCostImage(self, image:Image, useForwardEnergy:bool = False) -> Image:
        costBuffer = np.empty((image.height, image.width), dtype=np.float32)
        self.computeSeamCost(image, costBuffer, useForwardEnergy)
        
        return Image(costBuffer).normalize()

    def carveImage(self, image:Image, newWidth:int, useForwardEnergy:bool = False) -> tuple[Image, np.ndarray]:
        """
            Returns a carved image to match the newWidth and an array of all the carved columns.
        """
        numCarvedColumns = image.width - newWidth

        carvedImage    = Image(image)
        carvedColumns  = np.empty(shape=(numCarvedColumns, image.height), dtype=np.int32)
        seamCostBuffer = np.empty((image.height, image.width), dtype=np.float32)
        
        # carve away one column at a time until the newWidth is reached
        for i in range(numCarvedColumns):

            # compute the seam cost for the image
            self.computeSeamCost(carvedImage, seamCostBuffer, useForwardEnergy)
        
            # start at bottom of image and walking up removing the minimum energy column  
            carveX = seamCostBuffer[-1, 0:carvedImage.width].argmin()
            carvedColumn = carvedColumns[i]
            for y in reversed(range(carvedImage.height)):

                # shift over the pixels at carveX
                carvedImage._pixelBuffer[y, carveX:(carvedImage.width-1)] = carvedImage._pixelBuffer[y, (carveX+1):carvedImage.width]
                carvedColumn[y] = carveX

                # walk up the seam
                if y > 0:
                    _, carveX = self.getMinTopSeamCostX(carvedImage, seamCostBuffer, carvedImage.width, carveX, y, useForwardEnergy)

            carvedImage.width-= 1

        return carvedImage, carvedColumns

    def seamImage(self, carvedImage:Image, carvedColumns:np.ndarray, seamColor:np.ndarray|None = None) -> Image:

        if seamColor is None:
            seamColor = self.getOptimalSeamColor(carvedImage)

        numCarvedColumns = carvedColumns.shape[0]
        
        imageWidth = carvedImage.width + numCarvedColumns
        imageHeight = carvedImage.height

        seamImage = Image(imageWidth, imageHeight)
        
        # copy over carved image into seamImage
        seamImage._pixelBuffer[:,0:carvedImage.width] = carvedImage._pixelBuffer[:,0:carvedImage.width]
        seamImage.width = carvedImage.width

        # 'uncarve' the image in reverse order
        for i in reversed(range(numCarvedColumns)):
            carvedColumn = carvedColumns[i]

            for y, carvedX in enumerate(carvedColumn):
                
                # shift over the row and mark the seam
                seamImage._pixelBuffer[y, (carvedX+1):(seamImage.width+1)] = seamImage._pixelBuffer[y, carvedX:seamImage.width]
                seamImage._pixelBuffer[y, carvedX] = seamColor

            seamImage.width+= 1

        return seamImage

    def getOptimalSeamColor(self, image:Image) -> np.ndarray:
        # compute the color that is optimally far away from all other colors in the image

        medRGB:np.ndarray = np.median(image.pixels, axis=(0,1))
        darkestChannel = medRGB.argmin()
        
        if medRGB[darkestChannel] <= 128:
            # median pixel is dark 
            # turn on the darkest channel
            seamColor = np.zeros_like(medRGB)
            seamColor[darkestChannel] = 255
        else:
            # median pixel is bright         
            # turn off the brightest channel
            brightestChannel = medRGB.argmax()
            seamColor = np.full_like(medRGB, 255)
            seamColor[brightestChannel] = 0

        return seamColor