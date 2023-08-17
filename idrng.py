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

SEARCHMAX = 100000 #検索数上限
target_g7tid_list = [] # 先頭に0を付けない整数で格納してください. 例: 000827 -> target_g7tid_list = [827]
target_tidsid_list = [] # 先頭に0を付けない整数のタプルで格納してください.  例: tidが01234, sidが56789なら, target_tidsid_list = [(1234, 56789)] 


def tidsid_list2set(tidsid_list):
    return set([(sid<<16) ^ tid  for (tid, sid) in tidsid_list])

class IDRNG(ImageProcPythonCommand):
    NAME = 'BDSP_ID調整'
 
    def __init__(self, cam):
        super().__init__(cam)
 
    def do(self):
        # 黒魔術
        self.camera.camera.set(cv2.CAP_PROP_BUFFERSIZE,1)

        # コントローラー入力チェック
        for _ in range(5): self.press(Button.B, wait=0.1)
        
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
        reidentified_rng = None
        last_blink = 0.0

        remains = target_idx - idx

        while True:
            # seed再特定
            idx, reidentified_rng, last_blink = self.reidentify_advance(restored)
            remains = target_idx - idx
            # 残り消費数が少ないならループ離脱
            is_finished = (remains - 15) // 7 == 0
            if is_finished:break

            # キャンセル回数決定
            cancel_times = (remains - 15) // 7 #残り消費数 / 7 で見積り
            print(f"cancel name entry {cancel_times} time(s)")
            # キャンセルによる乱数消費
            for _ in range(cancel_times): self.advance_seed()
        
        # この時点で残り消費数が0未満なら失敗
        if remains<0:
            print("Woops. something wrong...")
            return

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
        # ホームに戻る
        self.press(Button.HOME)
        

    def menu2namecheck(self):
        print("launch game")
        # ゲーム選択
        self.press(Button.A, wait=1.2)
        # ユーザー選択
        self.press(Button.A, wait=32)
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
        self.press(Button.PLUS, wait=3.0)

    def advance_seed(self):
        # 名前確認画面からスタート
        self.press(Button.B, wait=1.2)
        # 顔写真選択
        self.press(Button.A, wait=1.0)
        # OSキーボード
        self.press(Button.A, wait=0.2)
        self.press(Button.PLUS, wait=0.8)
        self.press(Button.B, wait=0.3)

    def search_id(self, rng):#->(i, tid, sid, g7tid)

        target_g7tid_set = set(target_g7tid_list)
        target_tidsid_set = tidsid_list2set(target_tidsid_list) #(tid, sid)

        # 目的のidが直近にあるか検索
        rand = rng.deepcopy()
        tidsid, g7tid = 0, 0

        # 最初の50個はスキップ
        for i in range(50): tidsid, g7tid = generate_id(rand)

        for i in range(50, SEARCHMAX):
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

    def reidentify_advance(self, rng:Xorshift)->Tuple[int, float]:
        # 閾値
        THRESHOLD = 0.7
        # タイマー用変数
        current_time = time.perf_counter()
        # 前回の瞬き時間
        prev_blink_time = 0
        # 瞬き中かを判別する
        is_blinked = False        

        # RNG回りの何か
        searcher = MunchlaxLinearSearch()
        restored = None

        print("start observation")
        while True:
            self.wait(0.01)

            # 画像取得
            img = cv2.cvtColor(self.camera.readFrame(), cv2.COLOR_BGR2GRAY)
            eyeimg = img[460:480, 500:510]
            
            # 瞬き検知
            eyevalue = np.mean(eyeimg) / 255.0
            is_blinking = eyevalue < THRESHOLD

            # 現在時刻取得
            current_time = time.perf_counter()
            
            if is_blinking and not is_blinked:
                # 瞬き間隔の測定
                interval = current_time - prev_blink_time
                if prev_blink_time != 0:
                    # 瞬き間隔を復元器に投入
                    searcher.add_interval(interval)
                    # メッセージの表示
                    print(f"blinked! interval:{interval:.3f}")
                    # 再特定を試みる
                    restored = None
                    if len(searcher.intervals)>=4:
                        restored = searcher.search(rng, SEARCHMAX).__next__()
                    # 結果が得られたならループ離脱
                    if restored is not None:
                        # 現在のadvanceを表示
                        print()
                        print(f"current advance: {restored[0]}")
                        return restored[0], restored[1], current_time

                prev_blink_time = current_time

            is_blinked = is_blinking

    def restore_baseseed(self)->Xorshift:
        # 閾値
        THRESHOLD = 0.7
        # タイマー用変数
        current_time = time.perf_counter()
        # 前回の瞬き時間
        prev_blink_time = 0
        # 瞬き中かを判別する
        is_blinked = False        

        # RNG回りの何か
        inverter = MunchlaxInverter()
        restored = None

        print("start observation")
        while True:
            self.wait(0.01)

            # 画像取得
            img = cv2.cvtColor(self.camera.readFrame(),cv2.COLOR_BGR2GRAY)
            eyeimg = img[460:480, 500:510]
            
            # 瞬き検知
            eyevalue = np.mean(eyeimg) / 255.0
            is_blinking = eyevalue < THRESHOLD

            # 現在時刻取得
            current_time = time.perf_counter()
            
            if is_blinking and not is_blinked:
                # 瞬き間隔の測定
                interval = current_time - prev_blink_time
                if prev_blink_time != 0:
                    # 瞬き間隔を復元器に投入
                    inverter.add_interval(interval)
                    # メッセージの表示
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
                prev_blink_time = current_time

            is_blinked = is_blinking

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