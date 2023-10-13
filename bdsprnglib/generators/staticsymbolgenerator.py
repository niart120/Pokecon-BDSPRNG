from .generatorext import ShinyType, _generate_ivs, _to_shiny_type, _to_size_type
from ..rng.xorshift import Xorshift

class StaticSymbolGenerator:
    def __init__(self, flawless_ivs:int=3, fixed_ability:int=3, fixed_gender:bool=True, use_synchronize:bool=False, never_shiny:bool=False):
        self.flawless_ivs = flawless_ivs
        self.fixed_ability = fixed_ability
        self.fixed_gender = fixed_gender
        self.use_synchronize = use_synchronize
        self.never_shiny = never_shiny

    def pseudogenerate(rng:Xorshift):
        # 簡単のため色違い判定とサイズ判定の結果のみ返す
        
        rng = rng.deepcopy() # 副作用が無いように見せかけるためコピーを取る
        rng.get_rand() #ec

        # 色違い判定処理
        temp_tidsid = rng.get_rand() 
        temp_tsv = (temp_tidsid & 0xFFFF) ^ (temp_tidsid >> 16)

        pid = rng.get_rand()
        psv = (pid&0xFFFF) ^ (pid >> 16)

        shiny_type = ShinyType.NotShiny if self.never_shiny else _to_shiny_type(psv, temp_tsv)

        _generate_ivs(rng, self.flawless_ivs) #個体値判定消費

        if self.fixed_ability == 2 or self.fixed_ability == 3: rng.get_rand() # 夢特性固定(ハマナスパーク), 通常判定(ディアパルetc)の場合は特性判定消費

        if not self.fixed_gender: rng.get_rand() # 性別不明/固定で無い場合は性別判定消費

        if not self.use_synchronize: rng.get_rand() # シンクロを使わない場合は性格判定消費

        size = rng.get_rand() % 129 + rng.get_rand() % 128 # 厳密にはheight(高さ)だが証関連ではこの値のみ参照する
        size_type = _to_size_type(size)
        return (shiny_type, size_type)