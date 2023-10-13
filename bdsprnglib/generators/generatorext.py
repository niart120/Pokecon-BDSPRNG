from enum import IntEnum

class ShinyType(IntEnum):
    Nothing = 0
    NotShiny = 1
    Star = 2
    Square = 4
    StarSquare = 6
    Any = 7

class SizeType(IntEnum):
    Nothing = 0
    XXXS = 1
    XXS = 2
    XS = 4
    S = 8
    M = 16
    L = 32
    XL = 64
    XXL = 128
    XXXL = 256
    XXXSXXXL = 257
    Any = 511

def _to_size_type(size:int):
    if size == 0: return SizeType.XXXS
    if size <= 30: return SizeType.XXS
    if size <= 60: return SizeType.XS
    if size <= 100: return SizeType.S
    if size <= 160: return SizeType.M
    if size <= 195: return SizeType.L
    if size <= 241: return SizeType.XL
    if size <= 254: return SizeType.XXL
    if size == 255: return SizeType.XXXL
    return SizeType.Any

def _to_shiny_type(psv:int, tsv:int):
    sv = psv ^ tsv
    if sv >= 16: return ShinyType.NotShiny
    return ShinyType.Square if sv == 0 else ShinyType.Star

def _generate_ivs(rng:Xorshift, flawless_ivs:int):
    ivs = [32]*6
    for i in range(flawless_ivs):
        while True:
            idx = rng.get_rand() % 6
            if ivs[idx] == 32:
                intivs[idx] = 31
                break

    for i in range(6):
        if ivs[i] == 32: ivs[i] = rng.get_rand() % 32
    return ivs