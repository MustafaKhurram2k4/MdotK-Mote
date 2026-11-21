"""Desktop Mote consent center. Remote permissions are off by default."""
import sys, os, threading, secrets, socket, platform, subprocess
from pathlib import Path
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,QCheckBox,QMessageBox,QSystemTrayIcon,QMenu,QProgressBar
from PySide6.QtGui import QAction,QPixmap,QIcon
from PySide6.QtCore import Qt,QTimer
import qrcode
from config import APP_NAME,APP_VERSION,PORT,TOKEN_MIN_LENGTH
from crypto_vault import load_token,save_token,delete_token
import server
ROOT=Path(__file__).resolve().parent
class MoteWindow(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle(f"{APP_NAME} · {APP_VERSION}"); self.resize(540,720); self.thread=None; self.paused=False
  self.setStyleSheet("QWidget{background:#101014;color:#e9e8ed;font-family:Segoe UI} QLabel{color:#d7d5df} QPushButton{background:#24232a;border:1px solid #393840;border-radius:12px;padding:11px;color:#f4f3f8} QPushButton:hover{background:#303039} QLineEdit{background:#19181d;border:1px solid #41404a;border-radius:10px;padding:10px;color:#fff} QCheckBox{padding:6px} QProgressBar{height:7px;border:0;background:#292830;border-radius:3px} QProgressBar::chunk{background:#a9a3ff;border-radius:3px}")
  w=QWidget(); self.setCentralWidget(w); lay=QVBoxLayout(w); lay.setContentsMargins(26,24,26,22); lay.setSpacing(13)
  head=QHBoxLayout(); title=QLabel("M O T E"); title.setStyleSheet("font-size:26px;letter-spacing:5px;font-family:Georgia"); head.addWidget(title); head.addStretch(); self.status=QLabel("●  STOPPED"); self.status.setStyleSheet("color:#999"); head.addWidget(self.status); lay.addLayout(head)
  self.banner=QLabel("Remote is disconnected. No phone can send commands."); self.banner.setWordWrap(True); self.banner.setStyleSheet("background:#1b1a20;border:1px solid #393740;border-radius:12px;padding:14px"); lay.addWidget(self.banner)
  lay.addWidget(QLabel("SECRET TOKEN")); self.token=QLineEdit(); self.token.setPlaceholderText("Create or enter a custom token (8+ characters)"); self.token.setEchoMode(QLineEdit.Password); lay.addWidget(self.token)
  row=QHBoxLayout(); self.show=QPushButton("Show"); self.show.clicked.connect(self.toggle_show); gen=QPushButton("Generate random"); gen.clicked.connect(self.generate); lock=QPushButton("Lock & Save Token"); lock.clicked.connect(self.save); row.addWidget(self.show); row.addWidget(gen); row.addWidget(lock); lay.addLayout(row)
  self.strength=QProgressBar(); self.strength.setRange(0,100); self.strength.setTextVisible(False); lay.addWidget(self.strength); self.token.textChanged.connect(self.measure)
  self.qr=QLabel("QR appears after starting Mote"); self.qr.setAlignment(Qt.AlignCenter); self.qr.setMinimumHeight(190); self.qr.setStyleSheet("background:#19181d;border:1px solid #383740;border-radius:14px"); lay.addWidget(self.qr)
  self.address=QLabel("Phone URL will appear here"); self.address.setAlignment(Qt.AlignCenter); lay.addWidget(self.address)
  row2=QHBoxLayout(); self.start=QPushButton("Start Mote"); self.start.clicked.connect(self.start_mote); self.pause=QPushButton("Pause / Disconnect Remote"); self.pause.clicked.connect(self.toggle_pause); self.stop=QPushButton("Stop Mote"); self.stop.clicked.connect(self.stop_mote); row2.addWidget(self.start); row2.addWidget(self.pause); row2.addWidget(self.stop); lay.addLayout(row2)
  lay.addWidget(QLabel("LOCAL PERMISSIONS · disabled by default")); self.typing=QCheckBox("Keyboard typing input"); self.gamepad=QCheckBox("Virtual gamepad / controller input"); self.power=QCheckBox("Power, sleep and restart shortcuts");
  for cb in (self.typing,self.gamepad,self.power): cb.stateChanged.connect(self.permission_changed); lay.addWidget(cb)
  self.autostart=QCheckBox("Start Mote automatically when I sign in"); self.autostart.stateChanged.connect(self.set_autostart); lay.addWidget(self.autostart)
  lay.addStretch(); foot=QLabel("LAN only · Do not use on public Wi-Fi or forward port 8765."); foot.setStyleSheet("color:#999;font-size:11px"); lay.addWidget(foot)
  token=load_token();
  if token: self.token.setText(token); self.banner.setText("Saved token loaded from your OS credential store.")
  self.tray=QSystemTrayIcon(self); self.tray.setToolTip(APP_NAME); menu=QMenu(); menu.addAction("Show Mote",self.showNormal); menu.addAction("Pause / Disconnect",self.toggle_pause); menu.addAction("Stop Mote",self.stop_mote); menu.addAction("Exit",self.quit); self.tray.setContextMenu(menu); self.tray.show()
  self.poll=QTimer(self); self.poll.timeout.connect(self.refresh); self.poll.start(700)
 def toggle_show(self): self.token.setEchoMode(QLineEdit.Normal if self.token.echoMode()==QLineEdit.Password else QLineEdit.Password); self.show.setText("Hide" if self.token.echoMode()==QLineEdit.Normal else "Show")
 def generate(self): self.token.setText(secrets.token_urlsafe(18)); self.token.setEchoMode(QLineEdit.Password)
 def measure(self):
  s=self.token.text(); score=min(100,len(s)*5+(sum(c.isupper() for c in s)+sum(c.isdigit() for c in s)+sum(not c.isalnum() for c in s)*2)*4); self.strength.setValue(score)
 def save(self):
  token=self.token.text().strip()
  if len(token)<TOKEN_MIN_LENGTH: QMessageBox.warning(self,"Token too short",f"Use at least {TOKEN_MIN_LENGTH} characters."); return
  save_token(token); QMessageBox.information(self,"Token locked","Token saved to your operating system credential store.")
 def permission_changed(self):
  server.set_permissions({"typing":self.typing.isChecked(),"gamepad":self.gamepad.isChecked(),"power":self.power.isChecked()})
  if any((self.typing.isChecked(),self.gamepad.isChecked(),self.power.isChecked())): self.tray.showMessage("Mote permissions changed","Sensitive remote permissions enabled. Keep your phone on trusted Wi-Fi.",QSystemTrayIcon.Warning,4000)
 def start_mote(self):
  if not load_token(): self.save();
  if not load_token(): return
  if self.thread and self.thread.is_alive(): server.state["paused"]=False; self.paused=False; return
  self.thread=threading.Thread(target=server.run_server,daemon=True); self.thread.start(); server.state["paused"]=False; self.paused=False
 def toggle_pause(self):
  if not server.state["running"]: return
  server.state["paused"]=not server.state["paused"]; self.paused=server.state["paused"]
  if self.paused: server.sessions.clear(); server.state["connected"]=0; self.tray.showMessage("Mote remote paused","Phone access is paused and paired sessions disconnected.",QSystemTrayIcon.Information,3000)
 def stop_mote(self):
  server.stop_server(); self.paused=True; self.qr.clear(); self.qr.setText("QR appears after starting Mote"); self.address.setText("Phone URL will appear here"); self.tray.showMessage("Mote stopped","Remote connections have been disconnected.",QSystemTrayIcon.Information,2500)
 def refresh(self):
  running=server.state["running"]; connected=server.state["connected"]
  self.status.setText("●  ACTIVE" if running and not server.state["paused"] else "●  PAUSED" if running else "●  STOPPED"); self.status.setStyleSheet("color:#63df9b" if running and not server.state["paused"] else "color:#e4ae54" if running else "color:#888")
  if connected: self.banner.setText(f"PHONE CONNECTED · {connected} active session(s) · remote commands enabled"); self.banner.setStyleSheet("background:#14251d;border:1px solid #276341;border-radius:12px;padding:14px;color:#b8ffd0")
  elif running and server.state["paused"]: self.banner.setText("Remote paused. Existing phone sessions are disconnected.")
  elif running: self.banner.setText("Mote is running. Pair a phone on your trusted local Wi-Fi."); self.banner.setStyleSheet("background:#1b1a20;border:1px solid #393740;border-radius:12px;padding:14px")
  if running and not self.address.text().startswith("http"):
   ip=server.local_ip(); url=f"http://{ip}:{PORT}/"; self.address.setText(url+" · use QR or open address on phone")
   if ip!="127.0.0.1":
    qr=qrcode.make(url); temp=ROOT/"_mote_qr.png"; qr.save(temp); self.qr.setPixmap(QPixmap(str(temp)).scaled(180,180,Qt.KeepAspectRatio,Qt.SmoothTransformation))
  if connected and getattr(self,"_last_connected",0)!=connected: self.tray.showMessage("Mote phone connected","Remote is active. Pause / Disconnect is available on this desktop.",QSystemTrayIcon.Information,3500)
  self._last_connected=connected
 def set_autostart(self,state):
  # Per-user startup entry, pointing to the packaged executable. In source mode, startup shortcut is not enabled.
  if not getattr(sys,"frozen",False): QMessageBox.information(self,"Packaging required","Automatic startup is available in the packaged release build."); self.autostart.setChecked(False); return
  try:
   if platform.system()=="Windows":
    import winreg; key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE); name="MdotK Mote"; winreg.SetValueEx(key,name,0,winreg.REG_SZ,sys.executable) if self.autostart.isChecked() else winreg.DeleteValue(key,name); winreg.CloseKey(key)
   else: QMessageBox.information(self,"Autostart","Use your OS login-item settings to manage autostart for this app.")
  except Exception as e: QMessageBox.warning(self,"Autostart",str(e))
 def quit(self): self.stop_mote(); QApplication.quit()
 def closeEvent(self,event): self.hide(); event.ignore()
def main(): app=QApplication(sys.argv); app.setQuitOnLastWindowClosed(False); window=MoteWindow(); window.show(); sys.exit(app.exec())
if __name__=="__main__": main()
