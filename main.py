from m5stack import *
from m5ui import *
from uiflow import *
from m5stack import touch
import wifiCfg
from m5mqtt import M5mqtt
import json

from HomeAssistant import HomeAssistant

setScreenColor(15)
lblLog = M5TextBox(10, 910, "-", lcd.FONT_DejaVu40, 0, rotate=0)

def setLogMessage(text):
    lblLog.setText(str(text))
    lcd.partial_show(0, 900, 300, 60)

setLogMessage("Load config")

DeviceState = {'time': False, 'v_bat': 0}
touchNow = None
touchOld = None

f = open('secrets.json')
M5Config = json.loads(f.read())
f.close()

# Setup connections and services
setLogMessage("Connect to " + M5Config['wifi']['ssid'])
wifiCfg.doConnect(M5Config['wifi']['ssid'], M5Config['wifi']['pw'])
while not wifiCfg.wlan_sta.isconnected():
  pass
setLogMessage("Connected")

HomeServer = HomeAssistant(M5Config['hassio']['url'], M5Config['hassio']['token'])
m5mqtt = M5mqtt('m5paper-homeremote', M5Config['mqtt']['url'], 1883, M5Config['mqtt']['usr'], M5Config['mqtt']['pw'], 300)
statestream_base_topic = M5Config['mqtt']['base_topic']

class IconButton:
    def __init__(self, icon, position, size):
        self.pos = position
        self.size = size
        self.icon = M5Img(self.pos[0], self.pos[1], icon, True)

    def isPressed(self, touch):
        if (((self.pos[0]) <= touch[0]) and (touch[0] <= (self.pos[0] + self.size[0]))):
            if (((self.pos[1]) <= touch[1]) and (touch[1] <= (self.pos[1] + self.size[1]))):
                return True
        return False

    def changeImg(self, newIcon):
        self.icon.hide()
        self.icon.changeImg(newIcon)
        self.icon.show()
        self.redraw()

    def redraw(self):
        lcd.partial_show(self.pos[0], self.pos[1], self.size[0], self.size[1])


class MediaPlayer:
    def __init__(self, entity, position):
        data = HomeServer.getJson(entity)
        print(data)
        self.state = data['state'] if 'state' in data else "-"
        name = data['attributes']['friendly_name']
        source = data['attributes']['source'] if 'source' in data['attributes'] else "-"
        media_title = data['attributes']['media_title'] if 'media_title' in data['attributes'] else "-"
        self.entity = entity
        self.pos = position
        self.size = (500, 150)
        self.frame = M5Rect(self.pos[0], self.pos[1], self.size[0], self.size[1], 15, 0)
        self.icon = M5Img(self.pos[0] + 5, self.pos[1] + 5, "res/speaker.jpg", True)
        self.btnSource = IconButton("res/radio.jpg", (self.pos[0] + 50, self.pos[1] + 5), (48, 48))
        self.btnPlay = IconButton("res/play_cir.png", (self.pos[0] + 320, self.pos[1] + 50), (96, 96))
        self.btnNext = IconButton("res/next.png", (self.pos[0] + 420, self.pos[1] + 70), (48, 48))
        self.lblDevice = M5TextBox(self.pos[0] + 100, self.pos[1] + 15, name, lcd.FONT_DejaVu24, 0, rotate=0)
        self.lblState = M5TextBox(self.pos[0] + 380, self.pos[1] + 15, self.state, lcd.FONT_DejaVu24, 0, rotate=0)
        self.lblArtist = M5TextBox(self.pos[0] + 20, self.pos[1] + 70, source, lcd.FONT_DejaVu24, 0, rotate=0)
        self.lblSong = M5TextBox(self.pos[0] + 20, self.pos[1] + 100, media_title, lcd.FONT_DejaVu24, 0, rotate=0)
        entity_id = entity.split(".")
        m5mqtt.subscribe(str(statestream_base_topic + str(entity_id[0]) + '/' + str(entity_id[1]) + '/state'),
                         self.mqtt_state)
        m5mqtt.subscribe(str(statestream_base_topic + str(entity_id[0]) + '/' + str(entity_id[1]) + '/source'),
                         self.mqtt_source)
        m5mqtt.subscribe(str(statestream_base_topic + str(entity_id[0]) + '/' + str(entity_id[1]) + '/media_title'),
                         self.mqtt_media_title)
        m5mqtt.subscribe(str(statestream_base_topic + str(entity_id[0]) + '/' + str(entity_id[1]) + '/media_artist'),
                         self.mqtt_media_artist)

    def mqtt_state(self, topic_data):
        self.state = topic_data
        self.lblState.setText(self.state)
        if self.state == "playing":
            self.btnPlay.changeImg("res/pause_cir.png")
        else:
            self.btnPlay.changeImg("res/play_cir.png")

    def mqtt_source(self, topic_data):
        source = topic_data.replace('"', "")
        if source == "Spotify":
            self.btnSource.changeImg("res/spotify.jpg")
        elif source == "Computer":
            self.btnSource.changeImg("res/speaker.jpg")
            self.lblArtist.setText("")
        else:
            self.btnSource.changeImg("res/radio.jpg")
            self.lblArtist.setText("")
        self.redraw()

    def mqtt_media_title(self, topic_data):
        self.lblSong.setText(topic_data.replace('"', ""))
        self.redraw()

    def mqtt_media_artist(self, topic_data):
        self.lblArtist.setText(topic_data.replace('"', ""))
        self.redraw()

    def scheduler(self, touch):
        if self.isPressed(touch):
            if self.btnPlay.isPressed(touch):
                if self.state == "playing":
                    HomeServer.call(self.entity, "media_pause")
                else:
                    HomeServer.call(self.entity, "media_play")
            elif self.btnNext.isPressed(touch):
                HomeServer.call(self.entity, "media_next_track")
            elif self.btnSource.isPressed(touch):
                HomeServer.call(self.entity, "select_source", {"source": "FM1"})
            else:
                self.action()

    def action(self):
        pass

    def isPressed(self, touch):
        if (((self.pos[0]) <= touch[0]) and (touch[0] <= (self.pos[0] + self.size[0]))):
            if (((self.pos[1]) <= touch[1]) and (touch[1] <= (self.pos[1] + self.size[1]))):
                return True
        return False

    def redraw(self):
        lcd.partial_show(self.pos[0], self.pos[1], self.size[0], self.size[1])


class Light:
    def __init__(self, entity, position):
        data = HomeServer.getJson(entity)
        state = data['state']
        name = data['attributes']['friendly_name'][:4]
        self.entity = entity
        self.pos = position
        self.size = (150, 150)
        self.frame = M5Rect(self.pos[0], self.pos[1], self.size[0], self.size[1], 15, 0)
        self.icon = M5Img(self.pos[0] + self.size[0] - 50, self.pos[1] + 2, "res/ceil-lgt.jpg", True)
        self.lblTitle = M5TextBox(self.pos[0] + 10, self.pos[1] + self.size[1] - 50, name, lcd.FONT_DejaVu40, 0,
                                  rotate=0)
        self.lblState = M5TextBox(self.pos[0] + 10, self.pos[1] + self.size[1] - 75, state, lcd.FONT_DejaVu24, 0,
                                  rotate=0)
        entity_id = entity.split(".")
        m5mqtt.subscribe(str(statestream_base_topic + str(entity_id[0]) + '/' + str(entity_id[1]) + '/state'), self.mqtt_state)

    def mqtt_state(self, topic_data):
        self.lblState.setText(topic_data)
        self.redraw()

    def scheduler(self, touch):
        if self.isPressed(touch):
            self.action()

    def action(self):
        HomeServer.call(self.entity, "toggle")

    def isPressed(self, touch):
        if (self.pos[0] <= touch[0]) and (touch[0] <= (self.pos[0] + self.size[0])):
            if ((self.pos[1]) <= touch[1]) and (touch[1] <= (self.pos[1] + self.size[1])):
                return True
        return False

    def redraw(self):
        lcd.partial_show(self.pos[0], self.pos[1], self.size[0], self.size[1])

def syncRtcFromHomeAssistant():
    weekday = 6
    date_time = HomeServer.getState("sensor.date_time")
    date, time = date_time.split(", ")
    #time = HomeServer.getState("sensor.time")
    #date = HomeServer.getState("sensor.date")
    date = date.split("-")
    time = time.split(":")
    rtc.set_datetime((int(date[0]), int(date[1]), int(date[2]), weekday, int(time[0]), int(time[1]), 0))
    setLogMessage(HomeServer.getState("Time updated"))

lblScreenName = M5TextBox(10, 10, "Office", lcd.FONT_DejaVu72, 0, rotate=0)
rectHeader = M5Rect(0, 80, 540, 5, 0, 0)
lblTime = M5TextBox(420, 10, "23:45", lcd.FONT_DejaVu40, 0, rotate=0)
rectTopBox = M5Rect(20, 120, 500, 150, 15, 0)
lblBattery = M5TextBox(429, 234, "3.75V", lcd.FONT_DejaVu24, 0, rotate=0)
imgTemp = M5Img(468, 125, "res/temp.jpg", True)
lblTemp = M5TextBox(374, 135, "23.4", lcd.FONT_DejaVu40, 0, rotate=0)
rectBottom = M5Rect(0, 840, 540, 5, 0, 0)
imgRight = M5Img(445, 850, "res/right_2x.png", True)
lblHumidity = M5TextBox(374, 185, "43%", lcd.FONT_DejaVu40, 0, rotate=0)
image0 = M5Img(468, 175, "res/water-pct.png", True)
imgLeft = M5Img(340, 850, "res/left_2x.png", True)
line0 = M5Line(M5Line.PLINE, 350, 120, 350, 270, 0)

# UI Elements
ToggleButtons = [
    Light("light.pcb_backlight", (20, 290)),
    Light("light.monitor_riser", (190, 290)),
    Light("switch.office_spots", (360, 290)),
    MediaPlayer("media_player.schreibtisch", (20, 660))
]


# Describe this function...
def HeadHandler():
    global DeviceState
    lblTime.setText(str((str((rtc.datetime()[4])) + str((str(':') + str((rtc.datetime()[5])))))))
    lcd.partial_show(410, 0, 150, 80)


# Describe this function...
def DeviceHandler():
    global DeviceState
    lblBattery.setText(str((str(("%.2f" % ((bat.voltage()) / 1000))) + str('V'))))
    lcd.partial_show(350, 120, 170, 150)


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
            print(touchNow[0], touchNow[1])
            for element in ToggleButtons:
                element.scheduler((touchNow[0], touchNow[1]))
    touchOld = touchNow[3]
    pass


@timerSch.event('deviceManager')
def tdeviceManager():
    global DeviceState
    HeadHandler()
    pass


@timerSch.event('HardwareManager')
def tHardwareManager():
    global DeviceState
    DeviceHandler()
    pass

#syncRtcFromHomeAssistant()

m5mqtt.start()
lcd.show()


timerSch.run('touch', 40, 0x00)
timerSch.run('deviceManager', 10000, 0x00)
timerSch.run('HardwareManager', 1000, 0x00)

setLogMessage("Ready")


