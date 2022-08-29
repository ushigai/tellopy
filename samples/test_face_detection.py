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
