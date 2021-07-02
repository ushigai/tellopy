import ushigai.pytello

tello = ushigai.pytello.PYtello()

tello.setup_tello()

tello.go_tello("TAKEOFF")
tello.go_tello("LAND")

tello.close_tello()
