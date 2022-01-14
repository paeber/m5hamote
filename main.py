##################################################
## M5Hamote - A HomeAssistant remote on M5Paper
##################################################
## Author: @paeber
## Github: https://github.com/paeber/m5paper-homeassistant-remote
## Copyright: Copyright 2021, PaEber Electronics
## Version: 0.0.1
## Status: alpha
##################################################

from m5stack import *
from m5ui import *
from uiflow import *
from m5stack import touch
import wifiCfg
from m5mqtt import M5mqtt
import json
import time

from HomeAssistant import HomeAssistant
import M5PaperUI

setScreenColor(15)
lblLog = M5TextBox(10, 910, "-", lcd.FONT_DejaVu40, 0, rotate=0)

def setLogMessage(text):
    # Show text in bottom left corner for debug and status purposes
    lblLog.setText(str(text))
    lcd.partial_show(0, 900, 300, 60)

class dotdict(dict):
    """
    dot.notation access to dictionary attributes
    https://stackoverflow.com/questions/2352181/how-to-use-a-dot-to-access-members-of-dictionary
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


setLogMessage("Boot")
print("Wait 10 sec")
wait(10)
print("----- Start init ------")

setLogMessage("Load config")

DeviceState = {'v_bat': 0}
touchNow = None
touchOld = None

f = open('secrets.json')
HamoteConfig = json.loads(f.read())
f.close()

# Setup connections and services
setLogMessage("Connect to " + HamoteConfig['wifi']['ssid'])
wifiCfg.doConnect(HamoteConfig['wifi']['ssid'], HamoteConfig['wifi']['pw'])
while not wifiCfg.wlan_sta.isconnected():
  pass

setLogMessage("Setup services")
Services = dotdict()
Services.HomeServer = HomeAssistant(HamoteConfig['hassio']['url'], HamoteConfig['hassio']['token'])
Services.MqttServer = M5mqtt('m5paper-homeremote', HamoteConfig['mqtt']['url'], 1883, HamoteConfig['mqtt']['usr'], HamoteConfig['mqtt']['pw'], 300)
Services.Config = HamoteConfig

def syncRtcFromHomeAssistant():
    weekday = 6
    date_time = Services.HomeServer.getState("sensor.date_time")
    date, time = date_time.split(", ")
    date = date.split("-")
    time = time.split(":")
    rtc.set_datetime((int(date[0]), int(date[1]), int(date[2]), weekday, int(time[0]), int(time[1]), 0))
    setLogMessage(Services.HomeServer.getState("Time updated"))

# Additional UI Element *to be simplified*
rectHeader = M5Rect(0, 80, 540, 5, 0, 0)
lblScreenName = M5TextBox(10, 10, "Office", lcd.FONT_DejaVu72, 0, rotate=0)
lblTime = M5TextBox(420, 10, "23:45", lcd.FONT_DejaVu40, 0, rotate=0)
rectTopBox = M5Rect(20, 120, 500, 150, 15, 0)
lineTopBox = M5Line(M5Line.PLINE, 350, 120, 350, 270, 0)
lblBattery = M5TextBox(429, 234, "3.75V", lcd.FONT_DejaVu24, 0, rotate=0)
imgTemp = M5Img(468, 125, "res/temp.jpg", True)
lblTemp = M5TextBox(374, 135, "23.4", lcd.FONT_DejaVu40, 0, rotate=0)
lblHumidity = M5TextBox(374, 185, "43%", lcd.FONT_DejaVu40, 0, rotate=0)
imgHumidity = M5Img(468, 175, "res/water-pct.png", True)
rectBottom = M5Rect(0, 840, 540, 5, 0, 0)
imgLeft = M5Img(340, 850, "res/left_2x.png", True)
imgRight = M5Img(445, 850, "res/right_2x.png", True)


# UI Elements based on M5PaperUI objects
ToggleButtons = [
    M5PaperUI.Light("light.pcb_backlight", (20, 290), Services),
    M5PaperUI.Light("light.monitor_riser", (190, 290), Services),
    M5PaperUI.Light("switch.office_spots", (360, 290), Services),
    M5PaperUI.Light("light.buro_decke", (20, 460), Services),
    M5PaperUI.MediaPlayer("media_player.schreibtisch", (20, 660), Services)
]


# Update information in head section of the screen
def HeadHandler():
    global DeviceState
    hours = str(rtc.datetime()[4])
    minutes = str(rtc.datetime()[5])
    if len(minutes) == 1:
        minutes = "0" + minutes
    lblTime.setText(str(hours + ':' + minutes))
    lcd.partial_show(410, 0, 150, 80)

# Execute M5Paper relevant hardware tasks
def DeviceHandler():
    global DeviceState
    lblBattery.setText(str((str(("%.2f" % ((bat.voltage()) / 1000))) + str('V'))))
    lcd.partial_show(350, 120, 170, 150)

# Callbacks for M5Paper button wheel
def buttonUP_wasPressed():
    lcd.show()
    pass
btnUP.wasPressed(buttonUP_wasPressed)


@timerSch.event('touch')
def ttouch():
    global touchNow, touchOld
    touchNow = touch.read()
    if touchNow[3] != touchOld:
        if touchNow[3]:
            print("Touch:", (touchNow[0], touchNow[1]))
            for element in ToggleButtons:
                element.scheduler((touchNow[0], touchNow[1]))
    touchOld = touchNow[3]


@timerSch.event('deviceManager')
def tdeviceManager():
    global DeviceState
    HeadHandler()


@timerSch.event('HardwareManager')
def tHardwareManager():
    global DeviceState
    DeviceHandler()


#syncRtcFromHomeAssistant()

Services.MqttServer.start()
lcd.show()

timerSch.run('touch', 40, 0x00)
timerSch.run('deviceManager', 10000, 0x00)
timerSch.run('HardwareManager', 1000, 0x00)

setLogMessage("Ready")

