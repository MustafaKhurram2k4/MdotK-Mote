"""Consent-gated virtual Xbox-style gamepad output with foreground-game detection.

Windows: vgamepad/ViGEmBus. Linux: uinput when installed and accessible.
macOS: intentionally reports unavailable; keyboard fallback remains in HostController.
"""
from __future__ import annotations
import platform, threading, time


class VirtualGamepad:
    BUTTONS = {"A":"A", "B":"B", "X":"X", "Y":"Y", "L1":"LEFT_SHOULDER", "R1":"RIGHT_SHOULDER", "L3":"LEFT_THUMB", "R3":"RIGHT_THUMB", "START":"START", "BACK":"BACK", "DPAD_UP":"DPAD_UP", "DPAD_DOWN":"DPAD_DOWN", "DPAD_LEFT":"DPAD_LEFT", "DPAD_RIGHT":"DPAD_RIGHT"}
    def __init__(self):
        self.system=platform.system(); self.pad=None; self.available=False; self.error=None
        self.axes={"lx":0.0,"ly":0.0,"rx":0.0,"ry":0.0,"lt":0.0,"rt":0.0}; self.buttons=set()
        self._init_backend()
    def _init_backend(self):
        try:
            if self.system=="Windows":
                import vgamepad
                self.pad=vgamepad.VX360Gamepad(); self.vg=vgamepad; self.available=True
            elif self.system=="Linux":
                # vgamepad uses Linux uinput; user must have /dev/uinput access.
                import vgamepad
                self.pad=vgamepad.VX360Gamepad(); self.vg=vgamepad; self.available=True
            else: self.error="Native virtual gamepad backend is not available on macOS. Keyboard fallback is supported."
        except Exception as e: self.error=f"Virtual gamepad backend unavailable: {e}"
    def update_axis(self, axis, value):
        if axis not in self.axes: raise ValueError("Unknown gamepad axis")
        value=max(-1.0,min(1.0,float(value))); self.axes[axis]=value
        if not self.available: return {"ok":False,"mode":"keyboard fallback","reason":self.error}
        if self.system=="Windows":
            if axis in ("lx","ly"):
                self.pad.left_joystick_float(x_value_float=self.axes["lx"],y_value_float=-self.axes["ly"])
            elif axis in ("rx","ry"):
                self.pad.right_joystick_float(x_value_float=self.axes["rx"],y_value_float=-self.axes["ry"])
            elif axis=="lt": self.pad.left_trigger_float(value_float=max(0.0,value))
            elif axis=="rt": self.pad.right_trigger_float(value_float=max(0.0,value))
            self.pad.update(); return {"ok":True,"mode":"virtual Xbox 360 controller"}
        if self.system=="Linux":
            if axis in ("lx","ly"): self.pad.left_joystick_float(x_value_float=self.axes["lx"],y_value_float=-self.axes["ly"])
            elif axis in ("rx","ry"): self.pad.right_joystick_float(x_value_float=self.axes["rx"],y_value_float=-self.axes["ry"])
            elif axis=="lt": self.pad.left_trigger_float(value_float=max(0.0,value))
            elif axis=="rt": self.pad.right_trigger_float(value_float=max(0.0,value))
            self.pad.update(); return {"ok":True,"mode":"uinput virtual gamepad"}
        return {"ok":False,"mode":"keyboard fallback","reason":self.error}
    def button(self, name, pressed=True):
        if name in ("L2","R2"):
            return self.update_axis("lt" if name=="L2" else "rt",1.0 if pressed else 0.0)
        if name not in self.BUTTONS: raise ValueError("Unknown gamepad button")
        if pressed: self.buttons.add(name)
        else: self.buttons.discard(name)
        if not self.available: return {"ok":False,"mode":"keyboard fallback","reason":self.error}
        if self.system=="Windows":
            enum=getattr(self.vg, "XUSB_BUTTON", None)
            if enum is None: return {"ok":False,"mode":"virtual Xbox controller","reason":"Button enum unavailable"}
            btn=getattr(enum,self.BUTTONS[name]); self.pad.press_button(button=btn) if pressed else self.pad.release_button(button=btn); self.pad.update()
        elif self.system=="Linux":
            enum=getattr(self.vg,"XUSB_BUTTON",None)
            if enum is not None:
                btn=getattr(enum,self.BUTTONS[name]); self.pad.press_button(button=btn) if pressed else self.pad.release_button(button=btn); self.pad.update()
        return {"ok":True,"mode":"virtual Xbox-style controller"}
    def reset(self):
        for b in list(self.buttons):
            try: self.button(b,False)
            except Exception: pass
        for a in self.axes: self.axes[a]=0
        if self.available and self.system=="Windows":
            try: self.pad.reset(); self.pad.update()
            except Exception: pass
    def close(self):
        self.reset()
        try:
            if self.pad and self.system=="Linux": self.pad.destroy()
        except Exception: pass

class ForegroundGameDetector:
    """Detect whether a recognizable game is the foreground process; never launches or hooks it."""
    GAME_HINTS=("game","steam","epic","unity","unreal","valorant","league","dota","cs2","counter-strike","minecraft","roblox","elden","fortnite","apex","overwatch","gta","forza","racing","rocketleague","cyberpunk","witcher","bg3","baldur","pubg","warzone","cod","battlefield","arma","hollow","hades","fallout","skyrim","resident","remnant","palworld","tekken","streetfighter","yuzu","ryujinx")
    EXCLUDED=("explorer","chrome","msedge","firefox","opera","brave","discord","spotify","steamwebhelper","gamebar","gamingservices","gameservices","searchhost","startmenuexperience","applicationframehost","systemsettings","settings","taskmgr","code","python","mote")
    def __init__(self): self._lock=threading.Lock(); self._cached={"active":False,"process":"","reason":"Detection supported on Windows only"}; self._last=0
    def foreground(self):
        if platform.system()!="Windows": return dict(self._cached)
        if time.monotonic()-self._last<0.5: return dict(self._cached)
        try:
            import ctypes, psutil
            hwnd=ctypes.windll.user32.GetForegroundWindow(); pid=ctypes.c_ulong(); ctypes.windll.user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            proc=psutil.Process(pid.value); name=proc.name().lower().replace(".exe",""); hints=self.GAME_HINTS
            active=any(h in name for h in hints) and not any(x in name for x in self.EXCLUDED)
            self._cached={"active":active,"process":proc.name(),"reason":"Foreground game detected" if active else "No recognized foreground game"}; self._last=time.monotonic()
        except Exception as e: self._cached={"active":False,"process":"","reason":f"Detection unavailable: {e}"}; self._last=time.monotonic()
        return dict(self._cached)
