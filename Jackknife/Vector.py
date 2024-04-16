import math
import numbers

class Vector:
    def __init__(self, data, cmp_cnt=None):
        if isinstance(data, list):
            self.data = data.copy()
        elif isinstance(data, int):
            self.data = [0 for col in range(data)]
        elif isinstance(data, numbers.Number) and isinstance(cmp_cnt, numbers.Number):
            self.data = [data for col in range(cmp_cnt)]
        elif isinstance(data, Vector):
            self.data = data.data.copy()

    
    @staticmethod
    def interpolate(a, b, t):
        if len(a.data) != len(b.data):
            raise ValueError("Vectors not same length")
        return Vector([(1-t) * a.data[i] + t * b.data[i] for i in range(len(a.data))])

    def size(self):
        return len(self.data)
    
    def __getitem__(self, index):
        return self.data[index]
    
    def __setitem__(self, index, value):
        self.data[index] = value
    
    def __add__(self, other):
        if isinstance(other, Vector):
            if len(self.data) != len(other.data):
                raise ValueError("Vectors not same length")
            return Vector([self.data[ii] + other.data[ii] for ii in range(len(self.data))])
        else:
            raise TypeError("Unsupported type")
            
    def __sub__(self, other):
        if isinstance(other, Vector):
            if len(self.data) != len(other.data):
                raise ValueError("Vectors not same length")
            return Vector([self.data[ii] - other.data[ii] for ii in range(len(self.data))])
        else:
            raise TypeError("Unsupported type")
        
    def __mul__(self, other):
        if isinstance(other, Vector):
            if len(self.data) != len(other.data):
                raise ValueError("Vectors not same length")
            return Vector([self.data[ii] * other.data[ii] for ii in range(len(self.data))])
        else:
            raise TypeError("Unsupported type")
        
    def __div__(self, other):
        if isinstance(other, (int, float)):
            return Vector([self.data[i] / other for i in range(len(self.data))])
        elif isinstance(other, Vector):
            return Vector([self.data[i] / other.data[i] if other.data[i] != 0 else float('inf') for i in range(len(self.data))])
        else:
            raise TypeError("Unsupported type")
        
    def magnitude(self):
        return math.sqrt(sum(x ** 2 for x in self.data))

    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Can't normalize")
        return Vector([x / mag for x in self.data])
    
    def l2norm2(self, other):
        ret = 0

        for ii in range(self.size()):
            delta = self.data[ii] - other.data[ii]
            ret += delta * delta

        return ret

    def l2norm(self, other):
        return math.sqrt(self.l2norm2(other))
    
    def dot(self, rhs):
        m = self.size()
        ret = 0

        for ii in range(m):
            ret += self.data[ii] * rhs.data[ii]

        return ret
    
    def sum(self):
        ret = 0

        for ii in range(self.size()):
            ret += self.data[ii]

        return ret
    
    def append(self, value):
        self.data.append(value)

    def cumulative_sum(self):
        ret = 0

        for ii in range(len(self.data)):
            ret += self.data[ii]
            self.data[ii] = ret

    def set_all_elements_to(self, value):
        for ii in range(len(self.data)):
            self.data[ii] = value