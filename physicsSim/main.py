from dataclasses import dataclass, field
from typing import Final, Iterable, Self, SupportsFloat, overload
import numpy as np
from py5 import Sketch
import debugpy

class Vec2():
    _array:np.ndarray[np.float32]

    @overload
    def __init__(self, x:SupportsFloat = 0, y:SupportsFloat = 0, /): ...

    @overload
    def __init__(self, array:Iterable[SupportsFloat], /): ...    

    def __init__(self, *args):
        match len(args):
            case 1:
                array = args[0]
                arrayLength = len(array)
                if arrayLength != 2:
                    raise Exception(f"Invalid call to Vec2. Expected array of length 2 got length {arrayLength} ({(array)})")
                
                self._array = np.array(array, dtype=np.float32)

            case 2:
                self._array = np.array(args, dtype=np.float32)                

            case _:
                raise Exception(f"Invalid call to Vec2. Expected 1 or 2 arguments got {len(args)} ({(args)})")
    
    @classmethod
    def random(cls, minX:SupportsFloat, maxX:SupportsFloat, minY:SupportsFloat, maxY:SupportsFloat) -> "Vec2":
        randValues = np.random.rand(2)
        randX = randValues[0]*(maxX - minX) + minX
        randY = randValues[1]*(maxY - minY) + minY

        return Vec2(randX, randY)

    @classmethod
    def zero(cls): return Vec2(0, 0)
    
    @classmethod
    def one(self): return Vec2(1, 1)

    @classmethod        
    def up(cls): return Vec2(0, -1)

    @classmethod
    def down(cls): return Vec2(0, 1)

    @classmethod
    def left(cls): return Vec2(-1, 0)

    @classmethod
    def right(cls): return Vec2(1, 0)

    @property
    def x(self) -> np.float32: 
        return self._array[0]
    
    @x.setter
    def x(self, value:SupportsFloat) -> None:
        self._array[0] = value

    @property
    def y(self) -> np.float32:
        return self._array[1]

    @y.setter
    def y(self, value:SupportsFloat) -> None:
        self._array[1] = value
    
    @property
    def normSquared(self) -> np.float32:
        return np.square(self._array).sum()
    
    @property
    def norm(self) -> np.float32:
        return np.sqrt(np.square(self._array).sum())

    @property
    def direction(self) -> "Vec2":
        normSquared = np.square(self._array).sum()
        if normSquared == 0:
            return Vec2(0, 0) 

        return Vec2(self._array / np.sqrt(normSquared))

    @property
    def scaledNormal(self) -> "Vec2":
        return Vec2(-self._array[1], self._array[0])

    @property
    def normal(self) -> "Vec2":
        normSquared = np.square(self._array).sum()
        if normSquared == 0:
            return Vec2(0, 0) 

        direction = self._array / np.sqrt(normSquared)
        return Vec2(-direction[1], direction[0])
    

    def dot(self, v2:"Vec2") -> np.float32:
        return (self._array * v2._array).sum()

    def project(self, v2:"Vec2") -> "Vec2":
        normSquared = np.square(self._array).sum()
        if normSquared == 0:
            return Vec2(0, 0)
        
        return Vec2(self._array * (self._array * v2._array).sum()/normSquared)
    
    def orthogonalProject(self, v2:"Vec2") -> "Vec2":
        normSquared = np.square(self._array).sum()
        if normSquared == 0:
            return Vec2(0, 0)

        return Vec2(v2 - self._array * (self._array * v2._array).sum()/normSquared)


    def __repr__(self) -> str:
        return f"Vec2(x={self._array[0]}, y={self._array[1]})"

    def __getitem__(self, index:int) -> np.float32:
        return self._array[index]

    def __setitem__(self, index:int, value:SupportsFloat) -> None:
        self._array[index] = value

    def __abs__(self) -> "Vec2":
        return Vec2(self._array.abs())

    def __neg__(self) -> "Vec2":
        return Vec2(-self._array)    

    def sqrt(self) -> "Vec2":
        np.sqrt(self._array)
        return self
    
    def __eq__(self, other:"Vec2") -> bool:
        return self._array[0] == other._array[0] and self._array[1] == other._array[1]

    def __ne__(self, other:"Vec2") -> bool:
        return self._array[0] != other._array[0] and self._array[1] != other._array[1]

    def __iadd__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        self._array+= other._array if isinstance(other, Vec2) else other
        return self
    
    def __isub__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        self._array-= other._array if isinstance(other, Vec2) else other
        return self

    def __imul__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        self._array*= other._array if isinstance(other, Vec2) else other
        return self
    
    def __itruediv__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        self._array/= other._array if isinstance(other, Vec2) else other
        return self
    
    def __ifloordiv__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        self._array//= other._array if isinstance(other, Vec2) else other
        return self


    def __add__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        return Vec2(self._array + other._array) if isinstance(other, Vec2) else Vec2(self._array + other)
    
    def __sub__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        return Vec2(self._array - other._array) if isinstance(other, Vec2) else Vec2(self._array - other)      

    def __mul__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        return Vec2(self._array * other._array) if isinstance(other, Vec2) else Vec2(self._array * other)
    
    def __truediv__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        return Vec2(self._array / other._array) if isinstance(other, Vec2) else Vec2(self._array / other)
    
    def __floordiv__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        return Vec2(self._array // other._array) if isinstance(other, Vec2) else Vec2(self._array // other)    


    def __radd__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        return Vec2(other._array + self._array) if isinstance(other, Vec2) else Vec2(other + self._array)
    
    def __rsub__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        return Vec2(other._array - self._array) if isinstance(other, Vec2) else Vec2(other - self._array)      

    def __rmul__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        return Vec2(other._array * self._array) if isinstance(other, Vec2) else Vec2(other * self._array)
    
    def __rtruediv__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        return Vec2(other._array / self._array) if isinstance(other, Vec2) else Vec2(other / self._array)
    
    def __rfloordiv__(self, other:"Vec2|SupportsFloat") -> "Vec2":
        return Vec2(other._array // self._array) if isinstance(other, Vec2) else Vec2(other // self._array)

    

class Rectangle:
    origin :Vec2
    size   :Vec2

    def __init__(self, originX:np.float32 = 0, originY:np.float32 = 0, sizeX:np.float32 = 0, sizeY:np.float32 = 0):
        self.origin = Vec2(originX, originY)
        self.size = Vec2(sizeX, sizeY)

    @property
    def area(self) -> np.float64: 
        return self.size.x * self.size.y
    
    @property
    def x1(self) -> np.float32:
        return self.origin.x

    @x1.setter
    def x1(self, value:SupportsFloat) -> None: 
        self.origin.x = value

    @property
    def x2(self) -> np.float32: 
        return self.origin.x + self.size.x

    @x2.setter
    def x2(self, value:SupportsFloat) -> None: 
        self.size.x = value - self.origin.x
    
    @property
    def y1(self) -> np.float32: 
        return self.origin.y

    @y1.setter
    def y1(self, value:SupportsFloat) -> None: 
        self.origin.y = value

    @property
    def y2(self) -> np.float32: 
        return self.origin.y + self.size.y

    @y2.setter
    def y2(self, value:SupportsFloat) -> None: 
        self.size.y = value - self.origin.y             


class Line:
    _v1        :Vec2
    _v2        :Vec2
    _length    :np.float32
    _normal    :Vec2
    _direction :Vec2

    def __init__(self, v1:Vec2, v2:Vec2):
        self._v1        = v1
        self._v2        = v2
        self._normal    = Vec2(0, 0)
        self._direction = Vec2(0, 0)

        self._updateState()

    def _updateState(self) -> None:
        scaledDirection = self._v2 - self._v1
        lengthSquared = scaledDirection.normSquared

        if lengthSquared == 0:
            self._length = 0
            self._normal*= 0
            self._direction*= 0

        else:
            self._length  = np.sqrt(lengthSquared)
            inverseLength = 1 / self._length

            self._direction = scaledDirection * inverseLength
            self._normal    = scaledDirection.scaledNormal * inverseLength 


    @property
    def v1(self) -> "Vec2": 
        return self._v1
    
    @v1.setter
    def v1(self, v:Vec2) -> None: 
        self._v1 = v
        self._updateState()    

    @property
    def v2(self) -> "Vec2": 
        return self._v2    

    @v2.setter
    def v2(self, v:Vec2) -> None: 
        self._v2 = v
        self._updateState()

    @property
    def length(self) -> Vec2: 
        return self._length    

    @property
    def normal(self) -> Vec2: 
        return self._normal

    @property
    def direction(self) -> Vec2: 
        return self._direction


class ARGB(int):

    @overload
    def __new__(cls, argb:np.uint32, /) -> Self: ...

    @overload
    def __new__(cls, r:np.uint8, g:np.uint8, b:np.uint8, /) -> Self: ...     
    
    @overload
    def __new__(cls, r:np.uint8, g:np.uint8, b:np.uint8, a:np.uint8, /) -> Self: ...     

    def __new__(cls, *args) -> Self:
        match len(args):
            case 1:
                argb = args[0]
            case 3:
                argb = 0xFF000000 | (args[0] << 16) | (args[1] << 8) | args[2]
            case 4:
                argb = (args[3] << 24) | (args[0] << 16) | (args[1] << 8) | args[2]

            case _:
                raise Exception(f"Invalid call to ARGB. Expected 1,3, or 4 arguments got {len(args)} ({(args)})")
        
        return super().__new__(cls, argb)

    @property
    def a(self) -> np.uint8:
        return (self >> 24) & 0xFF
    
    @property
    def r(self) -> np.uint8:
        return (self >> 16) & 0xFF

    @property
    def g(self) -> np.uint8:
        return (self >> 8) & 0xFF

    @property
    def b(self) -> np.uint8:
        return self & 0xFF

    def __repr__(self):
        return f"Color(a={self.a}, r={self.r}, g={self.g}, b={self.b}, [{self:08x}])"

@dataclass(frozen=True)
class Colors:
    # CSS4 Colors
    aliceblue           :Final[ARGB] = ARGB(0xFFF0F8FF)
    antiquewhite        :Final[ARGB] = ARGB(0xFFFAEBD7)
    aqua                :Final[ARGB] = ARGB(0xFF00FFFF)
    aquamarine          :Final[ARGB] = ARGB(0xFF7FFFD4)
    azure               :Final[ARGB] = ARGB(0xFFF0FFFF)
    beige               :Final[ARGB] = ARGB(0xFFF5F5DC)
    bisque              :Final[ARGB] = ARGB(0xFFFFE4C4)
    black               :Final[ARGB] = ARGB(0xFF000000)
    blanchedalmond      :Final[ARGB] = ARGB(0xFFFFEBCD)
    blue                :Final[ARGB] = ARGB(0xFF0000FF)
    blueviolet          :Final[ARGB] = ARGB(0xFF8A2BE2)
    brown               :Final[ARGB] = ARGB(0xFFA52A2A)
    burlywood           :Final[ARGB] = ARGB(0xFFDEB887)
    cadetblue           :Final[ARGB] = ARGB(0xFF5F9EA0)
    chartreuse          :Final[ARGB] = ARGB(0xFF7FFF00)
    chocolate           :Final[ARGB] = ARGB(0xFFD2691E)
    coral               :Final[ARGB] = ARGB(0xFFFF7F50)
    cornflowerblue      :Final[ARGB] = ARGB(0xFF6495ED)
    cornsilk            :Final[ARGB] = ARGB(0xFFFFF8DC)
    crimson             :Final[ARGB] = ARGB(0xFFDC143C)
    cyan                :Final[ARGB] = ARGB(0xFF00FFFF)
    darkblue            :Final[ARGB] = ARGB(0xFF00008B)
    darkcyan            :Final[ARGB] = ARGB(0xFF008B8B)
    darkgoldenrod       :Final[ARGB] = ARGB(0xFFB8860B)
    darkgray            :Final[ARGB] = ARGB(0xFFA9A9A9)
    darkgreen           :Final[ARGB] = ARGB(0xFF006400)
    darkgrey            :Final[ARGB] = ARGB(0xFFA9A9A9)
    darkkhaki           :Final[ARGB] = ARGB(0xFFBDB76B)
    darkmagenta         :Final[ARGB] = ARGB(0xFF8B008B)
    darkolivegreen      :Final[ARGB] = ARGB(0xFF556B2F)
    darkorange          :Final[ARGB] = ARGB(0xFFFF8C00)
    darkorchid          :Final[ARGB] = ARGB(0xFF9932CC)
    darkred             :Final[ARGB] = ARGB(0xFF8B0000)
    darksalmon          :Final[ARGB] = ARGB(0xFFE9967A)
    darkseagreen        :Final[ARGB] = ARGB(0xFF8FBC8F)
    darkslateblue       :Final[ARGB] = ARGB(0xFF483D8B)
    darkslategray       :Final[ARGB] = ARGB(0xFF2F4F4F)
    darkslategrey       :Final[ARGB] = ARGB(0xFF2F4F4F)
    darkturquoise       :Final[ARGB] = ARGB(0xFF00CED1)
    darkviolet          :Final[ARGB] = ARGB(0xFF9400D3)
    deeppink            :Final[ARGB] = ARGB(0xFFFF1493)
    deepskyblue         :Final[ARGB] = ARGB(0xFF00BFFF)
    dimgray             :Final[ARGB] = ARGB(0xFF696969)
    dimgrey             :Final[ARGB] = ARGB(0xFF696969)
    dodgerblue          :Final[ARGB] = ARGB(0xFF1E90FF)
    firebrick           :Final[ARGB] = ARGB(0xFFB22222)
    floralwhite         :Final[ARGB] = ARGB(0xFFFFFAF0)
    forestgreen         :Final[ARGB] = ARGB(0xFF228B22)
    fuchsia             :Final[ARGB] = ARGB(0xFFFF00FF)
    gainsboro           :Final[ARGB] = ARGB(0xFFDCDCDC)
    ghostwhite          :Final[ARGB] = ARGB(0xFFF8F8FF)
    gold                :Final[ARGB] = ARGB(0xFFFFD700)
    goldenrod           :Final[ARGB] = ARGB(0xFFDAA520)
    gray                :Final[ARGB] = ARGB(0xFF808080)
    green               :Final[ARGB] = ARGB(0xFF008000)
    greenyellow         :Final[ARGB] = ARGB(0xFFADFF2F)
    grey                :Final[ARGB] = ARGB(0xFF808080)
    honeydew            :Final[ARGB] = ARGB(0xFFF0FFF0)
    hotpink             :Final[ARGB] = ARGB(0xFFFF69B4)
    indianred           :Final[ARGB] = ARGB(0xFFCD5C5C)
    indigo              :Final[ARGB] = ARGB(0xFF4B0082)
    ivory               :Final[ARGB] = ARGB(0xFFFFFFF0)
    khaki               :Final[ARGB] = ARGB(0xFFF0E68C)
    lavender            :Final[ARGB] = ARGB(0xFFE6E6FA)
    lavenderblush       :Final[ARGB] = ARGB(0xFFFFF0F5)
    lawngreen           :Final[ARGB] = ARGB(0xFF7CFC00)
    lemonchiffon        :Final[ARGB] = ARGB(0xFFFFFACD)
    lightblue           :Final[ARGB] = ARGB(0xFFADD8E6)
    lightcoral          :Final[ARGB] = ARGB(0xFFF08080)
    lightcyan           :Final[ARGB] = ARGB(0xFFE0FFFF)
    lightgoldenrodyellow:Final[ARGB] = ARGB(0xFFFAFAD2)
    lightgray           :Final[ARGB] = ARGB(0xFFD3D3D3)
    lightgreen          :Final[ARGB] = ARGB(0xFF90EE90)
    lightgrey           :Final[ARGB] = ARGB(0xFFD3D3D3)
    lightpink           :Final[ARGB] = ARGB(0xFFFFB6C1)
    lightsalmon         :Final[ARGB] = ARGB(0xFFFFA07A)
    lightseagreen       :Final[ARGB] = ARGB(0xFF20B2AA)
    lightskyblue        :Final[ARGB] = ARGB(0xFF87CEFA)
    lightslategray      :Final[ARGB] = ARGB(0xFF778899)
    lightslategrey      :Final[ARGB] = ARGB(0xFF778899)
    lightsteelblue      :Final[ARGB] = ARGB(0xFFB0C4DE)
    lightyellow         :Final[ARGB] = ARGB(0xFFFFFFE0)
    lime                :Final[ARGB] = ARGB(0xFF00FF00)
    limegreen           :Final[ARGB] = ARGB(0xFF32CD32)
    linen               :Final[ARGB] = ARGB(0xFFFAF0E6)
    magenta             :Final[ARGB] = ARGB(0xFFFF00FF)
    maroon              :Final[ARGB] = ARGB(0xFF800000)
    mediumaquamarine    :Final[ARGB] = ARGB(0xFF66CDAA)
    mediumblue          :Final[ARGB] = ARGB(0xFF0000CD)
    mediumorchid        :Final[ARGB] = ARGB(0xFFBA55D3)
    mediumpurple        :Final[ARGB] = ARGB(0xFF9370DB)
    mediumseagreen      :Final[ARGB] = ARGB(0xFF3CB371)
    mediumslateblue     :Final[ARGB] = ARGB(0xFF7B68EE)
    mediumspringgreen   :Final[ARGB] = ARGB(0xFF00FA9A)
    mediumturquoise     :Final[ARGB] = ARGB(0xFF48D1CC)
    mediumvioletred     :Final[ARGB] = ARGB(0xFFC71585)
    midnightblue        :Final[ARGB] = ARGB(0xFF191970)
    mintcream           :Final[ARGB] = ARGB(0xFFF5FFFA)
    mistyrose           :Final[ARGB] = ARGB(0xFFFFE4E1)
    moccasin            :Final[ARGB] = ARGB(0xFFFFE4B5)
    navajowhite         :Final[ARGB] = ARGB(0xFFFFDEAD)
    navy                :Final[ARGB] = ARGB(0xFF000080)
    oldlace             :Final[ARGB] = ARGB(0xFFFDF5E6)
    olive               :Final[ARGB] = ARGB(0xFF808000)
    olivedrab           :Final[ARGB] = ARGB(0xFF6B8E23)
    orange              :Final[ARGB] = ARGB(0xFFFFA500)
    orangered           :Final[ARGB] = ARGB(0xFFFF4500)
    orchid              :Final[ARGB] = ARGB(0xFFDA70D6)
    palegoldenrod       :Final[ARGB] = ARGB(0xFFEEE8AA)
    palegreen           :Final[ARGB] = ARGB(0xFF98FB98)
    paleturquoise       :Final[ARGB] = ARGB(0xFFAFEEEE)
    palevioletred       :Final[ARGB] = ARGB(0xFFDB7093)
    papayawhip          :Final[ARGB] = ARGB(0xFFFFEFD5)
    peachpuff           :Final[ARGB] = ARGB(0xFFFFDAB9)
    peru                :Final[ARGB] = ARGB(0xFFCD853F)
    pink                :Final[ARGB] = ARGB(0xFFFFC0CB)
    plum                :Final[ARGB] = ARGB(0xFFDDA0DD)
    powderblue          :Final[ARGB] = ARGB(0xFFB0E0E6)
    purple              :Final[ARGB] = ARGB(0xFF800080)
    rebeccapurple       :Final[ARGB] = ARGB(0xFF663399)
    red                 :Final[ARGB] = ARGB(0xFFFF0000)
    rosybrown           :Final[ARGB] = ARGB(0xFFBC8F8F)
    royalblue           :Final[ARGB] = ARGB(0xFF4169E1)
    saddlebrown         :Final[ARGB] = ARGB(0xFF8B4513)
    salmon              :Final[ARGB] = ARGB(0xFFFA8072)
    sandybrown          :Final[ARGB] = ARGB(0xFFF4A460)
    seagreen            :Final[ARGB] = ARGB(0xFF2E8B57)
    seashell            :Final[ARGB] = ARGB(0xFFFFF5EE)
    sienna              :Final[ARGB] = ARGB(0xFFA0522D)
    silver              :Final[ARGB] = ARGB(0xFFC0C0C0)
    skyblue             :Final[ARGB] = ARGB(0xFF87CEEB)
    slateblue           :Final[ARGB] = ARGB(0xFF6A5ACD)
    slategray           :Final[ARGB] = ARGB(0xFF708090)
    slategrey           :Final[ARGB] = ARGB(0xFF708090)
    snow                :Final[ARGB] = ARGB(0xFFFFFAFA)
    springgreen         :Final[ARGB] = ARGB(0xFF00FF7F)
    steelblue           :Final[ARGB] = ARGB(0xFF4682B4)
    tan                 :Final[ARGB] = ARGB(0xFFD2B48C)
    teal                :Final[ARGB] = ARGB(0xFF008080)
    thistle             :Final[ARGB] = ARGB(0xFFD8BFD8)
    tomato              :Final[ARGB] = ARGB(0xFFFF6347)
    turquoise           :Final[ARGB] = ARGB(0xFF40E0D0)
    violet              :Final[ARGB] = ARGB(0xFFEE82EE)
    wheat               :Final[ARGB] = ARGB(0xFFF5DEB3)
    white               :Final[ARGB] = ARGB(0xFFFFFFFF)
    whitesmoke          :Final[ARGB] = ARGB(0xFFF5F5F5)
    yellow              :Final[ARGB] = ARGB(0xFFFFFF00)
    yellowgreen         :Final[ARGB] = ARGB(0xFF9ACD32)



# TODO move this to physics
def move(position:Vec2, velocity:Vec2, acceleration:Vec2, time:SupportsFloat) -> Vec2:
    return position + (velocity + .5*acceleration*time)*time

@dataclass
class Sand:
    sketch:"SandSimulation"

    position     :Vec2 = field(default_factory=Vec2.zero)
    velocity     :Vec2 = field(default_factory=Vec2.zero)
    acceleration :Vec2 = field(default_factory=Vec2.zero)

    size:float = .001 #1mm
    color:ARGB = field(default_factory=lambda: Colors.yellow)

    elasticity:float = .8

    def getLineIntersection(self, line:Line, t:SupportsFloat, separation:SupportsFloat = 0) -> Vec2 | None:

        centerDist        = .5*self.size + separation
        centerDistSquared = np.square(centerDist)
        
        # compute our location relative to line endpoints after 't' time
        p1 = move(self.position, self.velocity, self.acceleration, t)
        d1 = p1 - line.v1
        d2 = p1 - line.v2 

        # check if p1's projection is between v1 and v2
        direction = line.direction
        
        if direction.dot(d1) >= 0 and direction.dot(d2) <= 0:
            
            # check to see if p1's normal distance is close enough to line
            normal  = line.normal        
            dNormal = normal.dot(d1)
            if dNormal*dNormal <= centerDistSquared:
                
                # resolve collision by projecting p1 onto the line and offsetting the normal by centerdistance  
                normalOffset = centerDist if dNormal >= 0 else -centerDist 
                return line.v1 + direction.project(p1) + normal*normalOffset

        else:
            # check to see if we are close to the line endpoints

            if d1.normSquared <= centerDistSquared:
                # TODO: implement this!
                raise NotImplementedError()

            if d2.normSquared <= centerDistSquared:
                # TODO: implement this!
                raise NotImplementedError()

        return None

    def getNextImpactLine(self, line:Line, seperation:SupportsFloat = 0) -> tuple[np.float32, np.float32]:
        
        # get initial state
        r = .5*self.size
        p = self.position
        v = self.velocity
        a = self.acceleration

        # compute acceleration, velocities, and distance orthogonal to the line
        normal  = line.normal
        aNormal = normal.dot(a)
        vNormal = normal.dot(v)
        dNormal = normal.dot(line.v1 - p)

        # offset orthogonal distance to line by radius
        if dNormal >= 0:
            dNormal-= r
        else:
            dNormal+= r

        # Minimize mean square error by solving for the four possible solutions for 'd/dt E^2 = 0'
        # where 'E = p + vt * .5at^2 - l' is the square distance between our position at time 't' and the line 'l'
        impactT = np.inf
        impactPos = None

        if aNormal != 0:
            # evaluate possible solution at t = -v/a
            t = -vNormal / aNormal
            if (0 < t < impactT):
                p1 = self.getLineIntersection(line, t, seperation) 
                if p1 is not None:
                    impactT = t
                    impactPos = p1

            sqrtTermSquared = 2*aNormal*dNormal + vNormal*vNormal
            if sqrtTermSquared >= 0:
                sqrtTerm = np.sqrt(sqrtTermSquared)

                # evaluate possible solution at t = (-v - sqrt(2a(l-p) + v^2))/a
                t = (-vNormal - sqrtTerm)/aNormal
                if (0 < t < impactT):
                    p1 = self.getLineIntersection(line, t, seperation) 
                    if p1 is not None:
                        impactT = t
                        impactPos = p1

                # evaluate possible solution at t = (-v + sqrt(2a(l-p) + v^2))/a
                t = (-vNormal + sqrtTerm)/aNormal
                if (0 < t < impactT):
                    p1 = self.getLineIntersection(line, t, seperation) 
                    if p1 is not None:
                        impactT = t
                        impactPos = p1

        elif vNormal != 0:
            # evaluate possible solution at t = (l-p)/v
            t = dNormal / vNormal

            if (0 < t < impactT):
                p1 = self.getLineIntersection(line, t, seperation) 
                if p1 is not None:
                    impactT = t
                    impactPos = p1

        return impactT, impactPos
    
    def getPointIntersection(self, point:Vec2, t:SupportsFloat, separation:SupportsFloat = 0) -> Vec2 | None:
        centerDist        = .5*self.size + separation
        centerDistSquared = np.square(centerDist)
        
        p = move(self.position, self.velocity, self.acceleration, t)
        d = p - point
        dNormSquared = d.normSquared

        if dNormSquared <= centerDistSquared:
            dScaler = centerDist/np.sqrt(dNormSquared)
            return point + d * dScaler

        return None

    def getNextImpactSand(self, sand:"Sand", seperation:SupportsFloat = 0) -> tuple[np.float32, np.float32]:
        
        # get initial state
        r = .5*self.size
        p = self.position
        v = self.velocity
        a = self.acceleration

        rSeperation = .5*sand.size + seperation

        # compute acceleration, velocities, and distance orthogonal to the line
        vNormSquared = v.normSquared
        d            = sand.position - p

        # Minimize mean square error by solving for the four possible solutions for 'd/dt E^2 = 0'
        # where 'E = p + vt * .5at^2 - l' is the square distance between our position at time 't' and the line 'l'
        impactT   = np.inf
        impactT2  = np.inf
        impactPos = None

        if a.normSquared != 0:

            # TODO: figure out if we even need this... seams to go away 
            # # evaluate possible solution at t = -v/a
            # t = -vNorm / aNorm
            # if (0 < t < impactT):
            #     p1 = self.getLineIntersection(line, t, seperation) 
            #     if p1 is not None:
            #         impactT = t
            #         impactPos = p1

            sqrtTermSquared:Vec2 = 2*a*(d + vNormSquared - r) + np.square(v)
            if sqrtTermSquared.normSquared >= 0:
                sqrtTerm:Vec2 = np.sqrt(sqrtTermSquared)

                # evaluate possible solution at t = (-v - sqrt(2a(l-p) + v^2))/a
                t2 = ((-v - sqrtTerm)/a).normSquared
                if (0 < t2 < impactT2):
                    t = np.sqrt(t2)
                    p1 = self.getPointIntersection(sand.position, t, rSeperation) 
                    if p1 is not None:
                        impactT = t
                        impactT2 = t2
                        impactPos = p1

                # evaluate possible solution at t = (-v + sqrt(2a(l-p) + v^2))/a
                t2 = ((-v + sqrtTerm)/a).normSquared
                if (0 < t2 < impactT2):
                    t = np.sqrt(t2)
                    p1 = self.getPointIntersection(sand.position, t, rSeperation) 
                    if p1 is not None:
                        impactT = t
                        impactT2 = t2
                        impactPos = p1

        elif v.normSquared != 0:
            # evaluate possible solution at t = (l-p)/v
            t2 = ((d - r)/v).normSquared

            if (0 < t2 < impactT2):
                t = np.sqrt(t2)
                p1 = self.getPointIntersection(sand.position, t, rSeperation) 
                if p1 is not None:
                    impactT = t
                    impactT2 = t2
                    impactPos = p1

        return impactT, impactPos    
        
    def update(self, deltaT:SupportsFloat) -> None:

        maxCollisions = 5
        epsilonDist = 1e-6
        # epsilonDist = 1e-3

        pos0 = self.position
        vel0 = self.velocity
        acl0 = self.acceleration

        lineColliders = self.sketch.lineColliders
        sandColliders = self.sketch.sandParticles

        deltaT = .005
        self.elasticity = .5

        for i in range(maxCollisions):
            if deltaT <= 0:
                break

            # check for collision against bounds
            hitBounds = False
            for line in lineColliders:

                # Note: we sperate collisions by epsilonDist to prevent clipping though due to floating point rounding errors
                #       this adds a very small amount of potential energy to the system, but with small epsilonDist
                #       and elasticity < 1 the system still looses energy
                impactT, impactPos = self.getNextImpactLine(line, epsilonDist)            
                if impactT <= deltaT:

                    # move to impact position and bounce off bounds
                    pos1 = impactPos

                    impactVel = vel0 + acl0*impactT
                    vel1 = self.elasticity * (impactVel - 2*line.normal.project(impactVel))
                    
                    deltaT-= impactT
                    hitBounds = True
                    break

            if not hitBounds:
                for sand in sandColliders:
                    if sand == self:
                        # skip over ourselves
                        continue

                    # Note: we sperate collisions by epsilonDist to prevent clipping though due to floating point rounding errors
                    #       this adds a very small amount of potential energy to the system, but with small epsilonDist
                    #       and elasticity < 1 the system still looses energy
                    impactT, impactPos = self.getNextImpactSand(sand, epsilonDist)            
                    if impactT <= deltaT:

                        self.getNextImpactSand(sand, epsilonDist)

                        # move to impact position and bounce off bounds
                        pos1 = impactPos
                        impactNormal = (impactPos - sand.position).direction

                        impactVel1 = vel0 + acl0*impactT
                        impactVel2 = sand.velocity
                        deltaVel   = 2*impactNormal.project(impactVel1 - impactVel2)
                        
                        vel1 = self.elasticity * (impactVel1 - deltaVel)
                        
                        # TODO: only apply this if we don't break out of loop due to no  change to pos or vel
                        sand.velocity = sand.elasticity * (impactVel2 + deltaVel)
                        
                        deltaT-= impactT
                        hitBounds = True
                        break                

            if not hitBounds:
                # safe to advance full step
                pos1 = move(pos0, vel0, acl0, deltaT)
                vel1 = vel0 + acl0*deltaT
                deltaT = 0

            if pos0 == pos1 and vel0 == vel1:
                # No updates. system is a stable equilibrium
                break
            
            # update positions and velocities
            pos0 = pos1
            vel0 = vel1

            self.velocity = vel1
            self.position = pos1
                

    def draw(self) -> None:
        self.sketch.fill(self.color)

        pixelPosition = self.sketch.pixelsPerMeter * (self.position - self.sketch.viewport.origin)
        pixelSize = self.sketch.pixelsPerMeter * self.size

        self.sketch.circle(pixelPosition.x, pixelPosition.y, pixelSize)

class SandSimulation(Sketch):
    defaultWidth:int
    defaultHeight:int
 
    viewport:Rectangle 
    gravityVector:Vec2
    pixelsPerMeter:float

    lastUpdateMs:int = 0

    # TODO: move this to a metrics class
    metricsPadding  :float = 10
    metricsFontSize :float = 16
    metricsFontColor:ARGB  = Colors.red
    metricsBGColor  :ARGB  = ARGB(0, 0, 0, 200)

    metricsEMAFrameTime:float = 0
    metricsEMAFrameTimeSmoothing: float = .1

    sandParticles:list[Sand]
    lineColliders:list[Line]


    def __init__(self, width:int, height:int):
        super().__init__()
        self.defaultWidth = width
        self.defaultHeight = height

        # make the window 20cm tall
        self.pixelsPerMeter = height / .2
        self.viewport = Rectangle(0, 0, width/self.pixelsPerMeter, height/self.pixelsPerMeter)


        # add colliders for edges of window
        self.lineColliders = [
            Line(Vec2(self.viewport.x1, self.viewport.y2), Vec2(self.viewport.x2, self.viewport.y2)),
            Line(Vec2(self.viewport.x1, self.viewport.y1), Vec2(self.viewport.x1, self.viewport.y2)),
            Line(Vec2(self.viewport.x2, self.viewport.y1), Vec2(self.viewport.x2, self.viewport.y2)),
        ]        

        # set gravity
        self.gravityVector = Vec2(0, 9.8) 

        # create sand particles
        numSandParticles = 2
        self.sandParticles = [None] * numSandParticles

        self.sandParticles[0] = Sand(
                sketch       = self,
                velocity     = Vec2(0, +.1),
                size         = 3e-3,
                # elasticity   = .1,
                position     = Vec2(self.viewport.x1 + self.viewport.size.x/2, 0),
                # acceleration = Vec2.zero()
                # acceleration = self.gravityVector
        )

        self.sandParticles[1] = Sand(
                sketch       = self,
                # velocity     = Vec2(0, -.1),
                velocity     = Vec2(0, 0),
                size         = 3e-3,
                # elasticity   = .1,
                position     = Vec2(self.viewport.x1 + self.viewport.size.x/2, self.viewport.size.y/1.5),
                # acceleration = Vec2.zero()
                # acceleration = self.gravityVector
        )


        # for i in range(numSandParticles):
            
        #     self.sandParticles[i] = Sand(
        #         sketch       = self,
        #         velocity     = Vec2.random(-1, 1, -1, 0),
        #         size         = 3e-3,
        #         position     = Vec2.random(self.viewport.x1, self.viewport.x2, self.viewport.y1, self.viewport.y2),
        #         # position     = Vec2(self.viewport.x1 + self.viewport.size.x/2, 0),
        #         # position     = Vec2(self.viewport.x1 + self.viewport.size.x/2, self.viewport.y1 + self.viewport.size.y/1.5),
        #         # elasticity   = np.random.rand(),
        #         acceleration = self.gravityVector
        #         # acceleration = Vec2.zero()
        #     )


    def settings(self) -> None:
        debugpy.debug_this_thread()
        self.size(self.defaultWidth, self.defaultHeight)

    def setup(self) -> None:
        debugpy.debug_this_thread()
        self.text_font(self.create_font("consolas", 12))
        self.rect_mode(self.CORNER)
        self.color_mode(self.RGB)
        self.no_stroke()

    def draw(self) -> None:
        debugpy.debug_this_thread()

        # compute the lapsed time since the last frame
        updateMs = self.millis()
        deltaMs = (updateMs - self.lastUpdateMs) if self.lastUpdateMs != 0 else 0
        deltaT = 1e-3 * deltaMs

        # Clear the screen
        self.background(0)

        # update and draw sand
        self.updateSand(deltaT)
        self.drawSand()

        # draw FPS counter
        self.drawMetrics(deltaT)

        self.lastUpdateMs = updateMs


    def updateSand(self, deltaT:float) -> None:
        for sand in self.sandParticles:
            sand.update(deltaT)


    def drawSand(self) -> None:
        for sand in self.sandParticles:
            sand.draw()


    def drawMetrics(self, frameTime:float) -> None:
        
        # update exponential moving average frame time
        self.metricsEMAFrameTime = frameTime*self.metricsEMAFrameTimeSmoothing + self.metricsEMAFrameTime*(1 - self.metricsEMAFrameTimeSmoothing) 

        # build metrics string
        emaFPS = (1 / self.metricsEMAFrameTime) if self.metricsEMAFrameTime > 0 else 0
        metricsStr = f"FrameTime: {frameTime*1e3:0.2f}ms | FPS: {emaFPS :5.2f} | Particles: {len(self.sandParticles)}"

        # compute string width
        self.text_size(self.metricsFontSize)
        metricsStrWidth = self.text_width(metricsStr)

        # draw background bar
        self.fill(self.metricsBGColor)
        self.rect(0, 0, (metricsStrWidth + 2*self.metricsPadding), (self.metricsFontSize + 2*self.metricsPadding))

        # draw metrics text
        self.fill(self.metricsFontColor)
        self.text(metricsStr, self.metricsPadding, (self.metricsPadding + self.metricsFontSize))

def main() -> None:
    simulation = SandSimulation(800, 800)    
    simulation.run_sketch()


if __name__ == "__main__":
    main()