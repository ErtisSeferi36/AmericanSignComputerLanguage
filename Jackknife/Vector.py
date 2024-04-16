import math

class Vector:
    def __init__(self, data):
        if isinstance(data, list):
            self.data = data.copy()
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