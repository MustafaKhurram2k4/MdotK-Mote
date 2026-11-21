"""Explicit action ID registry. Each ID is validated and delegated to HostController."""
from os_controller import HostController, Action
APP_ACTIONS={"discord":Action.APP_DISCORD,"twitch":Action.APP_TWITCH,"kick":Action.APP_KICK,"google":Action.APP_GOOGLE,"spotify":Action.APP_SPOTIFY}
STREAM_ACTIONS={"hbo":Action.HBO,"prime":Action.PRIME,"netflix":Action.NETFLIX,"youtube":Action.YOUTUBE,"hotstar":Action.HOTSTAR}
MEDIA_ACTIONS={"play_pause":Action.MEDIA_PLAY_PAUSE,"next":Action.MEDIA_NEXT,"previous":Action.MEDIA_PREVIOUS,"volume_up":Action.VOL_UP,"volume_down":Action.VOL_DOWN,"mute":Action.MUTE}
POWER_ACTIONS={"power":Action.POWER,"restart":Action.RESTART,"sleep":Action.SLEEP}
KEY_ACTIONS={"key":Action.KEY,"type":Action.TYPE}
DPAD_ACTIONS={"up":Action.DPAD_UP,"down":Action.DPAD_DOWN,"left":Action.DPAD_LEFT,"right":Action.DPAD_RIGHT}
class ActionHandlers:
    def __init__(self, controller:HostController): self.controller=controller
    def app_launcher(self, name):
        if name not in APP_ACTIONS: raise ValueError("Unknown launcher")
        return self.controller.execute(APP_ACTIONS[name].value)
    def streaming_shortcut(self, name):
        if name not in STREAM_ACTIONS: raise ValueError("Unknown streaming shortcut")
        return self.controller.execute(STREAM_ACTIONS[name].value)
    def media_volume(self, name):
        if name not in MEDIA_ACTIONS: raise ValueError("Unknown media control")
        return self.controller.execute(MEDIA_ACTIONS[name].value)
    def power_action(self, name, confirmed=False):
        if not confirmed: raise PermissionError("Phone confirmation required for power action")
        if name not in POWER_ACTIONS: raise ValueError("Unknown power action")
        return self.controller.execute(POWER_ACTIONS[name].value)
    def keyboard_action(self, name, data):
        if name not in KEY_ACTIONS: raise ValueError("Unknown keyboard action")
        return self.controller.execute(KEY_ACTIONS[name].value,data)
    def dpad_navigation(self, direction):
        if not self.controller.permissions.get("typing"): raise PermissionError("Keyboard input is disabled on desktop")
        if direction not in DPAD_ACTIONS: raise ValueError("Unknown direction")
        return self.controller.execute("key",{"key":direction})
    def gamepad_input(self, button, pressed=True, data=None):
        payload={"button":button,"pressed":bool(pressed)}
        if data: payload.update(data)
        return self.controller.execute("gamepad",payload)
    def dispatch(self, payload):
        kind=payload.get("kind"); action=payload.get("action"); data=payload.get("data",{})
        if kind=="app": return self.app_launcher(action)
        if kind=="stream": return self.streaming_shortcut(action)
        if kind=="media": return self.media_volume(action)
        if kind=="power": return self.power_action(action,data.get("confirmed",False))
        if kind=="keyboard": return self.keyboard_action(action,data)
        if kind=="dpad": return self.dpad_navigation(action)
        if kind=="gamepad": return self.gamepad_input(action,data.get("pressed",True),data)
        raise ValueError("Unknown action category")
