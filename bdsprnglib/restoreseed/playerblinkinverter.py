import numpy as np
from ..restoreseedmodule.blinkgeneratorext import PlayerBlink
from ..restoreseedmodule.utils import *
from ..rng.xorshift import Xorshift

class PlayerBlinkInverter(object):
    def __init__(self):
        self.blinkcount = 0
        self.entropy = 0
        self.t = get_trans()
        self.matrix = []
        self.vec = []
        self.inv = None

    def add_blink(self, blinktype:PlayerBlink)->None:
        """_summary_

        Args:
            blinktype (PlayerBlink): _description_
        """

        self.blinkcount += 1

        # 瞬きが無い場合はt(遷移行列)を更新して終了
        if blinktype==PlayerBlink.Nothing:
            self.t = self.t@get_trans() % 2
            return

        # 任意の瞬きがあった場合
        # matrixに現在の行列の125-128行成分を追加
        self.matrix.append(self.t[-4:])
        # vec配列に現在の瞬きを追加
        self.vec.extend([0,0,0,int(blinktype)])
        # エントロピー更新
        self.entropy += 4
        # t(遷移行列)を更新
        self.t = self.t@get_trans() % 2

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
