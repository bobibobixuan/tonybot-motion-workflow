import Hiwonder
import time


tonybot = Hiwonder.Tonybot()
beep = Hiwonder.Buzzer()


def start_main():
    global tonybot
    global beep

    tonybot.attachHead()
    tonybot.moveHeadAngle(90)
    time.sleep(0.5)

    tonybot.runActionGroup(0, 1)
    tonybot.waitForStop(3000)

    tonybot.runActionGroup(49, 2)
    tonybot.waitForStop(5000)

    tonybot.runActionGroup(50, 2)
    tonybot.waitForStop(5000)

    tonybot.runActionGroup(9, 2)
    tonybot.waitForStop(5000)

    beep.playTone(65, 300, False)
    time.sleep(0.3)
    beep.playTone(72, 300, False)
    time.sleep(0.3)

    tonybot.runActionGroup(10, 1)
    tonybot.waitForStop(3000)

    tonybot.runActionGroup(0, 1)
    tonybot.waitForStop(3000)


Hiwonder.startMain(start_main)
