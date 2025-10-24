def lerp(t:float, min:float, max:float) -> float:
    v = t * (max - min) + min
    
    return max if v >= max else \
           min if v <= min else \
           v