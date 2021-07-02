import ushigai.pytello
from time import sleep

tello = ushigai.pytello.PYtello()

tello.setup_tello()

for i in range(5):
    print(5 - i)
    sleep(1)

for _ in range(10):
    tello.take_picture()  # 引数なしで実行してみる
    sleep(0.5)

tello.take_picture("hogehgoe")  # 引数あり(ファイル名を指定して)実行してみる
sleep(1.0)
tello.take_picture("hugahuga")
sleep(1.0)

tello.close_tello()
