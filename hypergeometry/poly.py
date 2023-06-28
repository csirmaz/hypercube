
from typing import Iterable, Union
import numpy as np

from hypergeometry.point import Point

class Poly:
    """A collection of points or vectors represented as a matrix"""
    
    def __init__(self, points):
        """Accepts a 2D matrix or a list of points"""
        if isinstance(points[0], Point):
            points = [p.c for p in points]
        self.p = np.array(points)

    def __str__(self):
        return "(" + ",\n".join((f"{p}" for p in self.to_points())) + ")"
    
    @classmethod
    def from_identity(cls, dim: int) -> 'Poly':
        """Create a Poly from an identity matrix"""
        return Poly(np.identity(dim))

    @classmethod
    def from_random(cls, dim: int, num: int) -> 'Poly':
        """Create a Poly from values from a uniform distribution over `[0,1)`."""
        return Poly(np.random.rand(num, dim))
    
    def clone(self) -> 'Poly':
        """Returns a deep clone"""
        return Poly(self.p)
    
    def map(self, lmbd) -> 'Poly':
        """Generate a new Poly object using a lambda function applied to Point objects"""
        return Poly([lmbd(Point(p)) for p in self.p])
        
    def dim(self) -> int:
        """Return the number of dimensions"""
        return self.p.shape[1]
    
    def num(self) -> int:
        """Return the number of points/vectors"""
        return self.p.shape[0]
    
    def at(self, x: int) -> Point:
        """Return the x'th point as a Point object"""
        return Point(self.p[x])
    
    def to_points(self):
        """Separate into an array of Point objects"""
        return [Point(p) for p in self.p]
    
    def eq(self, p: 'Poly') -> bool:
        return (self.p == p.p).all()
    
    def allclose(self, p: 'Poly') -> bool:
        # Prevent broadcasting
        return self.p.shape == p.p.shape and np.allclose(self.p, p.p)
    
    def add(self, p: Point) -> 'Poly':
        return Poly(self.p + p.c)
    
    def sub(self, p: Point) -> 'Poly':
        return Poly(self.p - p.c)
    
    def mean(self) -> Point:
        return Point(np.average(self.p, axis=0))
    
    def norm(self) -> 'Poly':
        """Normalise each vector"""
        return Poly(self.p / np.sqrt(np.square(self.p).sum(axis=1, keepdims=True)))
    
    def rotate(self, coords: Iterable[int], rad: float) -> 'Poly':
        """Rotate each point. coords is a list of 2 coordinate indices that we rotate"""
        # Can do it faster by directly interacting with the matrix
        return Poly([p.rotate(coords, rad) for p in self.to_points()])

    def project(self, focd: float) -> 'Poly':
        """Project the points onto a subspace where the last coordinate is 0.
        `focd` is the distance of the focal point from the origin along this coordinate.
        """
        a = focd / (focd - self.p[:,-1])
        return Poly(self.p[:,:-1] * np.expand_dims(a, axis=1))
    
    def is_norm_basis(self) -> bool:
        """Returns if the collection of vectors is a "normal" basis (vectors are unit length and pairwise perpendicular)"""
        dots = self.p @ self.p.transpose()
        identity = np.identity(self.num())
        return dots.shape == identity.shape and np.allclose(dots, identity)

    def make_basis(self, strict=True) -> 'Poly':
        """Transform the vectors in self into a "normal" basis (unit-length pairwise perpendicular vectors).
        If strict=False, may leave out vectors if they are not linearly independent.
        """
        out = [self.at(0).norm()]
        for i in range(1, self.num()):
            v = self.at(i)
            for j in range(0, i):
                d = out[j].dot(v)
                v = v.sub(out[j].scale(d))
                # print(f"i={i} j={j} v_org={self.at(i)} out[j]={out[j]} d={d} v={v} {v.is_zero()}")
                if v.is_zero():
                    if strict:
                        raise Exception("make_basis: not independent")
                    v = None
            if v is not None:
                out.append(v.norm())
        return Poly(out)
    
    def apply_to(self, subject: Union['Poly', Point]) -> Union['Poly', Point]:
        """Get the linear combination of vectors in `self` according to the vector(s) in `subject`.
        If `self` is a basis, this converts vector(s) expressed in that basis into absolute coordinates."""
        assert subject.dim() == self.num() # DIM==bNUM
        if isinstance(subject, Point):
            return Point(subject.c @ self.p) # <(1), DIM> @ <bNUM, bDIM> -> <(1), bDIM>
        if isinstance(subject, Poly):
            return Poly(subject.p @ self.p) # <NUM, DIM> @ <bNUM, bDIM> -> <NUM, bDIM>
        raise Exception("apply_to: unknown type")
    
    def extract_from(self, subject: Union['Poly', Point]) -> Union['Poly', Point]:
        """Represent the point(s) in `subject` relative to the basis in `self` by
        returning the vector(s) x for which xA=s, where A is `self`, and s is `subject`.
        `self` must be an invertible matrix.
        """
        si = np.linalg.inv(self.p)
        if isinstance(subject, Point):
            return Point(subject.c @ si)
        if isinstance(subject, Poly):
            return Poly(subject.p @ si)
        raise Exception("extract_base_from: unknown type")
        
