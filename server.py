"""Mote LAN server: phone gated HTTP, paired encrypted WebSocket actions."""
import asyncio, base64, hashlib, hmac, ipaddress, json, os, secrets, time, socket, threading
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from zeroconf import Zeroconf, ServiceInfo
from config import *
from crypto_vault import load_token, derive_key, decrypt_envelope, encrypt_envelope
from device_guard import request_class
from os_controller import HostController
from action_handlers import ActionHandlers
ROOT=Path(__file__).resolve().parent
app=FastAPI(title=APP_NAME,docs_url=None,redoc_url=None)
app.mount("/static",StaticFiles(directory=str(ROOT/"static")),name="static")
failures={}; sessions={}; state={"running":False,"paused":False,"permissions":{"typing":False,"gamepad":False,"power":False},"connected":0,"alerts":[]}
controller=HostController(state["permissions"]); handlers=ActionHandlers(controller)
lock=threading.RLock(); zeroconf=None; mdns_info=None; uv_server=None
class PairRequest(BaseModel): token:str=Field(min_length=8,max_length=256); slot:int=Field(ge=1,le=5)
def private_ip(ip):
 try: return ipaddress.ip_address(ip).is_private or ip in ("127.0.0.1","::1")
 except ValueError: return False
def client_ip(request): return request.client.host if request.client else "unknown"
def locked(ip):
 record=failures.get(ip,{"count":0,"until":0}); return record["until"]>time.time()
def bad_token(ip):
 rec=failures.setdefault(ip,{"count":0,"until":0}); rec["count"]+=1
 if rec["count"]>=MAX_FAILED_ATTEMPTS: rec["until"]=time.time()+LOCKOUT_SECONDS; rec["count"]=0; state["alerts"].append(f"Security lockout: {ip} blocked for 15 minutes")
def reset_fail(ip): failures.pop(ip,None)
def phone_gate(request): return request_class(request)=="phone"
@app.get("/api/status")
async def status(): return {"running":state["running"],"paused":state["paused"],"connected":state["connected"],"permissions":dict(state["permissions"])}
@app.get("/api/desktop-info")
async def desktop_info(): return {"release":GITHUB_RELEASES_URL}
@app.post("/api/pair")
async def pair(req:PairRequest, request:Request):
 ip=client_ip(request)
 if request_class(request)!="phone": raise HTTPException(403,"Phone-only remote")
 if not private_ip(ip): raise HTTPException(403,"LAN-only pairing")
 if locked(ip): raise HTTPException(429,"Temporarily locked after failed pairing attempts")
 token=load_token()
 if not token or not hmac.compare_digest(req.token,token): bad_token(ip); raise HTTPException(401,"Invalid token")
 reset_fail(ip); salt=os.urandom(16); session_id=secrets.token_urlsafe(24)
 sessions[session_id]={"key":derive_key(token,salt),"seq":1,"slot":req.slot,"ip":ip,"created":time.time(),"last":time.time(),"ack_seq":1}
 return {"session":session_id,"salt":base64.b64encode(salt).decode(),"iterations":PBKDF2_ITERATIONS,"ws":"/ws"}
@app.websocket("/ws")
async def ws(websocket:WebSocket):
 ip=websocket.client.host if websocket.client else "unknown"
 if not private_ip(ip): await websocket.close(code=1008); return
 await websocket.accept()
 session_id=websocket.query_params.get("session",""); sess=sessions.get(session_id)
 if not sess or sess["ip"]!=ip: await websocket.close(code=1008); return
 if state["paused"] or not state["running"]: await websocket.close(code=1013); return
 state["connected"]+=1; sess["last"]=time.time()
 try:
  while True:
   raw=await websocket.receive_json(); sess=sessions.get(session_id)
   if not sess or time.time()-sess["created"]>SESSION_TTL_SECONDS: await websocket.close(code=1008); break
   try:
    payload=decrypt_envelope(sess["key"],raw,sess["seq"]); sess["seq"]+=1; sess["last"]=time.time()
    if not state["running"] or state["paused"]: raise RuntimeError("Remote paused")
    result=handlers.dispatch(payload); await websocket.send_json(encrypt_envelope(sess["key"],sess["ack_seq"],{"ok":True,"seq":sess["seq"]-1,"result":result})); sess["ack_seq"]+=1
   except Exception as exc:
    await websocket.send_json(encrypt_envelope(sess["key"],sess["ack_seq"],{"ok":False,"error":str(exc)[:160]})); sess["ack_seq"]+=1
 except WebSocketDisconnect: pass
 finally:
  state["connected"]=max(0,state["connected"]-1); sessions.pop(session_id,None)
@app.get("/{path:path}")
async def index(path:str,request:Request):
 kind=request_class(request)
 if kind=="phone": return FileResponse(ROOT/"static/index.html")
 if kind=="tablet": return FileResponse(ROOT/"static/tablet.html")
 return FileResponse(ROOT/"static/desktop.html")
def set_permissions(permissions):
 state["permissions"].update({k:bool(permissions.get(k,False)) for k in state["permissions"]}); controller.permissions=state["permissions"]
 if not state["permissions"]["typing"] or not state["permissions"]["gamepad"]: sessions.clear()
def start_mdns(ip):
 global zeroconf,mdns_info
 try:
  zeroconf=Zeroconf(); mdns_info=ServiceInfo("_http._tcp.local.","Mote Remote._http._tcp.local.",addresses=[socket.inet_aton(ip)],port=PORT,properties={"path":"/"},server="mote.local."); zeroconf.register_service(mdns_info)
 except Exception: stop_mdns()
def stop_mdns():
 global zeroconf,mdns_info
 try:
  if zeroconf and mdns_info: zeroconf.unregister_service(mdns_info)
  if zeroconf: zeroconf.close()
 except Exception: pass
 zeroconf=None; mdns_info=None

def local_ip():
 try:
  sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); sock.connect(("192.0.2.1",80)); ip=sock.getsockname()[0]; sock.close()
  if private_ip(ip): return ip
 except Exception: pass
 return "127.0.0.1"
def run_server():
 global uv_server
 import uvicorn
 config=uvicorn.Config(app,host=HOST,port=PORT,log_level="warning")
 uv_server=uvicorn.Server(config); state["running"]=True; state["paused"]=False; start_mdns(local_ip())
 uv_server.run(); state["running"]=False; stop_mdns(); uv_server=None

def stop_server():
 global uv_server
 state["paused"]=True; sessions.clear(); state["connected"]=0
 if uv_server: uv_server.should_exit=True
