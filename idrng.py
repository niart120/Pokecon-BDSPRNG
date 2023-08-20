# このコードはMITライセンスに準拠します 
# 良く分からんと言う人:末尾のライセンス表記を消さなければご自由にお使い頂いて構いません. 
# 但し, 以下のコードを利用したことによる責任は一切負いかねます. 自己責任でお願いします.

import cv2
import numpy as np

from Commands.PythonCommandBase import  ImageProcPythonCommand
from Commands.Keys import KeyPress, Button, Direction, Stick, Hat

from .bdsprnglib.starterrng import MunchlaxInverter, MunchlaxLinearSearch, generate_id
from .bdsprnglib.restoreseedmodule import blink_pokemon
from .bdsprnglib.rng import Xorshift

import time
from typing import Tuple

"""
- ゲームの起動から基準Seed厳選, ID検索, 乱数消費, ID決定までの操作を自動で実行します.
- 名前入力画面まで到達したのち, ホーム画面に戻って自動操作を終了します. 任意の名前を入力してストーリーを開始し, 目的のIDが得られているかを確認してください.
- 注意:名前入力後の博士からの確認画面は必ず"はい"を選択してください.

- メニュー画面でBDSPのソフトにカーソルが合っている状態で実行してください.
- id調整を行う用のアカウントを新しく作成した上で, ゲーム起動時にそのアカウントにカーソルがあっている必要があります.

また, `target_g7tid_list` または `target_tidsid_list` のいずれかのリストに目的のIDを格納してください.
格納形式はコメントの通りです.
"""

target_g7tid_list = [] # 先頭に0を付けない整数で格納してください. 例: 000827 -> target_g7tid_list = [827]
target_tidsid_list = [] # 先頭に0を付けない整数のタプルで格納してください.  例: tidが01234, sidが56789なら, target_tidsid_list = [(1234, 56789)] 
EPSILON = 0.1 # 許容観測誤差

def tidsid_list2set(tidsid_list):
    return set([(sid<<16) ^ tid  for (tid, sid) in tidsid_list])

def calculate_SEARCHMAX():
    """目標IDの出現頻度に応じて許容する消費数の上限を計算してくれる凄い奴

    Returns:
        int: 許容する消費数の上限の値
    """
    # 目標Seedの出現確率(の近似)
    p = len(target_g7tid_list)/1_000_000 + len(target_tidsid_list)/(2**32)
    # U \approx \sqrt{\frac{3CA}{p}} がE(T)+3SD(T)を最小化する良い近似を与える
    U = int((3*300*1.2/p)**(0.5))

    print(f"Calculate U(threshould)")
    print(f"U={U}, p = {p}")

    return U

class IDRNG(ImageProcPythonCommand):
    NAME = 'BDSP_ID調整'
 
    def __init__(self, cam):
        super().__init__(cam)
 
    def do(self):
        # もし目標IDが空なら中止
        if len(target_g7tid_list) == 0 or len(target_tidsid_list) == 0:
            print("target id list is empty.")
            print("Automation abort.")
        
        # 黒魔術
        self.camera.camera.set(cv2.CAP_PROP_BUFFERSIZE,1)
        
        #検索数上限の決定
        self.SEARCHMAX = calculate_SEARCHMAX() 

        # コントローラー入力チェック
        for _ in range(5): self.press(Button.B, wait=0.1)
        
        # Seed厳選
        result = None
        while True:
            # メニュー画面から名前確認画面まで遷移
            self.menu2namecheck()
            # seed特定
            restored = self.restore_baseseed()
            # id検索の実行
            result = self.search_id(restored)
            if result is not None:break

            # メニューに戻る->ゲーム終了
            self.press(Button.HOME, wait=0.5)
            self.press(Button.X, wait=0.5)
            self.press(Button.A, wait=1.5)

        target_idx, tid, sid, g7tid = result
        idx = 0
        remains = target_idx - idx

        reidentified_rng = None
        last_blink = 0.0

        # 自動消費
        while True:
            # seed再特定
            idx, reidentified_rng, last_blink = self.reidentify_advance(restored)
            remains = target_idx - idx
            # この時点で残り消費数が0未満なら失敗
            if remains<0:
                print("Woops. something went wrong...")
                return
            # 残り消費数が少ないならループ離脱
            is_finished = (remains - 15) // 6 == 0 or remains < 15
            if is_finished:break

            # キャンセル回数決定
            cancel_times = (remains - 15) // 6 #残り消費数 / 6 で見積り
            print(f"cancel name entry {cancel_times} time(s)")
            # キャンセルによる乱数消費
            for _ in range(cancel_times): self.advance_seed()

        # timeline生成準備
        waituntil = last_blink + blink_pokemon(reidentified_rng)
        remains -= 1

        # timeline生成開始
        while remains > 0:
            next_time = waituntil - time.perf_counter() or 0
            self.wait(next_time)

            remains -= 1
            interval = blink_pokemon(reidentified_rng)
            waituntil += interval
            print(f"remains:{remains}, interval:{interval:.3f}")

        # 名前確認画面からスタート
        self.press(Button.B, wait=2.0)
        
        # 顔写真選択(WIP)
        self.press(Button.A, wait=1.0)
        print("Completed.")
        print(f"g7tid:{g7tid}, tid:{tid}, sid:{sid}")
        # ホームに戻る
        self.press(Button.HOME)
        

    def menu2namecheck(self):
        print("launch game")
        # ゲーム選択
        self.press(Button.A, wait=1.2)
        # ユーザー選択
        self.press(Button.A, wait=25)
        #(暗転)

        # 言語選択(WIP)
        self.press(Button.A, wait=2.0)
        self.press(Button.A, wait=2.0)
        self.press(Button.A, wait=2.0)

        # キーボード画面を検知するまで連打
        print("mash A until poke-con detect keyboard window")
        for _ in range(30): self.press(Button.A, wait=0.1)
        while True:
            self.press(Button.A, wait=0.3)
            # 画像取得
            img = cv2.cvtColor(self.camera.readFrame(),cv2.COLOR_BGR2GRAY)
            keyboardimg = img[650:700, 400:450]
            # 輝度(グレースケール)の最大値を取る
            value = np.max(keyboardimg)
            if value < 100:
                break

        self.press(Button.A, wait=0.3)
        self.press(Button.PLUS, wait=1.0)

    def advance_seed(self):
        # 名前確認画面からスタート
        self.press(Button.B, wait=1.2)
        # 顔写真選択
        self.press(Button.A, wait=1.3)
        # OSキーボード
        self.press(Button.A, wait=0.2)
        self.press(Button.PLUS, wait=0.8)
        self.press(Button.B, wait=0.5)

    def search_id(self, rng):#->(i, tid, sid, g7tid)

        target_g7tid_set = set(target_g7tid_list)
        target_tidsid_set = tidsid_list2set(target_tidsid_list) #(tid, sid)

        # 目的のidが直近にあるか検索
        rand = rng.deepcopy()
        tidsid, g7tid = 0, 0

        # 最初の50個はスキップ
        for i in range(50): tidsid, g7tid = generate_id(rand)

        for i in range(50, self.SEARCHMAX):
            tidsid, g7tid = generate_id(rand)
            if (g7tid in target_g7tid_set) or (tidsid in target_tidsid_set):
                # ロギング
                print("Found!")
                tid,sid = tidsid&0xFFFF, tidsid>>16
                print(f"advances:{i}, g7tid:{g7tid}, tid:{tid}, sid:{sid}")
                return (i, tid, sid, g7tid)

        # 見つからなかったらNone(未発見)を返す
        print("Not found...")
        return None

    def observe_blink_interval(self)->float:
        # 閾値
        THRESHOLD = 0.7
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
            eyeimg = img[460:480, 500:510]
            # 瞬き検知
            eyevalue = np.mean(eyeimg) / 255.0
            is_blinking = eyevalue < THRESHOLD

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

    def reidentify_advance(self, rng:Xorshift)->Tuple[int, float]:
        # RNG回りの何か
        searcher = MunchlaxLinearSearch()
        restored = None

        for interval, current_time in self.observe_blink_interval():
            # 瞬き間隔を復元器に投入
            searcher.add_interval(interval)
            print(f"blinked! interval:{interval:.3f}")
            if len(searcher.intervals) >= 7:
                # 既定回数以上観測したなら再特定を試みる
                restored = searcher.search(rng, self.SEARCHMAX, epsilon=0.5).__next__()
                # 結果が得られたならループ離脱
                if restored is not None:
                    # 現在のadvanceを表示
                    print()
                    print(f"current advance: {restored[0]}")
                    return restored[0], restored[1], current_time
                else:
                    searcher.reset()

    def restore_baseseed(self)->Xorshift:
        # RNG回りの何か
        inverter = MunchlaxInverter(eps = EPSILON)
        restored = None

        for interval, _ in self.observe_blink_interval():
            # 瞬き間隔を復元器に投入
            inverter.add_interval(interval)
            print(f"blinked! entropy:{inverter.entropy} interval:{interval:.3f}")
            # 復元を試みる
            restored = inverter.try_restore_state()
            # 復元結果が得られたならループ離脱
            if restored is not None:
                # 復元された乱数生成器の内部状態を表示
                print()
                print(f"restored: {[hex(s_i).upper() for s_i in restored.get_state()]}")
                print(f"blink: {inverter.blinkcount} times")
                return restored


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