def _rotl(val:int, s:int):
    return ((val << s) ^ (val >> s)) & 0xFFFFFFFFFFFFFFFF

def _temper(seed:int, state:int):
    seed += state
    
    seed = 0xBF58476D1CE4E5B9 * (seed ^ (seed >> 30))
    seed &= 0xFFFFFFFFFFFFFFFF
    seed = 0x94D049BB133111EB * (seed ^ (seed >> 27))
    seed &= 0xFFFFFFFFFFFFFFFF

    return seed ^ (seed >> 31)

class XoroshiroBDSP(object):
    def __init__(self, seed):
        self.s0 = _temper(seed, 0x9E3779B97F4A7C15)
        self.s1 = _temper(seed, 0x3C6EF372FE94F82A)

    def deepcopy(self):
        return Xoroshiro(*self.get_state())

    def next(self):
        t0, t1 = self.s0, self.s0 ^ self.s1
        res = (self.s0 + self.s1) & 0xFFFFFFFFFFFFFFFF

        self.s0, self.s1 = (_rotl(self.s0, 24) ^ self.s1 ^ (self.s1 << 16)) & 0xFFFFFFFFFFFFFFFF, rotl(self.s1, 37)

        return self.w

    def get_rand(self, exmax = 0x100000000):
        return (self.next() >> 32) % exmax

    def get_state(self):
        return [self.s0, self.s1]

    def set_state(self, s0, s1, s2, s3):
        self.s0 = s0
        self.s1 = s1