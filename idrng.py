# このコードはMITライセンスに準拠します 
# 良く分からんと言う人:以下のライセンス表記を消さなければご自由にお使い頂いて構いません. 
# 但し, 以下のコードを利用したことによる責任は一切負いかねます. 自己責任でお願いします.
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

import cv2
import numpy as np

from Commands.PythonCommandBase import  ImageProcPythonCommand
from Commands.Keys import KeyPress, Button, Direction, Stick, Hat

from .bdsprnglib.starterrng import MunchlaxInverter
from .bdsprnglib.rng import Xorshift

import time
 
class IDRNG(ImageProcPythonCommand):
    NAME = 'BDSP_ID調整'
 
    def __init__(self, cam):
        super().__init__(cam)
 
    def do(self):
        # 黒魔術
        self.camera.camera.set(cv2.CAP_PROP_BUFFERSIZE,1)
        
        # 閾値
        THRESHOLD = 0.7
        # タイマー用変数
        current_time = time.perf_counter()
        # 前回の瞬き時間
        prev_blink_time = 0
        # 瞬き中かを判別する
        is_blinked = False        
        # 周波数
        freq = 30

        # RNG回りの何か
        inverter = MunchlaxInverter()
        restored = None

        while True:
            #ビジーウェイトでタイマー構築
            self.wait(0.01)
            """
            current_time = current_time + 1.0/freq
            while time.perf_counter() < current_time + 1.0/freq:
                pass
            """

            # 画像取得
            img = cv2.cvtColor(self.camera.readFrame(),cv2.COLOR_BGR2GRAY)
            eyeimg = img[460:480, 500:510]
            current_time = time.perf_counter()
            
            # 瞬き検知
            eyevalue = np.mean(eyeimg) / 255.0
            is_blinking = eyevalue < THRESHOLD
            
            if is_blinking and not is_blinked:
                # 瞬き間隔の測定
                interval = current_time - prev_blink_time
                if prev_blink_time != 0:
                    # メッセージの表示
                    print(f"blinked! {interval} s")
                    # 瞬き間隔を復元器に投入
                    inverter.add_interval(interval)
                    restored = inverter.try_restore_state()
                    # 復元結果が得られたならループ離脱
                    if restored is not None:
                        break
                prev_blink_time = current_time

            is_blinked = is_blinking

        # 復元された乱数生成器の内部状態を表示して終了
        print()
        print(f"restored: {[hex(s_i).upper() for s_i in restored.get_state()]}")
        print(f"blink: {inverter.blinkcount} times")

            