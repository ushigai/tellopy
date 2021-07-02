"""
写真を撮影し、顔認識を行うプログラム
顔認識本体はHaar Cascadeで殴ってる
実行する場合はモジュールの`setup_tello()`内の`cascade_path`を書き換えてほしい
self.cascade_path = "(自分のPythonの保存先)/Lib/site-packages/cv2/data/haarcascade_frontalface_default.xml"
↑こんな感じにしてもろて
"""

import ushigai.pytello
from time import sleep

tello = ushigai.pytello.PYtello()

tello.setup_tello()

for i in range(3):
    print(3 - i)
    sleep(1.0)

print("ぱしゃ")

for i in range(20):
    try:
        L = tello.face_detection()
        going = len(L) == 1
        if going:
            print("顔がある！")
            going = False
        else:
            print("顔がない！")
        sleep(2.0)
    except:
        break

tello.close_tello()
