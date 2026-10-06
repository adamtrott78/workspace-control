import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const html=readFileSync(new URL("../public/heartbeat-live-card.html",import.meta.url),"utf8");
const script=html.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];
assert.ok(script,"live-card module script exists");

function createHarness(){
  class El {
    constructor(){this.children=[];this.textContent="";this.className="";this.innerHTML="";}
    append(...parts){this.children.push(...parts);}
    replaceChildren(...parts){this.children=parts;}
  }
  const elems=new Map();
  for(const key of ["title","state","history","footer"])elems.set(key,new El());
  const handlers=new Map();
  const messages=[];
  let timers=[];
  let seq=0;
  let hidden=false;
  const seeded={task_id:"task-a",heartbeat:{task_id:"task-a",sequence:1,state:"working",message:"First",updated_at:"2026-10-05T01:00:01Z"},recent:[{task_id:"task-a",sequence:1,state:"working",message:"First",updated_at:"2026-10-05T01:00:01Z"}]};
  const parent={postMessage(message){messages.push(message);}};
  const window={
    parent,
    openai:{toolInput:{task_id:"task-a"},toolOutput:{structuredContent:seeded}},
    addEventListener(name,fn){handlers.set("window:"+name,fn);}
  };
  const document={
    get hidden(){return hidden;},
    getElementById(id){return elems.get(id);},
    createElement(){return new El();},
    addEventListener(name,fn){handlers.set("document:"+name,fn);}
  };
  function setTimeoutFake(fn,delay){const id=++seq;timers.push({id,fn,delay});return id;}
  function clearTimeoutFake(id){timers=timers.filter(t=>t.id!==id);}
  const context={window,document,Date,Error,Promise,Map,String,Array,Math,setTimeout:setTimeoutFake,clearTimeout:clearTimeoutFake};
  vm.runInNewContext(script,context,{filename:"heartbeat-live-card.js"});
  function reply(id,result,error){
    handlers.get("window:message")({source:parent,data:{jsonrpc:"2.0",id,...(error?{error}:{result})}});
  }
  function handleNext(method,result){
    const at=messages.findIndex(x=>x.method===method);
    assert.ok(at>=0,"missing "+method);
    const [msg]=messages.splice(at,1);
    reply(msg.id,result);
    return msg;
  }
  async function flush(){for(let i=0;i<5;i++)await Promise.resolve();}
  async function runTimer(){
    assert.ok(timers.length);
    const timer=timers.shift();
    timer.fn();
    await flush();
    return timer;
  }
  return {window,elems,messages,handlers,handleNext,flush,runTimer,get timers(){return timers},setHidden(x){hidden=x;handlers.get("document:visibilitychange")?.();}};
}
function snapshot(n,task="task-a"){
  const recent=Array.from({length:Math.min(n,3)},(_,i)=>{
    const id=n-Math.min(n,3)+1+i;
    return {task_id:task,sequence:id,state:"working",message:"Update "+id,updated_at:"2026-10-05T01:00:"+String(id).padStart(2,"0")+"Z"};
  });
  return {task_id:task,heartbeat:recent.at(-1),recent};
}
test("one mounted card requests its own subsequent task-local snapshots and rolls forward",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});
  await h.flush();
  assert.ok(h.messages.some(x=>x.method==="ui/notifications/initialized"));
  await h.runTimer();
  const first=h.handleNext("tools/call",{structuredContent:snapshot(2)});
  assert.equal(first.params.name,"heartbeat_snapshot");
  assert.equal(first.params.arguments.task_id,"task-a");
  await h.flush();
  assert.deepEqual(h.elems.get("history").children.map(x=>x.children[0].textContent),["Update 1","Update 2"]);
  await h.runTimer();
  h.handleNext("tools/call",{structuredContent:snapshot(5)});
  await h.flush();
  assert.deepEqual(h.elems.get("history").children.map(x=>x.children[0].textContent),["Update 3","Update 4","Update 5"]);
  assert.equal(h.elems.get("title").textContent,"task-a");
  assert.equal(h.messages.filter(x=>x.method==="heartbeat_open").length,0);
});
test("wrong-task responses never replace the current card",async()=>{
  const h=createHarness();h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  h.handleNext("tools/call",{structuredContent:snapshot(3,"task-b")});await h.flush();
  assert.equal(h.elems.get("title").textContent,"task-a");
  assert.deepEqual(h.elems.get("history").children.map(x=>x.children[0].textContent),["First"]);
});
test("hidden widgets do not request snapshots and resume when visible",async()=>{
  const h=createHarness();h.handleNext("ui/initialize",{});await h.flush();
  h.setHidden(true);
  assert.equal(h.timers.length,0);
  h.setHidden(false);await h.runTimer();
  assert.ok(h.messages.some(x=>x.method==="tools/call"));
});
test("after a done snapshot the card stops scheduling refreshes",async()=>{
  const h=createHarness();h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  const s=snapshot(3);s.heartbeat.state="done";
  h.handleNext("tools/call",{structuredContent:s});await h.flush();
  assert.equal(h.elems.get("state").textContent,"done");
  assert.equal(h.timers.length,0);
});
