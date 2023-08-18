from ..rng.xorshift import Xorshift
from ..restoreseedmodule.blinkgeneratorext import *

class MunchlaxLinearSearch(object):
    def __init__(self):
        self.intervals = []

    def add_interval(self, interval:float):
        self.intervals.append(interval)

    def search(self, rng:Xorshift, maxrange:int, epsilon:float=0.1):
        rng = rng.deepcopy()

        blink_cahce = [0]*256 # 瞬き間隔のキャッシュ

        for i in range(len(self.intervals)):
            blink_cahce[i] = blink_pokemon(rng)

        def check(k:int):
            for i in range(len(self.intervals)):
                b = blink_cahce[(k + i) & 0xFF]
                if abs(self.intervals[i] - b) > epsilon: return False
            return True
        
        head = 0
        tail = len(self.intervals)

        while head <= maxrange:
            if check(head): yield (tail, rng.deepcopy())
            head += 1
            blink_cahce[tail & 0xFF] = blink_pokemon(rng)
            tail += 1
        yield None

    def reset(self):
        self.intervals = []