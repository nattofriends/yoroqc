import win32ui, win32process, win32con, win32api, win32gui, ctypes, ctypes.wintypes
import time, threading

class COMMAND:
    CMD_CONNECT             = '0x50000000'
    CMD_STATE               = '0x50000001'
    CMD_PLAYMODE            = '0x50000002'
    CMD_NOWPLAYING          = '0x50000003'
    CMD_LISTSUBTITLETRACKS  = '0x50000004'
    CMD_LISTAUDIOTRACKS     = '0x50000005'
    CMD_CURRENTPOSITION     = '0x50000007'
    CMD_NOTIFYSEEK          = '0x50000008'
    CMD_NOTIFYENDOFSTREAM   = '0x50000009'
    CMD_PLAYLIST            = '0x50000006'
    CMD_DISCONNECT          = '0x5000000b'

    CMD_OPENFILE            = '0xA0000000'
    CMD_STOP                = '0xA0000001'
    CMD_CLOSEFILE           = '0xA0000002'
    CMD_PLAYPAUSE           = '0xA0000003'
    CMD_ADDTOPLAYLIST       = '0xA0001000'
    CMD_CLEARPLAYLIST       = '0xA0001001'
    CMD_STARTPLAYLIST       = '0xA0001002'
    CMD_SETPOSITION         = '0xA0002000'
    CMD_SETAUDIODELAY       = '0xA0002001'
    CMD_SETSUBTITLEDELAY    = '0xA0002002'
    CMD_SETINDEXPLAYLIST    = '0xA0002003'
    CMD_SETAUDIOTRACK       = '0xA0002004'
    CMD_SETSUBTITLETRACK    = '0xA0002005'
    CMD_GETSUBTITLETRACKS   = '0xA0003000'
    CMD_GETCURRENTPOSITION  = '0xA0003004'
    CMD_JUMPOFNSECONDS      = '0xA0003005'
    CMD_GETAUDIOTRACKS      = '0xA0003001'
    CMD_GETNOWPLAYING       = '0xA0003002'
    CMD_GETPLAYLIST         = '0xA0003003'
    CMD_TOGGLEFULLSCREEN    = '0xA0004000'
    CMD_JUMPFORWARDMED      = '0xA0004001'
    CMD_JUMPBACKWARDMED     = '0xA0004002'
    CMD_INCREASEVOLUME      = '0xA0004003'
    CMD_DECREASEVOLUME      = '0xA0004004'
    CMD_SHADER_TOGGLE       = '0xA0004005'
    CMD_CLOSEAPP            = '0xA0004006'
    CMD_OSDSHOWMESSAGE      = '0xA0005000'


class MPC_OSDDATA(ctypes.Structure):
    _fields_ = [
        ('nMsgPos', ctypes.c_int),
        ('nDurationMS', ctypes.c_int),
        ('strMsg', ctypes.c_wchar*127)
    ]

class COPYDATASTRUCT(ctypes.Structure):
    _fields_ = [
        ('dwData', ctypes.wintypes.LPARAM),
        ('cbData', ctypes.wintypes.DWORD),
        ('lpData', ctypes.c_void_p)
    ]
PCOPYDATASTRUCT = ctypes.POINTER(COPYDATASTRUCT)


class Listener(object):
    def __init__(self, receive_callback):
        self.mpchc_hwnd = None

        message_map = {
            win32con.WM_COPYDATA: self.on_copydata,
        }

        self.receive_callback = receive_callback
        
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = message_map
        wc.lpszClassName = 'MyWindowClass'
        wc.hInstance = win32api.GetModuleHandle(None)

        classAtom = win32gui.RegisterClass(wc)
        self.hwnd = win32gui.CreateWindow (classAtom, "win32gui test", 0, 0, 0,
            win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, wc.hInstance, None)

        cmd = r"mpc-hc\mpc-hc.exe /slave " + str(self.hwnd)

        si = win32process.STARTUPINFO()
        procArgs = (None, cmd, None, None, 0, win32process.CREATE_NEW_CONSOLE, None, None,  si)

        self.procHandles = win32process.CreateProcess(*procArgs)
        self.hProcess, self.hThread, self.PId, self.TId = self.procHandles

    def on_copydata(self, hwnd, msg, wparam, lparam):
        pCDS = ctypes.cast(lparam, PCOPYDATASTRUCT)

        command = hex(pCDS.contents.dwData)
        data = ctypes.wstring_at(pCDS.contents.lpData)
        
        self.do_stuff(command, data)

    def send_message(self, command, message=''):
        """
        Send commands to MPC

        e.g. self.send_message(COMMAND.CMD_GETCURRENTPOSITION)
        """
        command = int(command, 16)
        data = ctypes.create_unicode_buffer(message)
        cds = COPYDATASTRUCT(command, ctypes.sizeof(data), ctypes.cast(data, ctypes.c_void_p))
        win32api.SendMessage(self.mpchc_hwnd, win32con.WM_COPYDATA, 0, ctypes.addressof(cds))

    def send_osd_message(self, message, duration):
        """
        Send OSD message to MPC. This will display a message on MPC
        Max message length = 127 characters
        """
        command = int(COMMAND.CMD_OSDSHOWMESSAGE, 16)
        data = MPC_OSDDATA(1, int(duration), message)
        cds = COPYDATASTRUCT(command, ctypes.sizeof(data), ctypes.addressof(data))
        win32api.SendMessage(self.mpchc_hwnd, win32con.WM_COPYDATA, 0, ctypes.addressof(cds))

    def do_stuff(self, command, data):
        if command == COMMAND.CMD_CONNECT:
            self.mpchc_hwnd = int(data)
        self.receive_callback(command, data)
