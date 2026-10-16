import py5
import debugpy

from colour import Color
from dataclasses import dataclass

@dataclass
class Joint():
    x    :float = 0
    y    :float = 0
    angle:float = 0

    # constraints
    minX:float = float('-inf')
    minY:float = float('-inf')
    maxX:float = float('inf')
    maxY:float = float('inf')

    minAngle = 0
    maxAngle = py5.TWO_PI

class Limb():
    armColor  :Color = Color("darkblue")
    jointColor:Color = Color("darkred")
    
    thickness:float = 1
    length   :float = 5
    joints   :tuple[Joint, Joint]

    def __init__(self, joint1:Joint, joint2:Joint):
        self.joints = (joint1, joint2)

    def moveJoint1(self, targetX:float, targetY:float) -> None:
        joint1, joint2 = self.joints

        # constrain target to joint1 limits
        targetX = py5.constrain(targetX, joint1.minX, joint1.maxX)
        targetY = py5.constrain(targetY, joint1.minY, joint1.maxY)

        tDirection = py5.Py5Vector2D(targetX - joint2.x, targetY - joint2.y).normalize()

        j1Pos = py5.Py5Vector2D(targetX, targetY)
        j2Pos = j1Pos - (tDirection * self.length)

        joint1.x = j1Pos.x
        joint1.y = j1Pos.y

        joint2.x = j2Pos.x
        joint2.y = j2Pos.y

    def moveJoint2(self, targetX:float, targetY:float) -> None:
        joint1, joint2 = self.joints

        # constrain target to joint2 limits
        targetX = py5.constrain(targetX, joint2.minX, joint2.maxX)
        targetY = py5.constrain(targetY, joint2.minY, joint2.maxY)

        tDirection = py5.Py5Vector2D(targetX - joint1.x, targetY - joint1.y).normalize()

        j2Pos = py5.Py5Vector2D(targetX, targetY)
        j1Pos = j2Pos - (tDirection * self.length)

        joint1.x = j1Pos.x
        joint1.y = j1Pos.y

        joint2.x = j2Pos.x
        joint2.y = j2Pos.y

        
class RobotSim(py5.Sketch):
    limbLength   :float = 50
    limbThickness:float = 15

    limbs:list[Limb] 

    viewportWidth  :int = 500
    viewportHeight :int = 500
    backgroundColor:Color = Color('darkgray')
    
    lastDrawMs :int = 0

    def __init__(self):
        super().__init__()

        self.limbs = []

        angle = 0
        angleStride = py5.radians(20)
        baseX, baseY = (self.viewportWidth/2 , self.viewportHeight - self.limbThickness/2)
        numLimbs = 5
        for i in range(numLimbs):

            newX = baseX + self.cos(angle) * self.limbLength
            newY = baseY - self.sin(angle) * self.limbLength
            newAngle = (angle + angleStride) % py5.TWO_PI
            
            joint1 = Joint(baseX, baseY, angle)
            joint2 = Joint(newX, newY, newAngle)

            if i == 0:
                # anchor first joint to the ground
                joint1.minX = baseX
                joint1.maxX = baseX

                joint1.minY = baseY
                joint1.maxY = baseY

            newLimb = Limb(joint1, joint2)
            newLimb.length = self.limbLength

            newLimb.thickness = self.limbThickness
            
            self.limbs.append(newLimb)

            baseX = newX
            baseY = newY
            angle = newAngle
            
            
    def enterPy5Thread(self) -> None:
        # attach the debugger to threads created from py5
        if debugpy.is_client_connected():
            debugpy.debug_this_thread()

    def settings(self) -> None:
        self.enterPy5Thread()

        # initialize the window size
        width  = self.viewportWidth
        height = self.viewportHeight

        self.size(width, height)

    def setup(self) -> None:
        self.enterPy5Thread()

        self.window_title("RobotSim")

        # setup text
        self.text_font(self.create_font("consolas", 12))
        
        # setup drawing settings
        self.color_mode(self.RGB)


    def draw(self) -> None:
        self.enterPy5Thread()

        # compute deltaT
        drawMs = py5.millis()
        deltaT = 1e-3 * (drawMs - self.lastDrawMs)
    
        # clear the screen
        self.background(self.backgroundColor)

        # # update inputs
        # self.processInput()

        # update and draw limbs
        self.updateLimbs(deltaT)
        self.drawLimbs()

        self.lastDrawMs = drawMs


    def updateLimbs(self, deltaT:float) -> None:
        if not self.is_mouse_pressed:
            return

        # using fabrik algorithm

        numLimbs = len(self.limbs)

        # backward pass
        targetX = self.mouse_x
        targetY = self.mouse_y
        for i in reversed(range(numLimbs)):
            limb = self.limbs[i]

            limb.moveJoint2(targetX, targetY)

            joint1 = limb.joints[0] 
            targetX = joint1.x
            targetY = joint1.y

        # forward pass
        for i in range(numLimbs):
            limb   = self.limbs[i]
            joint2 = limb.joints[1]

            limb.moveJoint1(targetX, targetY)

            targetX = joint2.x
            targetY = joint2.y


    def drawLimbs(self) -> None:
        for limb in self.limbs:
            joint1, joint2 = limb.joints 

            self.stroke_weight(limb.thickness)
            
            # draw arm
            self.stroke(limb.armColor)
            self.line(joint1.x, joint1.y, joint2.x, joint2.y)

            # draw joint's
            self.stroke(limb.jointColor)
            self.point(joint1.x, joint1.y)
            self.point(joint2.x, joint2.y)


def main() -> None:
    robotSim = RobotSim()
    robotSim.run_sketch()
    


if __name__ == "__main__":
    main()