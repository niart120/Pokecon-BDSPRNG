from .generatorext import ShinyType, _generate_ivs, _to_shiny_type, _to_size_type
from ..rng.xorshift import Xorshift
from ..rng.xoroshiroBDSP import XoroshiroBDSP

class RoamerGenerator:
    def __init__(self, flawless_ivs:int=3, use_synchronize:bool=False):
        self.flawless_ivs = flawless_ivs
        self.use_synchronize = use_synchronize

    def pseudogenerate(rng:Xorshift):
        # 簡単のため色違い判定とサイズ判定の結果のみ返す
        
        rng = rng.deepcopy() # 副作用が無いように見せかけるためコピーを取る
        ec = rng.get_rand() #ec

        # xoroshiro128の初期化
        _rng = XoroshiroBDSP(ec)

        # 色違い判定処理
        temp_tidsid = _rng.get_rand(0xFFFFFFFF) 
        temp_tsv = (temp_tidsid & 0xFFFF) ^ (temp_tidsid >> 16)

        pid = _rng.get_rand()
        psv = (pid&0xFFFF) ^ (pid >> 16)

        shiny_type = _to_shiny_type(psv, temp_tsv)

        _generate_ivs(_rng, self.flawless_ivs) #個体値判定消費

        _rng.get_rand() # 特性判定消費

        if not self.use_synchronize: _rng.get_rand() # シンクロを使わない場合は性格判定消費

        size = _rng.get_rand(129) + _rng.get_rand(128) # 厳密にはheight(高さ)だが証関連ではこの値のみ参照する

        size_type = _to_size_type(size)
        return (shiny_type, size_type)