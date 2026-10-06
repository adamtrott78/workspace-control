import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const html=readFileSync(new URL("../public/heartbeat-live-card.html",import.meta.url),"utf8");
const script=html.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];
assert.ok(script,"live-card module script exists");
assert.doesNotThrow(()=>new vm.Script(script,{filename:"heartbeat-live-card.js"}));

function createHarness(){
  class El{
    constructor(){this.children=[];this.textContent="";this.className="";}
    append(...parts){this.children.push(...parts);}
    replaceChildren(...parts){this.children=parts;}
  }
  const elems=new Map();
  for(const key of ["title","state","history","footer"])elems.set(key,new El());
  const handlers=new Map();
  const messages=[];
  let timers=[],seq=0,hidden=false;
  const first={task_id:"task-a",turn_id:"turn-a",heartbeat:{task_id:"task-a",turn_id:"turn-a",sequence:1,state:"working",message:"First",updated_at:"2026-10-06T10:00:01Z"},recent:[{task_id:"task-a",turn_id:"turn-a",sequence:1,state:"working",message:"First",updated_at:"2026-10-06T10:00:01Z"}],active:true,superseded:false,completed:false};
  const parent={postMessage(message){messages.push(message);}};
  const window={parent,openai:{toolInput:{task_id:"task-a"},toolOutput:{structuredContent:first}},addEventListener(name,fn){handlers.set("window:"+name,fn);}};
  const document={get hidden(){return hidden;},getElementById(id){return elems.get(id);},createElement(){return new El();},addEventListener(name,fn){handlers.set("document:"+name,fn);}};
  function setTimeoutFake(fn,delay){const id=++seq;timers.push({id,fn,delay});return id;}
  function clearTimeoutFake(id){timers=timers.filter(t=>t.id!==id);}
  const context={window,document,Date,Error,Promise,Map,String,Array,Math,setTimeout:setTimeoutFake,clearTimeout:clearTimeoutFake};
  vm.runInNewContext(script,context,{filename:"heartbeat-live-card.js"});
  function reply(id,result,error){handlers.get("window:message")({source:parent,data:{jsonrpc:"2.0",id,...(error?{error}:{result})}});}
  function handleNext(method,result){
    const at=messages.findIndex(x=>x.method===method);
    assert.ok(at>=0,"missing "+method);
    const [msg]=messages.splice(at,1);reply(msg.id,result);return msg;
  }
  async function flush(){for(let i=0;i<5;i++)await Promise.resolve();}
  async function runTimer(){assert.ok(timers.length);const timer=timers.shift();timer.fn();await flush();return timer;}
  return {elems,messages,handleNext,flush,runTimer,get timers(){return timers},setHidden(x){hidden=x;handlers.get("document:visibilitychange")?.();},teardown(){handlers.get("window:message")?.({source:parent,data:{jsonrpc:"2.0",method:"ui/resource-teardown"}});}};
}

function snapshot(messages,{active=true,superseded=false,completed=false}={}){
  const recent=messages.slice(-3).map((message,i)=>{
    const sequence=messages.length-Math.min(messages.length,3)+1+i;
    return {task_id:"task-a",turn_id:"turn-a",sequence,state:completed&&i===Math.min(messages.length,3)-1?"done":"working",message,updated_at:"2026-10-06T10:00:"+String(sequence).padStart(2,"0")+"Z"};
  });
  return {task_id:"task-a",turn_id:"turn-a",heartbeat:recent.at(-1),recent,active,superseded,completed};
}

test("one mounted card rolls only within its immutable turn",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  const call=h.handleNext("tools/call",{structuredContent:snapshot(["One","Two","Three","Four"])});
  assert.equal(call.params.name,"heartbeat_snapshot");
  assert.deepEqual(call.params.arguments,{task_id:"task-a",turn_id:"turn-a"});
  await h.flush();
  assert.deepEqual(h.elems.get("history").children.map(x=>x.children[0].textContent),["Two","Three","Four"]);
});

test("superseded turn becomes static and stops polling",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  h.handleNext("tools/call",{structuredContent:snapshot(["One","Two"],{active:false,superseded:true})});
  await h.flush();
  assert.equal(h.elems.get("state").textContent,"superseded");
  assert.equal(h.timers.length,0);
  assert.equal(h.elems.get("footer").textContent,"Prior assistant turn · no longer live");
});

test("completed turn stops polling",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  h.handleNext("tools/call",{structuredContent:snapshot(["One","Done"],{active:false,completed:true})});
  await h.flush();
  assert.equal(h.elems.get("state").textContent,"done");
  assert.equal(h.timers.length,0);
});

test("hidden and torn-down widgets do not keep polling",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();
  h.setHidden(true);assert.equal(h.timers.length,0);
  h.setHidden(false);assert.ok(h.timers.length>0);
  h.teardown();assert.equal(h.timers.length,0);
});
