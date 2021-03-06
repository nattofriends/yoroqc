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

class YoroFrame(wx.Frame):
    PLAY = '0'
    PAUSE = '1'
    CHOTTO_DAKE = 0.01
    MESSAGE_SHOW_DURATION = 3000
    
    ITEM_MAP = {
        1: "", #new
        2: " (done)",
        3: " (rejected)",
    }
    
    def __init__(self, tb, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.register_hotkey()
        self.Bind(wx.EVT_HOTKEY, self.on_hotkey, id=self.hotkey_id)
        
        self.tb = tb
        
        self.config = ConfigParser.SafeConfigParser()
        self.config.read("config.ini")
        
        self.listener = mpcw32.Listener(self.on_receive_message)
        self.last_state = None
        self.intent = None
        self.showing = False
        self.queue_message = None
        
        # It's probably dangerous to raise a dialog box inside a constructor, so do it on initial callback.
        try:
            self.author = self.config.get("yoroqc", "name")
        except ConfigParser.NoOptionError:
            self.author = None
        
    def register_hotkey(self):
        self.hotkey_id = 100
        self.RegisterHotKey(
            self.hotkey_id, #a unique ID for this hotkey
            0, #the modifier key
            win32con.VK_F9,
        )
            
    def on_hotkey(self, evt):
        """
        Prints a simple message when a hotkey event is received.
        """
        if self.last_state != self.PAUSE:
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
            
            if self.author:
                self.tb.ShowBalloon("YORO-QC", "Ohamorning, {0}.".format(self.author), flags=wx.ICON_INFORMATION)
                
            
            while not self.author:
                dialog = wx.TextEntryDialog(None, "What is your name?", caption="YORO-QC")
                dialog.Raise()
                
                dialog.ShowModal()
                author = dialog.GetValue()
                
                if author != u'':
                    self.author = author
                    self.config.set("yoroqc", "name", self.author)
                    with open("config.ini", 'wb') as conf:
                        self.config.write(conf)
                else:
                    wx.MessageBox("Enter your name, faggot.", "YORO-QC", style=wx.ICON_ERROR)
            
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
                time = round(float(data))
                minutes = str(int(time / 60)).zfill(2) 
                seconds = str(int(time % 60)).zfill(2)
                
                r = requests.get(self.config.get("yoroqc", "api") + "/api/search/time/{0}:{1}".format(minutes, seconds))
                formatted = ["QC Note at {0}:{1}".format(minutes, seconds)]
                around = r.json()
                if around['items']:
                    formatted.extend(['', 'Existing Items:'])
                for item in around['items']:
                    formatted.append("{id}: ({time}) '{text}', by {author}{status_text}".format(status_text=self.ITEM_MAP[item['status']], **item))
                formatted = '\n'.join(formatted)
                
                dialog = wx.TextEntryDialog(None, formatted, caption="YORO-QC")
                dialog.Raise()
                
                dialog.ShowModal()
                note = dialog.GetValue()
                
                if note != u'':
                    payload = {"time": "{0}:{1}".format(minutes, seconds), "text": note, "author": self.author}
                    json_payload = json.dumps(payload)
                    
                    try:
                        r = requests.post(self.config.get("yoroqc", "api") + "/api/add", data=json_payload)
                        if r.status_code == 200:
                            response = r.json()
                            self.queue_message = "Posted #{0}".format(response['id'])
                        else:
                            self.queue_message = "Error (HTTP {0}).".format(r.status_code)
                    except Exception as e:
                        self.queue_message = "Error ({0})".format(type(e))
                        
                if self.last_state != self.PAUSE:
                    self.intent = self.PLAY
                    self.listener.send_message(mpcw32.COMMAND.CMD_PLAYPAUSE)
                else:  # No state transitions happened, show message directly
                    if self.queue_message:
                        self.send_osd_message(self.queue_message)
                        self.queue_message = None
                self.showing = False
                
class YoroTaskBarIcon(wx.TaskBarIcon):
    '''Despite the existence of this, let us continue to do many things through the OSD callback,
    because no one has time to look at notification bubbles while timing.
    '''
    
    def __init__(self, *args, **kwargs):
        wx.TaskBarIcon.__init__(self, *args, **kwargs)
        
        log_level = wx.Log.GetLogLevel()
        wx.Log.SetLogLevel(0)
        icon = wx.IconFromBitmap(wx.Bitmap('myuuse.png'))
        wx.Log.SetLogLevel(log_level)
        
        self.SetIcon(icon, "YORO-QC")
        
    def create_menu_item(self, menu, label, func):
        item = wx.MenuItem(menu, -1, label)
        menu.Bind(wx.EVT_MENU, func, id=item.GetId())
        menu.AppendItem(item)
        return item
        
    def CreatePopupMenu(self):
        menu = wx.Menu()
        # create_menu_item(menu, 'Say Hello', self.on_hello)
        # menu.AppendSeparator()
        self.create_menu_item(menu, 'Quit', self.on_quit)
        return menu
        
    def on_quit(self, event):
        os._exit(0)
    
        
app = wx.App()
# I don't remember what these arguments mean.
tb = YoroTaskBarIcon()
YoroFrame(tb, None, -1, "")

app.MainLoop()