import Hiwonder
import time


tonybot = Hiwonder.Tonybot()


def start_main():
    global tonybot

    tonybot.runActionGroup(0, 1)
    tonybot.waitForStop(3000)
    time.sleep(0.5)

    # 159 号是假定已经由 python-toolkit 生成并部署到设备上的自定义动作组。
    tonybot.runActionGroup(159, 1)
    tonybot.waitForStop(20000)

    tonybot.runActionGroup(10, 1)
    tonybot.waitForStop(3000)

    tonybot.runActionGroup(0, 1)
    tonybot.waitForStop(3000)


Hiwonder.startMain(start_main)
