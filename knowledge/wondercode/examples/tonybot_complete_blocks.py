import Hiwonder
import time
import Hiwonder_IIC
from Hiwonder_BLE import BLE


tonybot = Hiwonder.Tonybot()
beep = Hiwonder.Buzzer()
i2c = Hiwonder_IIC.IIC()
imu = Hiwonder_IIC.MPU()
ble = BLE(BLE.MODE_BLE_SLAVE, "Tonybot")
uart = Hiwonder.UART(9600, 2, 5)


def start_main():
    global tonybot
    global beep
    global i2c
    global imu
    global ble
    global uart

    tonybot.attachHead()
    tonybot.detachHead()
    tonybot.moveHeadAngle(90)
    tonybot.moveServo(1, 500, 100)
    tonybot.runActionGroup(1, 1)
    tonybot.stopActionGroup()
    tonybot.setActionGroupSpeed(1, 100)
    tonybot.setAllActionGroupSpeed(100)
    tonybot.runActionGroup(tonybot.isRunning(), 1)
    tonybot.waitForStop(100)

    print("Hello")
    time.sleep(0.5)
    print(60)
    time.sleep(0.5)
    print(tonybot.getBatteryVolt(100))
    time.sleep(0.5)

    beep.playTone(65, 500, False)
    beep.playTone(65, 500, False)
    beep.setVolume(100)
    beep.setVolume(imu.read_gyro_data()[0])
    beep.setVolume(imu.read_angle()[0])

    ble.send_data("CMD")
    ble.send_data(ble.parse_uart_cmd("0")[0])
    ble.send_data(ble.parse_uart_cmd("0")[1])

    uart.send_data("CMD")
    uart.send_data(uart.has_data())
    uart.send_data(uart.contains_data("CMD"))
    uart.send_data(uart.read_buffer())
    uart.send_data(uart.read_uart_cmd())
    uart.send_data(uart.parse_uart_cmd("0")[1])
    uart.send_data(uart.parse_uart_cmd("0")[0])
    uart.clear_buffer()


Hiwonder.startMain(start_main)
