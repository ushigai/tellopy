import ushigai.pytello
from time import sleep

tello = ushigai.pytello.PYtello()
tello.setup_tello()

width, height = 960, 720


#tello.go_tello("TAKEOFF")
#tello.go_tello("up (身長に合わせて調整して)")

for _ in range(40):
    try:
        res = tello.face_detection() 
        print(res)
        if len(res) != 1:
            print("NONE << Tello")
            sleep(1)
            continue
        x, y, w, h = res[0]
        if w > 200:
            print("back")
            #tello.go_tello("back 30")
        if w < 150:
            print("forward")
            #tello.go_tello("forward 30")
        if y + h / 2 > height / 2 + 200:
            print("down")
            #tello.go_tello("down 30")
        if y + h / 2 < height / 2 - 200:
            print("up")
            #tello.go_tello("up 30")
        if x + w / 2 > width / 2 + 200:
            print("right")
            #tello.go_tello("right 30")
        if x + w / 2 < width / 2 - 200:
            print("left")
            #tello.go_tello("left 30")
        sleep(1)
    except:
        break

tello.close_tello()
