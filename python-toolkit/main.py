# Hiwonder Tonybot
# MicroPython - APP Bluetooth control

import Hiwonder, Hiwonder_IIC, time, machine
from Hiwonder_BLE import BLE

tonybot = Hiwonder.Tonybot()
ble = BLE(BLE.MODE_BLE_SLAVE,"Tonybot_{:02X}".format(machine.unique_id()[5]))
i2c = Hiwonder_IIC.IIC()
i2csonar = Hiwonder_IIC.I2CSonar(i2c)

i2csonar.setRGB(0,0x00,0xF0,0x00)
tonybot.moveHeadAngle(90)
tonybot.runActionGroup(0,1)
time.sleep(1.5)

status_motion = 0 # 要运动的状态
status_action = 0xFF # 要运行的动作组
status_func = 0 # 要运行的玩法

actfirst = 18 
actgo = 21 
actback = 22 
actleftskate = 11 
actrightskate = 12 
actturnleft = 23 
actturnright = 24 
actstandquickly = 19 
action_list = [actfirst , actgo , actback , actleftskate , actrightskate , actturnleft , actturnright]

MIN_DISTANCE_TURN = 200 # 距离阈值
BIAS = 0 # 舵机偏差

_obs_step = 0
gDistance = 0
gLDistance = 0
gRDistance = 0
have_move = False
lastActionIsGoBack = False
_walk_step = 0
battery_volt = 0
l_stop = False
r_stop = False

def ble_receive():
  global status_motion , status_action , status_func
  global battery_volt , l_stop , r_stop

  ble_rec_data = 0
  rec_parse_value = 0
  while True:
    if ble.is_connected():
      if ble.contains_data("CMD"):
        ble_rec_data = ble.read_uart_cmd()
        if not ble_rec_data:
          continue
        rec_parse_value = ble.parse_uart_cmd(ble_rec_data)
        _COMMAND = rec_parse_value[0]
        _COMMAND = int(_COMMAND)
        if(_COMMAND == 1 and len(rec_parse_value) == 2):
          cmd = int(rec_parse_value[1])
          if(cmd == 8):
            l_stop = True
          elif(cmd == 9):
            r_stop = True
          elif(cmd in [1,2,3,4]):
            l_stop = False
          elif(cmd in [5,6]):
            r_stop = False
          status_motion = cmd
        elif(_COMMAND == 2 and len(rec_parse_value) == 2):
          status_action = int(rec_parse_value[1])
        elif(_COMMAND == 3):
          if(int(rec_parse_value[1]) == 1): # 测距发送
            _distance = int(i2csonar.getDistance()*10)
            _distance = _distance if _distance < 500 else 500
            _senddata = "CMD|3|{}|$".format(_distance)
            ble.send_data(_senddata)
          elif(int(rec_parse_value[1]) == 2 and len(rec_parse_value) == 5): # 超声波RGB设置
            i2csonar.setRGB(0,int(rec_parse_value[2]),int(rec_parse_value[3]),int(rec_parse_value[4]))
        elif(_COMMAND == 4 and len(rec_parse_value) == 2): # 玩法功能
          if(int(rec_parse_value[1]) == 1): # 避障
            status_func = 1
          elif(int(rec_parse_value[1]) == 2): # 定距跟随
            status_func = 2
          elif(int(rec_parse_value[1]) == 0): # 关闭当前功能
            status_func = 0
        elif(_COMMAND == 5): # 电池电量
          # tmp = tonybot.getBatteryVolt(40)
          # if(tmp != -1):
            # battery_volt  = tmp
          _senddata = "CMD|5|{}|$".format(battery_volt)
          ble.send_data(_senddata)
    else:
        time.sleep(0.03)

def action_run():
  global status_motion, status_action, status_func
  global _obs_step , _walk_step , l_stop , r_stop , battery_volt
  step = 0
  tmp_action = 0
  flag_first_obs = True
  flag_first_walk = True
  last_time = 0
  last_time_2 = 0
  
  while True:
    if(last_time < time.ticks_ms()):
      last_time = time.ticks_ms() + 1000
      tonybot.sendCMDGetBatteryVolt()

    if(step == 0):
      if(status_motion in [1,2,3,4,5,6]):
        tmp_action = status_motion
        step = 2
      elif(status_action != 0xFF):
        tmp_action = status_action
        status_action = 0xFF
        step = 3
      elif(status_func == 1):
        flag_first_obs = True
        step = 4
      elif(status_func == 2):
        flag_first_walk = True
        step = 5
      else:
        time.sleep(0.05)
    
    # elif(step == 1): # 运动控制
      # tonybot.runActionGroup(action_list[tmp_action],0)
      # step = 2
    
    elif(step == 2): # 等待运动控制结束
      if(tmp_action in [1,2,3,4]):
        if(status_motion != tmp_action or l_stop == True): #status_motion != 9):
          if(tmp_action in [1,2]):
            tonybot.runActionGroup(19,1)
            time.sleep(0.52)
          tmp_action = 0
          step = 0
          continue
        if(tmp_action == 1):
          tonybot.runActionGroup(action_list[tmp_action],1)
          time.sleep(1.27)
        elif(tmp_action == 2):
          tonybot.runActionGroup(action_list[tmp_action],1)
          time.sleep(1.65)
        else:
          tonybot.runActionGroup(action_list[tmp_action],1)
          # tonybot.waitForStop(2000)
          time.sleep(0.65)
      else:
        if(status_motion != tmp_action or r_stop == True): #status_motion != 8):
          tmp_action = 0
          step = 0
          continue
        tonybot.runActionGroup(action_list[tmp_action],1)
        tonybot.waitForStop(2000)

    elif(step == 3): # 动作组
      tonybot.runActionGroup(tmp_action,1)
      tonybot.waitForStop(2000)
      tmp_action = 0
      step = 0
    
    elif(step == 4): # 超声波避障
      if(flag_first_obs):
        flag_first_obs = False
        tonybot.moveHeadAngle(90)
        _obs_step = 0
        tonybot.runActionGroup(0 , 1)
        tonybot.waitForStop(2000)
      if(status_func == 0):
        tonybot.stopActionGroup()
        tonybot.waitForStop(1000)
        tonybot.runActionGroup(0 , 1)
        tonybot.moveHeadAngle(90)
        tonybot.waitForStop(2000)
        step = 0
        continue
      obstacleAvoidance()
      time.sleep(0.05)
    
    elif(step == 5): # 定居行走
      if(flag_first_walk):
        flag_first_walk = False
        i2csonar.setRGB(0,0x00,0x00,0xF0)
        _walk_step = 0
        tonybot.runActionGroup(0 , 1)
        tonybot.waitForStop(2000)
      if(status_func == 0):
        i2csonar.setRGB(0,0x00,0xF0,0x00)
        tonybot.stopActionGroup()
        tonybot.waitForStop(1000)
        tonybot.runActionGroup(0 , 1)
        tonybot.waitForStop(2000)
        step = 0
        continue
      Distancewalking()
      time.sleep(0.05)
    else:
      step = 0
    
    if(last_time_2 < time.ticks_ms()):
      last_time_2 = time.ticks_ms() + 900
      tmp = tonybot.getBatteryVolt()
      if(tmp != -1):
        battery_volt  = tmp

def getAllDistance():
    global gDistance, gLDistance, gRDistance
    i2csonar.setRGB(0, 0, 50, 50)
    tonybot.moveHeadAngle(90 + BIAS)
    time.sleep(0.2)
    gDistance = i2csonar.getDistance() * 10
    tonybot.moveHeadAngle(145 + BIAS)
    time.sleep(0.4)
    tDistance = i2csonar.getDistance() * 10
    tonybot.moveHeadAngle(180 + BIAS)
    time.sleep(0.4)
    gLDistance = i2csonar.getDistance() * 10
    if tDistance < gLDistance:
      gLDistance = tDistance
    tonybot.moveHeadAngle(45 + BIAS)
    time.sleep(0.6)
    tDistance = i2csonar.getDistance() * 10
    tonybot.moveHeadAngle(0 + BIAS)
    time.sleep(0.4)
    gRDistance = i2csonar.getDistance() * 10
    if tDistance < gRDistance:
      gRDistance = tDistance
    tonybot.moveHeadAngle(90 + BIAS)
    time.sleep(0.4)

def obstacleAvoidance():
    global gDistance, gLDistance, gRDistance
    global _obs_step, have_move, lastActionIsGoBack
    Distance = i2csonar.getDistance() * 10
    if _obs_step == 0:
        gDistance = Distance
        if gDistance >= MIN_DISTANCE_TURN or gDistance == 0:
            if not tonybot.isRunning():
                i2csonar.setRGB(0, 0, 50, 0)
                tonybot.runActionGroup(actfirst, 1)
                tonybot.waitForStop(2000)
                tonybot.runActionGroup(actgo, 0)
                have_move = True
                _obs_step = 1
        else:
            _obs_step = 2
    elif _obs_step == 1:
        gDistance = Distance
        if gDistance < MIN_DISTANCE_TURN and gDistance > 0:
            tonybot.runActionGroup(actgo, 1)
            tonybot.waitForStop(2000)
            tonybot.runActionGroup(actfirst, 1)
            tonybot.waitForStop(2000)
            tonybot.runActionGroup(actstandquickly, 1)
            _obs_step = 2
    elif _obs_step == 2:
        if not tonybot.isRunning():
            getAllDistance()
            _obs_step = 3
    elif _obs_step == 3:
        i2csonar.setRGB(0, 0, 0, 50)
        if ((gDistance > MIN_DISTANCE_TURN) or (gDistance == 0)) and not lastActionIsGoBack:
            _obs_step = 0
            lastActionIsGoBack = False
            return
        if ((gLDistance > gRDistance and gLDistance > MIN_DISTANCE_TURN) or gLDistance == 0) and gDistance > 50:
            if have_move:
                tonybot.runActionGroup(36, 1)
                tonybot.waitForStop(1000)
            tonybot.runActionGroup(actturnleft, 4)
            lastActionIsGoBack = False
            _obs_step = 2
        elif ((gRDistance > gLDistance and gRDistance > MIN_DISTANCE_TURN) or gRDistance == 0) and gDistance > 50:
            if have_move:
                tonybot.runActionGroup(37, 1)
                tonybot.waitForStop(1000)
            tonybot.runActionGroup(actturnright, 4)
            lastActionIsGoBack = False
            _obs_step = 2
        else:
            tonybot.runActionGroup(actfirst, 1)
            tonybot.waitForStop(2000)
            tonybot.runActionGroup(actback, 2)
            tonybot.waitForStop(4000)
            tonybot.runActionGroup(actfirst, 1)
            tonybot.waitForStop(2000)
            tonybot.runActionGroup(actstandquickly, 1)
            lastActionIsGoBack = True
            _obs_step = 2
        have_move = False

def Distancewalking():
    global _walk_step, have_move
    Distance = i2csonar.getDistance() * 10
    if _walk_step == 0:
        if 30 < Distance < 180:
            i2csonar.setRGB(0, 50, 0, 0)
            tonybot.runActionGroup(actfirst, 1)
            tonybot.waitForStop(1000)
            have_move = True
            _walk_step = 1
        elif 300 < Distance < 400:  # 亮绿灯，执行过渡动作
            i2csonar.setRGB(0, 0, 50, 0)
            tonybot.runActionGroup(actfirst, 1)
            tonybot.waitForStop(1000)
            have_move = True
            _walk_step = 2
        elif have_move:
            _walk_step = 3
        else:
            i2csonar.setRGB(0, 0, 0, 50)
    elif _walk_step == 1:
        if (30 < Distance < 180) or have_move:
            have_move = False
            tonybot.runActionGroup(actback, 1)
            tonybot.waitForStop(2000)
        else:
            _walk_step = 3
    elif _walk_step == 2:
        if (300 < Distance < 400) or have_move:
            have_move = False
            tonybot.runActionGroup(actgo, 1)
            tonybot.waitForStop(2000)
        else:
            _walk_step = 3
    elif _walk_step == 3:
      tonybot.runActionGroup(actfirst, 1)
      tonybot.waitForStop(2000)
      tonybot.runActionGroup(actstandquickly, 1)
      i2csonar.setRGB(0, 0, 0, 50)
      tonybot.waitForStop(1000)
      have_move = False
      _walk_step = 0

Hiwonder.startMain(ble_receive)
Hiwonder.startMain(action_run)


