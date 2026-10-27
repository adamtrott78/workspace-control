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
    constructor(){
      this.children=[];
      this.textContent="";
      this.className="";
      this.scrollTop=0;
      this.clientHeight=100;
      this.scrollHeight=100;
      this.style={values:new Map(),setProperty(name,value){this.values.set(name,value);},getPropertyValue(name){return this.values.get(name)??"";}};
      this.top=0;
      this.bottom=0;
      this.height=180;
    }
    append(...parts){this.children.push(...parts);}
    replaceChildren(...parts){
      this.children=parts;
      this.children.forEach((child,i)=>{child.top=i*50;child.bottom=(i+1)*50;});
      this.scrollHeight=Math.max(100,parts.length*50);
    }
    getBoundingClientRect(){return {top:this.top,bottom:this.bottom,height:this.height};}
  }
  const elems=new Map();
  for(const key of ["app","title","state","history","footer","executor","ui-seen","progress-age"])elems.set(key,new El());
  const handlers=new Map();
  const messages=[];
  let timers=[],seq=0,hidden=false;
  const first=snapshot(["One"]);
  const parent={postMessage(message){messages.push(message);}};
  const window={parent,openai:{toolInput:{task_id:"task-a"},toolOutput:{structuredContent:first}},addEventListener(name,fn){handlers.set("window:"+name,fn);}};
  const document={
    get hidden(){return hidden;},
    documentElement:{scrollHeight:900},
    body:{scrollHeight:900},
    getElementById(id){return elems.get(id);},
    createElement(){return new El();},
    addEventListener(name,fn){handlers.set("document:"+name,fn);}
  };
  function setTimeoutFake(fn,delay){const id=++seq;timers.push({id,fn,delay});return id;}
  function clearTimeoutFake(id){timers=timers.filter(t=>t.id!==id);}
  const context={window,document,Date,Error,Promise,Map,String,Array,Math,Number,setTimeout:setTimeoutFake,clearTimeout:clearTimeoutFake};
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

function snapshot(messages,{active=true,superseded=false,completed=false,startSequence=1}={}){
  const history=messages.map((message,i)=>({
    task_id:"task-a",
    turn_id:"turn-a",
    sequence:startSequence+i,
    state:completed&&i===messages.length-1?"done":"working",
    message,
    updated_at:"2026-10-06T10:00:"+String(i+1).padStart(2,"0")+"Z"
  }));
  const recent=history.slice(-3);
  return {
    task_id:"task-a",
    turn_id:"turn-a",
    heartbeat:history.at(-1),
    recent,
    turn_history:history,
    active,
    superseded,
    completed,
    last_executor_touch_at:"2026-10-06T10:00:00Z",
    last_ui_seen_at:null
  };
}

function pollResult(messages,{afterSequence=1,turnStatus="active",resync=false,startSequence=1}={}){
  const history=snapshot(messages,{completed:turnStatus==="completed",startSequence}).turn_history;
  return {
    task_id:"task-a",
    turn_id:"turn-a",
    turn_status:turnStatus,
    updates:resync?history:history.filter(item=>item.sequence>afterSequence),
    resync,
    last_executor_touch_at:"2026-10-06T10:00:10Z",
    last_ui_seen_at:"2026-10-06T10:00:11Z"
  };
}

test("mounted card uses delta poll and preserves full rendered history and intrinsic sizing",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  const call=h.handleNext("tools/call",{structuredContent:pollResult(["One","Two","Three","Four","Five"])});
  assert.equal(call.params.name,"heartbeat_poll");
  assert.equal(call.params.arguments.task_id,"task-a");
  assert.equal(call.params.arguments.turn_id,"turn-a");
  assert.equal(call.params.arguments.after_sequence,1);
  await h.flush();
  assert.deepEqual(h.elems.get("history").children.map(x=>x.children[0].textContent),["One","Two","Three","Four","Five"]);
  assert.equal(h.elems.get("history").className,"history");
  assert.equal(h.elems.get("footer").textContent,"5 updates · current turn · live");
  assert.ok(h.messages.some(x=>x.method==="ui/notifications/size-changed"&&x.params.height===180));
  assert.equal(h.messages.some(x=>x.method==="ui/notifications/size-changed"&&x.params.height===900),false);
});

test("no-change delta poll does not discard cached history",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  const call=h.handleNext("tools/call",{structuredContent:pollResult(["One"])});
  await h.flush();
  assert.equal(call.params.arguments.after_sequence,1);
  assert.deepEqual(h.elems.get("history").children.map(x=>x.children[0].textContent),["One"]);
  assert.equal(h.elems.get("footer").textContent,"1 update · current turn · live");
  assert.equal(h.elems.get("executor").textContent.startsWith("Executor signal:"),true);
});

test("bounded resync replaces cached history with retained server window",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  h.handleNext("tools/call",{structuredContent:pollResult(["Three","Four","Five","Six"],{resync:true,startSequence:3})});
  await h.flush();
  assert.deepEqual(h.elems.get("history").children.map(x=>x.children[0].textContent),["Three","Four","Five","Six"]);
  assert.equal(h.elems.get("footer").textContent,"4 updates · current turn · live");
});

test("sixth update caps history at five-entry height and preserves deliberate upward scroll",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  h.handleNext("tools/call",{structuredContent:pollResult(["One","Two","Three","Four","Five"])});
  await h.flush();
  const history=h.elems.get("history");
  assert.equal(history.className,"history");
  assert.equal(history.scrollTop,0);

  history.scrollTop=0;
  await h.runTimer();
  const call=h.handleNext("tools/call",{structuredContent:pollResult(["One","Two","Three","Four","Five","Six"],{afterSequence:5})});
  assert.equal(call.params.arguments.after_sequence,5);
  await h.flush();
  assert.equal(history.className,"history capped");
  assert.equal(history.style.getPropertyValue("--five-update-height"),"250px");
  assert.equal(history.scrollTop,0);
});

test("superseded turn becomes static and stops polling without semantic retransmission",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  h.handleNext("tools/call",{structuredContent:pollResult(["One"],{turnStatus:"superseded"})});
  await h.flush();
  assert.equal(h.elems.get("state").textContent,"superseded");
  assert.equal(h.timers.length,0);
  assert.equal(h.elems.get("footer").textContent,"Prior assistant turn · no longer live");
});

test("completed turn stops polling after final delta",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();await h.runTimer();
  h.handleNext("tools/call",{structuredContent:pollResult(["One","Done"],{turnStatus:"completed"})});
  await h.flush();
  assert.equal(h.elems.get("state").textContent,"done");
  assert.equal(h.timers.length,0);
  assert.equal(h.elems.get("footer").textContent,"Turn complete · no longer live");
});

test("hidden and torn-down widgets do not keep polling",async()=>{
  const h=createHarness();
  h.handleNext("ui/initialize",{});await h.flush();
  h.setHidden(true);assert.equal(h.timers.length,0);
  h.setHidden(false);assert.ok(h.timers.length>0);
  h.teardown();assert.equal(h.timers.length,0);
});
