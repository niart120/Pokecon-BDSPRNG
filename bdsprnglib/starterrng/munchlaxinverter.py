import numpy as np
from ..restoreseedmodule.utils import *
from ..rng.xorshift import Xorshift

class MunchlaxInverter(object):
    def __init__(self, eps:float = 0.1, munchlax_blink:float = 0.285):
        self.blinkcount = 0
        self.entropy = 0
        self.t = get_trans()
        self.matrix = []
        self.vec = []
        
        self.intervals = []
        self.epsilon = int((0x7f_ffff / 9.0) * eps)
        self.munchlax_blink = munchlax_blink

    def add_interval(self, interval:float):
        self.blinkcount += 1
        self.intervals.append(interval)

        raw = get_raw_int(interval, self.munchlax_blink)

        # https://hackmd.io/@yatsuna827/SkC4h5JZq に基づいて信頼可能な下位nビットを求める
        n = count_confidence_bits(raw, self.epsilon)
        # 全bit信頼できない場合はそのまま終了
        if n==0:
            self.t = self.t@get_trans() % 2
            return
        
        # 信頼できるなら進めよう
        # matrixに現在の行列の(128-23) ~ (128-23+n)行成分を追加
        self.matrix.append(self.t[-23:-(23-n)])

        # vec配列に現在の瞬きで得られる情報を追加
        bitvec = (raw >> (23-n)) & ((1 << n) - 1)
        lst = bitvec2list(bitvec, size = n)
        self.vec.extend(lst)

        # エントロピー更新
        self.entropy += n
        # t(遷移行列)を更新
        self.t = self.t@get_trans() % 2
        return
        
    def try_restore_state(self)->Xorshift:
        if self.entropy < 128:
            return None
        mat = np.vstack(self.matrix)

        raw_result = gauss_jordan(mat, self.vec)
        # 復元に失敗した場合はNoneを返す
        if raw_result is None:
            return None

        # bitvectorの形式に変換
        bitvec_result = list2bitvec(raw_result)
        state = []
        for i in range(4):
            state.append(bitvec_result&0xFFFFFFFF)
            bitvec_result>>=32
        state = state[::-1] # 逆順になってるのでひっくり返す
        return Xorshift(*state)
