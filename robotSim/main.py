import py5

from colour import Color

class Limb():
    x1:float
    y1:float
    x2:float
    y2:float

    # cached length
    length:float

    armColor  :Color = Color("darkBlue")
    jointColor:Color = Color("DarkGoldenRod")

    minX1:float = float('-inf')
    maxX1:float = float('inf')

    minY1:float = float('-inf')
    maxY1:float = float('inf')

    def __init__(self, x:float, y:float, length:float, angle:float):
        self.x1 = x
        self.y1 = y

        # note: subtract sin to account for py5 coordinates growing down
        self.x2 = self.x1 + py5.cos(angle) * length
        self.y2 = self.y1 - py5.sin(angle) * length

        self.length = length

    def moveJ2(self, targetX:float, targetY:float) -> None:


        j1TDirection = py5.Py5Vector2D(targetX - self.x1, targetY - self.y1).normalize()

        self.x2 = targetX
        self.y2 = targetY        

        v = j1TDirection * self.length

        self.x1 = self.x2 - v.x
        self.y1 = self.y2 - v.y

    def moveJ1(self, targetX:float, targetY:float) -> None:

        constrainedX = py5.constrain(targetX, self.minX1, self.maxX1)
        constrainedY = py5.constrain(targetY, self.minY1, self.maxY1)

        j2TDirection = py5.Py5Vector2D(constrainedX - self.x2, constrainedY - self.y2).normalize()

        self.x1 = constrainedX
        self.y1 = constrainedY        

        v = j2TDirection * self.length

        self.x2 = self.x1 - v.x
        self.y2 = self.y1 - v.y        


class RobotSim(py5.Sketch):
    windowWidth:int  = 500
    windowHeight:int = 500

    backgroundColor:Color = Color("SkyBlue")

    numLimbs     :int   = 10
    limbLength   :float = 30
    limbThickness:float = 10

    maxFabrikIterations:int = 10
    
    limbs:list[Limb]

    def __init__(self):
        super().__init__()

        self.limbs = []
        x = self.windowWidth/2
        y = self.windowHeight - self.limbThickness

        angle = 0
        angleStride = py5.radians(15)
        for i in range(self.numLimbs):
            limb = Limb(x, y, self.limbLength, angle)

            if i == 0:
                limb.minX1 = x
                limb.maxX1 = x
                limb.minY1 = y
                limb.maxY1 = y

            # elif i == 1:
            #     limb.minY1 = y - 10


            self.limbs.append(limb)

            x = limb.x2
            y = limb.y2

            angle+= angleStride


    def settings(self) -> None:
        self.size(self.windowWidth, self.windowHeight)

    def setup(self) -> None:
        self.window_title('RobotSim')

    def draw(self) -> None:
        # clear the screen
        self.background(self.backgroundColor)

        self.updateLimbs()

        self.drawLimbs()

    def drawLimbs(self) -> None:
        for limb in self.limbs:
            self.stroke(limb.armColor)
            self.stroke_weight(self.limbThickness)
            self.line(limb.x1, limb.y1, limb.x2, limb.y2)

            self.stroke(limb.jointColor)
            self.point(limb.x1, limb.y1)
            self.point(limb.x2, limb.y2)

    def key_released(self) -> None:
        if self.key == "1":
            newLimb = Limb(0, 0, 15, 0)
            newLimb.armColor = Color("orange")
            self.limbs.insert(1, newLimb)


    def updateLimbs(self) -> None:
        if not self.is_mouse_pressed:
            return

        targetX = self.mouse_x
        targetY = self.mouse_y
        
        # solve inverse kinematics using FABRIK algorithm
        for i in range(self.maxFabrikIterations):

            for limb in reversed(self.limbs):
                limb.moveJ2(targetX, targetY)
                
                targetX = limb.x1
                targetY = limb.y1

            for limb in self.limbs:
                limb.moveJ1(targetX, targetY)            
                
                targetX = limb.x2
                targetY = limb.y2          

            # TODO: break out if the limbs haven't moved much



def main() -> None:
    robotSim = RobotSim()
    robotSim.run_sketch()


if __name__ == "__main__":
    main()
