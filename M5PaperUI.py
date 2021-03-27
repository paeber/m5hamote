##################################################
## M5Hamote - A HomeAssistant remote on M5Paper
##################################################
## Author: @paeber
## Github: https://github.com/paeber/m5paper-homeassistant-remote
## Copyright: Copyright 2021, PaEber Electronics
## Version: 0.1.0
## Status: beta
##################################################

from m5stack import *
from m5ui import *
from uiflow import *
from m5stack import touch
from m5mqtt import M5mqtt
import json


class IconButton(object):
    # Display image and read if touch position is on image
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


class MediaPlayer(object):
    # Display rectangle with media player status and controls
    def __init__(self, entity, position, services):
        self.hassio = services.HomeServer
        self.mqtt = services.MqttServer
        data = self.hassio.getJson(entity)
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
        self.mqtt.subscribe(
            str(services.Config['mqtt']['base_topic'] + str(entity_id[0]) + '/' + str(entity_id[1]) + '/state'),
            self.mqtt_state)
        self.mqtt.subscribe(
            str(services.Config['mqtt']['base_topic'] + str(entity_id[0]) + '/' + str(entity_id[1]) + '/source'),
            self.mqtt_source)
        self.mqtt.subscribe(
            str(services.Config['mqtt']['base_topic'] + str(entity_id[0]) + '/' + str(entity_id[1]) + '/media_title'),
            self.mqtt_media_title)
        self.mqtt.subscribe(
            str(services.Config['mqtt']['base_topic'] + str(entity_id[0]) + '/' + str(entity_id[1]) + '/media_artist'),
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
                    self.hassio.call(self.entity, "media_pause")
                else:
                    self.hassio.call(self.entity, "media_play")
            elif self.btnNext.isPressed(touch):
                self.hassio.call(self.entity, "media_next_track")
            elif self.btnSource.isPressed(touch):
                self.hassio.call(self.entity, "select_source", {"source": "FM1"})
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


class Light(object):
    # Display rectangle with light status and toggle control
    def __init__(self, entity, position, services):
        self.hassio = services.HomeServer
        self.mqtt = services.MqttServer
        data = self.hassio.getJson(entity)
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
        self.mqtt.subscribe(
            str(services.Config['mqtt']['base_topic'] + str(entity_id[0]) + '/' + str(entity_id[1]) + '/state'),
            self.mqtt_state)

    def mqtt_state(self, topic_data):
        self.lblState.setText(topic_data)
        self.redraw()

    def scheduler(self, touch):
        if self.isPressed(touch):
            self.action()

    def action(self):
        self.hassio.call(self.entity, "toggle")

    def isPressed(self, touch):
        if (self.pos[0] <= touch[0]) and (touch[0] <= (self.pos[0] + self.size[0])):
            if ((self.pos[1]) <= touch[1]) and (touch[1] <= (self.pos[1] + self.size[1])):
                return True
        return False

    def redraw(self):
        lcd.partial_show(self.pos[0], self.pos[1], self.size[0], self.size[1])
