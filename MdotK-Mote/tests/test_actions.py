"""Action permission/allowlist regression checks."""
import sys, types, unittest
# Import os_controller's dependencies without attempting desktop key injection.
from os_controller import HostController, Action
from action_handlers import ActionHandlers

class ActionTests(unittest.TestCase):
    def setUp(self):
        self.host=HostController({'typing':False,'gamepad':False,'power':False})
        self.handlers=ActionHandlers(self.host)
    def test_sensitive_permissions_default_off(self):
        for action in (Action.POWER,Action.RESTART,Action.SLEEP):
            with self.assertRaises(PermissionError): self.host.execute(action.value)
        with self.assertRaises(PermissionError): self.host.execute(Action.TYPE.value,{'text':'blocked'})
        with self.assertRaises(PermissionError): self.host.execute(Action.GAMEPAD.value,{'button':'A'})
    def test_unknown_launcher_rejected(self):
        with self.assertRaises(ValueError): self.handlers.app_launcher('arbitrary_shell')
    def test_unknown_stream_rejected(self):
        with self.assertRaises(ValueError): self.handlers.streaming_shortcut('unknown')
    def test_power_requires_phone_confirmation(self):
        self.host.permissions['power']=True
        with self.assertRaises(PermissionError): self.handlers.power_action('power',False)
    def test_key_allowlist(self):
        self.host.permissions['typing']=True
        with self.assertRaises(ValueError): self.host._keyboard(Action.KEY,{'key':'win'})
if __name__=='__main__': unittest.main()
