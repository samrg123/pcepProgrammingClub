import numpy as np
from src.Image import Image

class SeamCarver:

    def pixelEnergy(self, image:Image, x:int, y:int) -> float:
        # computes the squared gradient magnitude ((d/dx)^2 + (d/dy)^2) of the pixel at x,y

        # Note: neighbors[1,1] == pixels[y,x]
        neighbors = image.getNeighbors(x,y)

        deltaX:np.ndarray = neighbors[1,2] - neighbors[1,0]
        deltaY:np.ndarray = neighbors[2,1] - neighbors[0,1]

        gradX2 = deltaX.dot(deltaX)
        gradY2 = deltaY.dot(deltaY)     

        return gradX2 + gradY2

    def getMinEnergyX(self, seamEnergyBuffer:np.ndarray, width:int, x:int, y:int) -> tuple[float, int]:
        minX = x
        minEnergy = seamEnergyBuffer[y, x]
        
        # check if its cheaper to the left
        if x > 0:
            leftX = x-1
            leftEnergy = seamEnergyBuffer[y, leftX]

            if leftEnergy < minEnergy:
                minX = leftX
                minEnergy = leftEnergy

        # check if its cheaper to the right
        rightX = x+1
        if rightX < width:
            rightEnergy = seamEnergyBuffer[y, rightX]

            if rightEnergy < minEnergy:
                minX = rightX
                minEnergy = rightEnergy

        return minEnergy, minX

    def energyImage(self, image:Image) -> Image:
        #compute the energy matrix 
        energyMatrix = np.empty((image.height, image.width))

        minEnergy = np.inf
        maxEnergy = -np.inf
        for y in range(image.height):
            for x in range(image.width):

                energy = self.pixelEnergy(image, x, y)

                if energy < minEnergy:
                    minEnergy = energy
                
                if energy > maxEnergy:
                    maxEnergy = energy

                energyMatrix[y,x] = energy

        # normalize energy into 8 bit values
        energyRange = maxEnergy - minEnergy
        if energyRange != 0:
            return Image((255 / energyRange) * (energyMatrix - minEnergy))

        # return blank image
        return Image(image.width, image.height, 1)


    def carveImage(self, image:Image, newWidth:int) -> tuple[Image, np.ndarray]:
        """
            Returns a carved image to match the newWidth and an array of all the carved columns.
        """
        numCarvedColumns = image.width - newWidth

        carvedImage      = Image(image)
        carvedColumns    = np.empty(shape=(numCarvedColumns, image.height), dtype=np.uint32)
        seamEnergyBuffer = np.empty((image.height, image.width))
        
        # carve away one column at a time until the newWidth is reached
        for i in range(numCarvedColumns):

            # compute the seam energy for the image
            # initialize the first seam energy row to its pixel energy
            for x in range(carvedImage.width):
                seamEnergyBuffer[0, x] = self.pixelEnergy(carvedImage, x, 0)

            # walk down the rest of the image summing up the minimum energy paths to form seams
            for y in range(1, carvedImage.height):            
                topY = y - 1

                for x in range(carvedImage.width):
                    minTopEnergy, _ = self.getMinEnergyX(seamEnergyBuffer, carvedImage.width, x, topY)
                    seamEnergyBuffer[y, x] = minTopEnergy + self.pixelEnergy(carvedImage, x, y)


            # start at bottom of image and walking up removing the minimum energy column  
            carveX = seamEnergyBuffer[-1, 0:carvedImage.width].argmin()
            carvedColumn = carvedColumns[i]
            for y in reversed(range(carvedImage.height)):

                # shift over the pixels at carveX
                carvedImage._pixelBuffer[y, carveX:(carvedImage.width-1)] = carvedImage._pixelBuffer[y, (carveX+1):carvedImage.width]
                carvedColumn[y] = carveX

                # walk up the seam
                if y > 0:
                    _, carveX = self.getMinEnergyX(seamEnergyBuffer, carvedImage.width, carveX, y-1)

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

        medRGB:np.ndarray = np.median(image._pixelBuffer, axis=(0,1))
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