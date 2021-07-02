import ushigai.pytello
from time import *

tello = ushigai.pytello.PYtello()

tello.setup_tello()

# sleep(20)
"""
for i in range(1):
    print(str(i) * 1000)
    tello.take_picture()
    sleep(1)
"""

for i in range(50):
    tello.take_picture()

tello.query()
tello.close_tello()
