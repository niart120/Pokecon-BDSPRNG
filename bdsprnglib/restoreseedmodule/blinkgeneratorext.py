from enum import IntEnum
from ..rng.xorshift import Xorshift

class PlayerBlink(IntEnum):
    Nothing = 2
    Single = 0
    Double = 1

def blink_player(rng:Xorshift):
    r = rng.get_rand() & 0xF
    return PlayerBlink.Single if r == 0 else PlayerBlink.Double if r == 1 else PlayerBlink.Nothing

def blink_player_noisy(rng:Xorshift, poke_blink_timer:float, adv:int):
    poke_blink_timer -= 61 / 60.0

    if poke_blink_timer <= 0:
        poke_blink_timer += blink_pokemon(rng)
        adv += 1
    
    adv += 1
    return (blink_player(rng), poke_blink_timer, adv)
    
def blink_pokemon(rng:Xorshift, pokemon_blink:float = 0.285):
    return rng.range_float(3.0, 12.0) + pokemon_blink

def get_next_player_blink(rng):
    idx = 1
    while True:
        if (blink_player(rng) != PlayerBlink.Nothing): return idx
        idx += 1

def get_next_player_blink_noisy(rng:Xorshift, poke_blink_timer:float):
    dt = 61/60.0
    remain = poke_blink_timer
    
    idx = 1
    while True:
        remain -= dt
        if remain <= 0: remain += blink_pokemon(rng)
        if blink_player(rng) != PlayerBlink.Nothing: return (idx, remain)
