from collections import deque
from ..rng.xorshift import Xorshift
from ..restoreseedmodule.blinkgeneratorext import *

class PlayerLinearSearch(object):

    def __init__(self):
        self.intervals = deque()
        self.blinkcount = 0

    def add_interval(self, interval:int):
        self.intervals.append(interval)

    def search(self, rng:Xorshift, maxrange:int):
        # 副作用が無いように見せかけるためコピーを取る
        rng = rng.deepcopy()

        index_queue = deque()
        interval_queue = deque()

        idx = get_next_player_blink(rng)

        for i in range(len(self.intervals)):
            interval = get_next_player_blink(rng)
            idx += interval

            index_queue.append(idx)
            interval_queue.append(interval)

        head = 0
        tail = len(self.intervals)
        while head < maxrange:
            if self.intervals == interval_queue: yield (idx, rng.deepcopy())

            interval = get_next_player_blink(rng)
            idx += interval
            index_queue.append(idx)
            interval_queue.append(interval)

            index_queue.popleft()
            interval_queue.popleft()

            head += 1
            tail += 1

    def search_noisy(self, rng:Xorshift, maxrange:int, dt = 1.0/60.0):
        for i in range(1, maxrange+1):
            if blink_player(rng) == PlayerBlink.Nothing:continue
            
            offset = 0.0
            while offset < 12.3:
                rand = rng.deepcopy()
                
                is_noisy, advance, rest = self.check_noisy(rand, offset)
                if is_noisy:
                    yield (i + advance, rest, rand)
    
    def check_noisy(self, rng:Xorshift, pk_timer_offset:float):
        advance = 0
        pk_timer = pk_timer_offset

        for observed in self.intervals:
            interval = 0
            while True:
                interval += 1
                if interval > observed: return False, None, None

                # ポケモンの瞬きフレームの場合
                pk_timer -= 61.0 / 60.0
                if pk_timer <= 0:
                    advance += 1
                    pk_timer += blink_pokemon(rng)
            
            advance += 1
            if blink_player(rng)  != PlayerBlink.Nothing:
                if interval != observed: return False, None, None
                break
        
        return (True, advance, pk_timer)