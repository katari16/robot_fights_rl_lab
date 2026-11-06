import { createEngine } from './engine/mjswan.js';

const $ = (id) => document.getElementById(id);
const cameras = {
  arena: {lookat:[0,0,.55],distance:5.6,azimuth:105,elevation:-31,fovy:45},
  ringside: {lookat:[0,0,.8],distance:3.5,azimuth:95,elevation:-19,fovy:45},
  overhead: {lookat:[0,0,0],distance:6,azimuth:90,elevation:-85,fovy:45},
};
let engine, motion, seconds=0, playing=true, last=performance.now(), loop;

function poseAt(time) {
  const frame=(time*motion.fps)%motion.qpos.length, i=Math.floor(frame), w=frame-i;
  const a=motion.qpos[i], b=motion.qpos[(i+1)%motion.qpos.length];
  const pose=a.map((v,j)=>v*(1-w)+b[j]*w);
  for (const start of motion.quaternion_starts) {
    const qa=a.slice(start,start+4), qb=b.slice(start,start+4);
    let dot=qa.reduce((s,v,j)=>s+v*qb[j],0);
    if(dot<0){for(let j=0;j<4;j++)qb[j]*=-1;dot=-dot;}
    const theta=Math.acos(Math.min(1,Math.max(-1,dot)));
    for(let j=0;j<4;j++)pose[start+j]=dot>.9995?qa[j]*(1-w)+qb[j]*w:
      (qa[j]*Math.sin((1-w)*theta)+qb[j]*Math.sin(w*theta))/Math.sin(theta);
  }
  return pose;
}
function showPose(){
  engine.setPose($('mode').value==='nominal'?motion.nominal:poseAt(seconds));
  $('timeline').value=seconds/(motion.qpos.length/motion.fps);
  $('time').textContent=`${seconds.toFixed(1)} s`;
}
function tick(now){
  if(playing&&$('mode').value==='replay') seconds=(seconds+Math.min((now-last)/1000,.1)*Number($('speed').value))%(motion.qpos.length/motion.fps);
  last=now;showPose();loop=requestAnimationFrame(tick);
}
async function fetchOK(path){const r=await fetch(path);if(!r.ok)throw new Error(`${path}: HTTP ${r.status}`);return r;}
try{
  const [modelResponse,motionResponse]=await Promise.all([fetchOK('scene.mjz'),fetchOK('motion.json')]);
  motion=await motionResponse.json();
  document.querySelector('.badge').textContent=motion.label||'Reference motion';
  $('mode').querySelector('[value="replay"]').textContent=motion.description||'Jab recording';
  if(motion.detail) document.querySelector('header p').textContent=motion.detail;
  if(motion.segments){
    const select=document.createElement('select');select.setAttribute('aria-label','Skill');
    for(const part of motion.segments)select.add(new Option(part.name,String(part.start)));
    select.onchange=()=>{seconds=Number(select.value);$('mode').value='replay';showPose();};
    document.querySelector('.controls').append(select);
  }
  engine=await createEngine($('viewport'));
  await engine.loadScene({model:await modelResponse.arrayBuffer(),viewer:{...cameras.arena,originType:'WORLD',enableReflections:false,enableShadows:true}});
  engine.pause();
  engine.interaction.setMode('view');
  $('mode').value=motion.initial_mode;
  if(motion.initial_mode==='nominal') $('mode').querySelector('[value="replay"]').disabled=true;
  const initialSpeed=String(motion.initial_speed);
  if(![...$('speed').options].some(o=>o.value===initialSpeed)) $('speed').add(new Option(`${initialSpeed}×`,initialSpeed));
  $('speed').value=initialSpeed;
  $('status').hidden=true;
  $('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';};
  $('reset').onclick=()=>{seconds=0;showPose();};
  $('timeline').oninput=()=>{seconds=Number($('timeline').value)*(motion.qpos.length-1)/motion.fps;showPose();};
  $('camera').onchange=()=>engine.camera.set(cameras[$('camera').value]);
  $('mode').onchange=()=>{seconds=0;showPose();};
  document.addEventListener('keydown',(event)=>{if(event.code==='Space'&&event.target===document.body){event.preventDefault();$('play').click();}});
  // Expose readiness and the public engine for reproducible browser acceptance checks.
  window.arenaDemo={engine,motion,seek:(time)=>{seconds=time;showPose();},get time(){return seconds;}};
  loop=requestAnimationFrame(tick);
}catch(error){$('status').textContent=`Could not load the arena: ${error.message}`;console.error(error);}
window.addEventListener('pagehide',()=>{cancelAnimationFrame(loop);engine?.dispose();});
