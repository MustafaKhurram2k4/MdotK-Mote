const PBKDF_ITER=600000;
const enc=new TextEncoder(), dec=new TextDecoder();
export async function deriveSessionKey(token,salt,iterations=PBKDF_ITER){
 const material=await crypto.subtle.importKey('raw',enc.encode(token),'PBKDF2',false,['deriveKey']);
 return crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations,hash:'SHA-256'},material,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
}
export async function seal(key,seq,payload){
 const ts=Math.floor(Date.now()/1000), nonce=crypto.getRandomValues(new Uint8Array(12)), aad=enc.encode(`${seq}:${ts}`);
 const data=await crypto.subtle.encrypt({name:'AES-GCM',iv:nonce,additionalData:aad},key,enc.encode(JSON.stringify(payload)));
 return {seq,ts,nonce:btoa(String.fromCharCode(...nonce)),data:btoa(String.fromCharCode(...new Uint8Array(data)))};
}
export async function openSeal(key,envelope,expectedSeq){
 if(envelope.seq!==expectedSeq||Math.abs(Date.now()/1000-envelope.ts)>90) throw new Error('Sequence/timestamp validation failed');
 const nonce=Uint8Array.from(atob(envelope.nonce),c=>c.charCodeAt(0)), data=Uint8Array.from(atob(envelope.data),c=>c.charCodeAt(0));
 const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:nonce,additionalData:enc.encode(`${envelope.seq}:${envelope.ts}`)},key,data);
 return JSON.parse(dec.decode(plain));
}
export async function saveSession(slot,session,key){
 const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('mote-pairings',1);r.onupgradeneeded=()=>r.result.createObjectStore('slots');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
 await new Promise((resolve,reject)=>{const tx=db.transaction('slots','readwrite');tx.objectStore('slots').put({session,key,slot,created:Date.now()},String(slot));tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);});db.close();
}
export async function getSession(slot){const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('mote-pairings',1);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});const value=await new Promise((resolve,reject)=>{const tx=db.transaction('slots');const r=tx.objectStore('slots').get(String(slot));r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});db.close();return value||null;}
export async function removeSession(slot){const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('mote-pairings',1);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});await new Promise((resolve,reject)=>{const tx=db.transaction('slots','readwrite');tx.objectStore('slots').delete(String(slot));tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);});db.close();}
