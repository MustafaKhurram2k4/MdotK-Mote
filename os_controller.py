"""Safe cross-platform host actions. Sensitive inputs require explicit UI grants."""
import platform, subprocess, webbrowser
from enum import Enum
from virtual_gamepad import VirtualGamepad, ForegroundGameDetector

class Action(str, Enum):
    APP_DISCORD="discord"; APP_TWITCH="twitch"; APP_KICK="kick"; APP_GOOGLE="google"; APP_SPOTIFY="spotify"
    HBO="hbo"; PRIME="prime"; NETFLIX="netflix"; YOUTUBE="youtube"; HOTSTAR="hotstar"
    MEDIA_PLAY_PAUSE="media_play_pause"; MEDIA_NEXT="media_next"; MEDIA_PREVIOUS="media_previous"
    VOL_UP="volume_up"; VOL_DOWN="volume_down"; MUTE="mute"
    POWER="power"; RESTART="restart"; SLEEP="sleep"
    KEY="key"; TYPE="type"; DPAD_UP="dpad_up"; DPAD_DOWN="dpad_down"; DPAD_LEFT="dpad_left"; DPAD_RIGHT="dpad_right"
    GAMEPAD="gamepad"
URLS={Action.APP_DISCORD:"https://discord.com/app",Action.APP_TWITCH:"https://twitch.tv",Action.APP_KICK:"https://kick.com",Action.APP_GOOGLE:"https://google.com",Action.APP_SPOTIFY:"https://open.spotify.com",Action.HBO:"https://max.com",Action.PRIME:"https://primevideo.com",Action.NETFLIX:"https://netflix.com",Action.YOUTUBE:"https://youtube.com",Action.HOTSTAR:"https://hotstar.com"}
class HostController:
    def __init__(self, permissions=None):
        self.permissions = permissions or {"typing":False,"gamepad":False,"power":False}
        self._pressed=set(); self.virtual_pad=VirtualGamepad(); self.game_detector=ForegroundGameDetector()
    def execute(self, action: str, data=None):
        data=data or {}; action=Action(action)
        if action in URLS: webbrowser.open(URLS[action]); return {"ok":True}
        if action in (Action.POWER,Action.RESTART,Action.SLEEP):
            if not self.permissions.get("power"): raise PermissionError("Power actions are disabled on desktop")
            return self._power(action)
        if action in (Action.KEY,Action.TYPE):
            if not self.permissions.get("typing"): raise PermissionError("Keyboard typing is disabled on desktop")
            return self._keyboard(action,data)
        if action == Action.GAMEPAD:
            if not self.permissions.get("gamepad"): raise PermissionError("Gamepad is disabled on desktop")
            return self._gamepad(data)
        return self._media(action)
    def _media(self, action):
        keys={Action.MEDIA_PLAY_PAUSE:"playpause",Action.MEDIA_NEXT:"nexttrack",Action.MEDIA_PREVIOUS:"prevtrack",Action.VOL_UP:"volumeup",Action.VOL_DOWN:"volumedown",Action.MUTE:"volumemute"}
        key=keys.get(action)
        if not key: raise ValueError("Unsupported media action")
        if platform.system()=="Darwin":
            script={'playpause':'tell application "System Events" to key code  playpause','nexttrack':'tell application "System Events" to key code 124','prevtrack':'tell application "System Events" to key code 123'}.get(key)
            if script: subprocess.run(["osascript","-e",script],check=False)
            else: subprocess.run(["osascript","-e",f'tell application "System Events" to key code {key}'],check=False)
        else:
            try:
                import pyautogui
                pyautogui.press(key)
            except Exception as exc: raise RuntimeError(f"Media control unavailable: {exc}")
        return {"ok":True}
    def _keyboard(self,action,data):
        # Validate input before importing automation backends (which may require a GUI session).
        if action==Action.TYPE:
            text=str(data.get("text",""))[:500]
            import pyautogui
            pyautogui.write(text,interval=0.002); return {"ok":True}
        key=str(data.get("key",""))
        allowed={"enter","esc","escape","space","tab","backspace","delete","up","down","left","right","home","end","pageup","pagedown"}
        if key.lower() not in allowed: raise ValueError("Key is not allowed")
        import pyautogui
        pyautogui.press(key.lower()); return {"ok":True}
    def _power(self,action):
        system=platform.system()
        if system=="Windows":
            args={Action.POWER:["shutdown","/s","/t","0"],Action.RESTART:["shutdown","/r","/t","0"],Action.SLEEP:["rundll32.exe","powrprof.dll,SetSuspendState","0,1,0"]}[action]
        elif system=="Darwin": args={Action.POWER:["osascript","-e","tell application \"System Events\" to shut down"],Action.RESTART:["osascript","-e","tell application \"System Events\" to restart"],Action.SLEEP:["osascript","-e","tell application \"System Events\" to sleep"]}[action]
        else: args={Action.POWER:["systemctl","poweroff"],Action.RESTART:["systemctl","reboot"],Action.SLEEP:["systemctl","suspend"]}[action]
        subprocess.Popen(args); return {"ok":True}
    def _gamepad(self,data):
        # Virtual XInput/uinput output is preferred. On Windows it is gated to a
        # recognized foreground game; elsewhere backend availability is reported.
        name=str(data.get("button", ""))
        if platform.system()=="Windows":
            focus=self.game_detector.foreground()
            if not focus.get("active"):
                return {"ok":False,"mode":"waiting for game focus","game":focus.get("process",""),"reason":focus.get("reason")}
        if data.get("axis"):
            axis=str(data.get("axis")); value=float(data.get("value",0))
            return self.virtual_pad.update_axis(axis,value)
        if name in {"LX","LY","RX","RY","LT","RT"}:
            return self.virtual_pad.update_axis(name.lower(),float(data.get("value",0)))
        if name in self.virtual_pad.BUTTONS or name in ("L2","R2"):
            return self.virtual_pad.button(name,bool(data.get("pressed",True)))
        if not self.virtual_pad.available:
            fallback={"A":"space","B":"esc","X":"e","Y":"q","L1":"shift","R1":"alt","L2":"ctrl","R2":"enter"}
            if name in fallback:
                import pyautogui
                pyautogui.keyDown(fallback[name]) if data.get("pressed",True) else pyautogui.keyUp(fallback[name])
                return {"ok":True,"mode":"keyboard-mapped fallback"}
        # Compatibility fallback for directional inputs from the previous client.
        mapping={"UP":"up","DOWN":"down","LEFT":"left","RIGHT":"right"}
        if name in mapping:
            import pyautogui
            pyautogui.keyDown(mapping[name]) if data.get("pressed",True) else pyautogui.keyUp(mapping[name])
            return {"ok":True,"mode":"keyboard directional fallback"}
        dpad_fallback={"DPAD_UP":"up","DPAD_DOWN":"down","DPAD_LEFT":"left","DPAD_RIGHT":"right"}
        if name in dpad_fallback and not self.virtual_pad.available:
            import pyautogui
            key=dpad_fallback[name]
            pyautogui.keyDown(key) if data.get("pressed",True) else pyautogui.keyUp(key)
            return {"ok":True,"mode":"keyboard directional fallback"}
        raise ValueError("Unknown gamepad input")
