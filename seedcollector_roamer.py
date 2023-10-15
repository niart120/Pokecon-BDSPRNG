# このコードはMITライセンスに準拠します 
# 良く分からんと言う人:末尾のライセンス表記を消さなければご自由にお使い頂いて構いません. 
# 但し, 以下のコードを利用したことによる責任は一切負いかねます. 自己責任でお願いします.

import cv2
import numpy as np

from Commands.PythonCommandBase import  ImageProcPythonCommand
from Commands.Keys import KeyPress, Button, Direction, Stick, Hat

from .bdsprnglib.restoreseed import PlayerBlinkInverter, PlayerLinearSearch
from .bdsprnglib.restoreseedmodule import PlayerBlink
from .bdsprnglib.rng import Xorshift
from .bdsprnglib.generators import RoamerGenerator
from .bdsprnglib.generators.generatorext import ShinyType, SizeType

import time
import re
from typing import Tuple

"""
- ゲームの起動から主人公の自宅2Fでの基準Seed特定までの操作を自動で実行します.
- メニュー画面でBDSPのソフトにカーソルが合っている状態で実行してください.
- 便利ボタンの左キーに"博士の言葉"を表示させる任意の道具(ex. すごいつりざお, じてんしゃ, ポケトレetc)が登録されている必要があります.

"""

def calculate_SEARCHMAX(p):
    """目標seedの出現頻度に応じて許容する消費数の上限を計算してくれる凄い奴

    Parameters:
        p:float: 目標seedの出現確率 

    Returns:
        int: 許容する消費数の上限の値
    """
    # 目標Seedの出現確率(の近似)
    # U \approx \sqrt{\frac{3CA}{p}} がE(T)+3SD(T)を最小化する良い近似を与える
    U = int((3*720*100/p)**(0.5))

    print(f"Calculate U(threshould)")
    print(f"U={U}, p = {p}")

    return U

class BaseSeedCollector(ImageProcPythonCommand):
    NAME = 'BDSP_基準Seed厳選(徘徊固定シンボル)'
 
    def __init__(self, cam):
        super().__init__(cam)
 
    def do(self):
        shiny_condition = ShinyType.StarSquare
        size_condition = SizeType.XXXSXXXL

        # 黒魔術
        self.camera.camera.set(cv2.CAP_PROP_BUFFERSIZE,1)
        
        #検索数上限の決定
        self.SEARCHMAX = calculate_SEARCHMAX((1/4096) * (1/8192)) 

        # コントローラー入力チェック
        for _ in range(5): self.press(Button.B, wait=0.1)
        
        # Seed厳選
        result = None
        while True:
            launch_game_time = time.perf_counter()
            # メニュー画面から操作可能画面まで遷移
            self.menu2playable()
            # seed特定
            restored = None
            while restored is None:
                restored = self.restore_baseseed()
            
            # 個体検索の実行
            result = self.search_roamer_symbol(restored, shiny_condition, size_condition)
            if result is not None: break
            print("Not found...")
            print("Reset game")

            # メニューに戻る->ゲーム終了
            self.press(Button.HOME, wait=0.5)
            self.press(Button.X, wait=0.5)
            self.press(Button.A, wait=1.5)

            elapsed = time.perf_counter() - launch_game_time
            print(f"elapsed:{elapsed:.3f} s")

        adv, shiny_type, size_type = result

        print(f"Found at :advance={adv}, shiny_type={shiny_type}, size_type={size_type}")
        self.press(Button.HOME)

    def menu2playable(self):
        print("launch game")
        # ゲーム選択
        self.press(Button.A, wait=1.2)
        # ユーザー選択
        self.press(Button.A, wait=20)
        #(暗転)

        # キャラクターが操作可能になるまで連打
        print("mash A until playable")
        for _ in range(100): self.press(Button.A, wait=0.1)

        # ↓方向へ移動させて向きを固定
        self.press(Hat.BTM, duration = 1.0, wait=0.1)
        # キャラクターロック
        self.press(Button.PLUS, wait=0.5)
        self.press(Hat.LEFT, wait=0.1)

    def observe_blink_interval(self)->float:
        # 閾値
        THRESHOLD = 1000.0
        # タイマー用変数
        current_time = time.perf_counter()
        # 前回の瞬き時間
        prev_blink_time = 0
        # 瞬き中かを判別する
        is_blinked = False        

        print("start observation")
        while True:
            self.wait(0.01)
            # 現在時刻取得
            current_time = time.perf_counter()
            # 画像取得
            img = cv2.cvtColor(self.camera.readFrame(), cv2.COLOR_BGR2GRAY)
            eyeimg = img[510:535, 615:630] #x = 615, y = 510, xwidth = 15, ywidth = 25
            # 瞬き検知

            eyevalue = np.var(eyeimg) #平均二乗誤差を使う? -> バイアスでスライドするだけなので分散でOK
            is_blinking = eyevalue < THRESHOLD
            #print(eyevalue)
            # 瞬きをしていてひとつ前のフレームでも瞬きをしていないなら更新
            if is_blinking and not is_blinked:
                # 瞬き間隔の測定
                interval = current_time - prev_blink_time
                if prev_blink_time != 0:
                    # 瞬き間隔, 現在時刻をyield
                    yield interval, current_time
                # 前回の瞬きタイミングを更新する
                prev_blink_time = current_time

            # ひとつ前のフレームの状態を更新
            is_blinked = is_blinking

    def restore_baseseed(self)->Xorshift:
        # RNG回りの何か
        inverter = PlayerBlinkInverter()
        restored = None
        
        BLINKCONST = 1.017 #瞬き判定時間定数

        count = 0
        prev = 0
        prev_blink_type = PlayerBlink.Single

        # 特定結果検証用に間隔を記録しておく
        intervals = []


        # 最初に観測した段階では, 次の瞬きが来るまでSingleかDoubleかを判別することは出来ない.
        # 観測した瞬きを用いて即座に判定を行うのではなく, 前回までの観測結果を元にSeed特定を行う.
        for raw_interval, current_time in self.observe_blink_interval():
            # 初回のみprevを更新してループに戻る
            if prev==0:
                prev = current_time
                continue

            intvl = raw_interval/BLINKCONST

            # 二回瞬きの場合はblinktypeを上書きしてループに戻る
            if intvl < 0.6:
                prev_blink_type = PlayerBlink.Double
                continue

            # いずれにも該当しないので前回までの観測結果を入れる
            inverter.add_blink(prev_blink_type)

            # 四捨五入して瞬き間隔を計算
            interval = int(intvl + 0.5)

            # 検証用リストへの追加
            intervals.append(interval)

            print(f"prev_blink_type:{prev_blink_type}\tentropy:{inverter.entropy}\tinterval:{interval}")
            # 復元を試みる
            restored = inverter.try_restore_state()
            # 復元結果が得られたならループ離脱
            if restored is not None:break

            # 失敗した場合は今回の瞬き間隔分だけ瞬き無し(Nothing)をいれる
            # interval-1だけNoneを追加
            for i in range(interval-1):
                inverter.add_blink(PlayerBlink.Nothing)

            prev = current_time
            prev_blink_type = PlayerBlink.Single

            # もし観測回数が50回を超える(エントロピーが200より大きい)場合は強制打ち切り
            if inverter.entropy > 200:
                print("Failure...")
                return None

        # 特定結果の検証
        pls = PlayerLinearSearch()
        for interval in intervals:
            pls.add_interval(interval)

        elapsed = sum(intervals)
        try:
            _, baseseed = next(pls.search(restored, elapsed + 1))
        except StopIteration:
            print("Failure...")
            return None

        # 復元された乱数生成器の内部状態を表示
        print()
        s_0, s_1, s_2, s_3 = restored.get_state()
        x_0, x_1 = (s_0 << 32) | s_1, (s_2 << 32) | s_3
        print(f"restored! seed0:{hex(x_0)}, seed1:{hex(x_1)}")
        #print(f"restored: {[hex(s_i).upper() for s_i in restored.get_state()]}")
        print(f"blink: {inverter.blinkcount} times")
        return restored

    def search_roamer_symbol(self, rng:Xorshift, shiny_condition:ShinyType, size_condition:SizeType):
        rng = rng.deepcopy()

        # 移動時間を見越して10万消費分は予めスキップする
        rng.advance(100000)
        adv = 100000
        gen = RoamerGenerator(use_synchronize=False)

        # SEARCHMAXを上限として検索
        for _ in range(self.SEARCHMAX):
            shiny_type, size_type = gen.pseudogenerate(rng)
            if (shiny_type & shiny_condition) > 0 and (size_type & size_condition) > 0: 
                return (adv, shiny_type, size_type)
            rng.get_rand()#空読み
            adv += 1

        return None



"""
MIT License
Copyright (c) 2023 niart120
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""