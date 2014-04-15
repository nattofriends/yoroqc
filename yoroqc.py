import ConfigParser
import re
import os
import json
import threading
import time

import requests
import wx
import win32con #for the VK keycodes

import mpcw32

class FrameWithHotKey(wx.Frame):
    PLAY = '0'
    PAUSE = '1'
    CHOTTO_DAKE = 0.01
    MESSAGE_SHOW_DURATION = 3000
    
    ENDPOINT = "http://asuna.nolm.name:8888/api/add"
    
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.register_hotkey()
        self.Bind(wx.EVT_HOTKEY, self.handleHotKey, id=self.hotKeyId)
        
        self.config = ConfigParser.ConfigParser()
        self.config.read("config.ini")
        
        self.listener = mpcw32.Listener(self.on_receive_message)
        self.last_state = None
        self.intent = None
        self.showing = False
        self.queue_message = None
        
    def register_hotkey(self):
        self.hotKeyId = 100
        self.RegisterHotKey(
            self.hotKeyId, #a unique ID for this hotkey
            0, #the modifier key
            win32con.VK_F9,
        )
            
    def handleHotKey(self, evt):
        """
        Prints a simple message when a hotkey event is received.
        """
        self.intent = self.PAUSE
        self.listener.send_message(mpcw32.COMMAND.CMD_PLAYPAUSE)
        
        self.listener.send_message(mpcw32.COMMAND.CMD_GETCURRENTPOSITION)
        
    def send_osd_message(self, message):
        time.sleep(self.CHOTTO_DAKE)
        # Posting it on another thread doesn't work in some edge cases involving
        # pausing the video and then psoting a note directly afterwards. People can wait.
        self.listener.send_osd_message(message, self.MESSAGE_SHOW_DURATION)
        
    def on_receive_message(self, command, data):
        if command == mpcw32.COMMAND.CMD_CONNECT:
            # Get the last state. This produces a blip in the player, but we won't mind that for now.
            self.listener.send_message(mpcw32.COMMAND.CMD_PLAYPAUSE)
            self.listener.send_message(mpcw32.COMMAND.CMD_PLAYPAUSE)
            
        elif command == mpcw32.COMMAND.CMD_DISCONNECT:
            # Screw wxPython, we're outta here
            os._exit(0)
            
        elif command == mpcw32.COMMAND.CMD_PLAYMODE:
            if not self.intent:
                self.last_state = data
                
            if self.intent and data != self.intent:
                self.listener.send_message(mpcw32.COMMAND.CMD_PLAYPAUSE)
            else:
                # Okay, done toggling now. If we have notes, send them
                if self.queue_message:
                    # Post the message in another thread because doing it here tends to have it
                    # overwritten by pause/play messages when using EVR-CP (and possibly other renderers
                    # not madVR, not tested)
                    threading.Thread(target=self.send_osd_message, args=(self.queue_message,)).start()
                    self.queue_message = None
                self.intent = None
            
        elif command == mpcw32.COMMAND.CMD_CURRENTPOSITION:
            if not self.showing:
                self.showing = True
                time = float(data)
                minutes = str(int(time / 60)).zfill(2) 
                seconds = str(int(round(time % 60))).zfill(2)
                
                dialog = wx.TextEntryDialog(None, "QC Note at {0}:{1}".format(minutes, seconds), caption="YORO-QC")
                dialog.Raise()
                
                dialog.ShowModal()
                note = dialog.GetValue()
                
                if note != u'':
                    payload = {"time": "{0}:{1}".format(minutes, seconds), "text": note}
                    json_payload = json.dumps(payload)
                    r = requests.post(self.config.get("yoroqc", "api") + "/api/add", data=json_payload)
                    if r.status_code == 200:
                        response = r.json()
                        self.queue_message = "Posted #{0}".format(response['id'])
                    else:
                        self.queue_message = "Error posting note."
                        
                self.intent = self.last_state
                self.listener.send_message(mpcw32.COMMAND.CMD_PLAYPAUSE)
                self.showing = False
        
app = wx.App()
# I don't remember what these arguments mean.
f = FrameWithHotKey(None, -1, "")
app.MainLoop()