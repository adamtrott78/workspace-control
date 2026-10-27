import test from "node:test";
import assert from "node:assert/strict";
import { HeartbeatStore } from "../src/store.js";

function makeStore(){
  let n=0;
  return new HeartbeatStore({turnIdFactory:()=>`turn-${++n}`});
}

test("beginTurn creates an explicit turn and first heartbeat",()=>{
  const store=makeStore();
  const turn=store.beginTurn({
    sessionId:"chat-a",taskId:"task-a",message:"Starting",state:"working",
    now:new Date("2026-10-06T10:00:00Z")
  });
  assert.equal(turn.turn_id,"turn-1");
  assert.equal(turn.active,true);
  assert.equal(turn.heartbeat.turn_id,"turn-1");
  assert.deepEqual(turn.recent.map(x=>x.message),["Starting"]);
});

test("same conversation begins a new turn and supersedes the old one",()=>{
  const store=makeStore();
  const a=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A1",state:"working"});
  store.updateTurn({sessionId:"chat-a",taskId:"task-a",turnId:a.turn_id,message:"A2",state:"working"});
  const b=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"B1",state:"working"});
  assert.equal(store.getTurnSnapshot({taskId:"task-a",turnId:a.turn_id}).superseded,true);
  assert.equal(store.getTurnSnapshot({taskId:"task-a",turnId:a.turn_id}).active,false);
  assert.equal(b.turn_id,"turn-2");
  assert.deepEqual(b.recent.map(x=>x.message),["B1"]);
  assert.deepEqual(store.getSnapshot({sessionId:"chat-a",taskId:"task-a"}).history.map(x=>x.message),["A1","A2","B1"]);
});

test("later updates require the exact active turn and conversation",()=>{
  const store=makeStore();
  const a=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"Start",state:"working"});
  const hb=store.updateTurn({sessionId:"chat-a",taskId:"task-a",turnId:a.turn_id,message:"Next",state:"waiting"});
  assert.equal(hb.turn_id,a.turn_id);
  assert.throws(()=>store.updateTurn({
    sessionId:"chat-b",taskId:"task-a",turnId:a.turn_id,message:"Wrong chat",state:"working"
  }),/HEARTBEAT_TURN_CONVERSATION_MISMATCH/);
  assert.throws(()=>store.updateTurn({
    sessionId:"chat-a",taskId:"task-b",turnId:a.turn_id,message:"Wrong task",state:"working"
  }),/HEARTBEAT_TURN_TASK_MISMATCH/);
});

test("superseded turn IDs fail closed",()=>{
  const store=makeStore();
  const a=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A",state:"working"});
  store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"B",state:"working"});
  assert.throws(()=>store.updateTurn({
    sessionId:"chat-a",taskId:"task-a",turnId:a.turn_id,message:"Stale",state:"working"
  }),/HEARTBEAT_TURN_STALE/);
});

test("active task ownership rejects a different conversation",()=>{
  const store=makeStore();
  store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A",state:"working"});
  assert.throws(()=>store.beginTurn({
    sessionId:"chat-b",taskId:"task-a",message:"B",state:"working"
  }),/HEARTBEAT_TASK_OWNED_BY_ANOTHER_CONVERSATION/);
});

test("done closes the turn and releases task ownership",()=>{
  const store=makeStore();
  const a=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A",state:"working"});
  store.updateTurn({sessionId:"chat-a",taskId:"task-a",turnId:a.turn_id,message:"Done",state:"done"});
  const closed=store.getTurnSnapshot({taskId:"task-a",turnId:a.turn_id});
  assert.equal(closed.active,false);
  assert.equal(closed.completed,true);
  const b=store.beginTurn({sessionId:"chat-b",taskId:"task-a",message:"Reopened",state:"working"});
  assert.equal(b.active,true);
});

test("turn snapshot exposes full bounded history plus rolling-three without crossing turns",()=>{
  const store=makeStore();
  const a=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A1",state:"working"});
  for(let i=2;i<=5;i++) store.updateTurn({
    sessionId:"chat-a",taskId:"task-a",turnId:a.turn_id,message:"A"+i,state:"working"
  });
  const b=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"B1",state:"working"});
  const aSnapshot=store.getTurnSnapshot({taskId:"task-a",turnId:a.turn_id});
  const bSnapshot=store.getTurnSnapshot({taskId:"task-a",turnId:b.turn_id});
  assert.deepEqual(aSnapshot.turn_history.map(x=>x.message),["A1","A2","A3","A4","A5"]);
  assert.deepEqual(aSnapshot.recent.map(x=>x.message),["A3","A4","A5"]);
  assert.deepEqual(bSnapshot.turn_history.map(x=>x.message),["B1"]);
  assert.deepEqual(bSnapshot.recent.map(x=>x.message),["B1"]);
});

test("turn history respects the configured bound",()=>{
  const store=new HeartbeatStore({turnHistoryLimit:4,turnIdFactory:()=>"turn-bounded"});
  const turn=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A1",state:"working"});
  for(let i=2;i<=6;i++) store.updateTurn({
    sessionId:"chat-a",taskId:"task-a",turnId:turn.turn_id,message:"A"+i,state:"working"
  });
  const snapshot=store.getTurnSnapshot({taskId:"task-a",turnId:turn.turn_id});
  assert.deepEqual(snapshot.turn_history.map(x=>x.message),["A3","A4","A5","A6"]);
  assert.deepEqual(snapshot.recent.map(x=>x.message),["A4","A5","A6"]);
});

test("task history remains available across turns",()=>{
  const store=makeStore();
  const a=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A",state:"working"});
  store.updateTurn({sessionId:"chat-a",taskId:"task-a",turnId:a.turn_id,message:"A2",state:"working"});
  store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"B",state:"working"});
  const snapshot=store.getSnapshot({sessionId:"different",taskId:"task-a"});
  assert.deepEqual(snapshot.history.map(x=>x.message),["A","A2","B"]);
  assert.ok(snapshot.history.every(x=>x.turn_id));
});

test("missing task still returns empty task-level snapshot",()=>{
  const store=makeStore();
  assert.deepEqual(store.getSnapshot({sessionId:"chat-a"}),{
    heartbeat:null,history:[],timeline:[]
  });
});

test("silent executor touch preserves all semantic history, sequence and card history",()=>{
  const store=makeStore();
  const begin=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"working",now:new Date("2026-10-22T10:00:00Z")});
  const old=store.getTurnSnapshot({taskId:"task-a",turnId:begin.turn_id});
  assert.deepEqual(store.touchTurn({sessionId:"chat-a",taskId:"task-a",turnId:begin.turn_id,now:new Date("2026-10-22T10:01:00Z")}),{acknowledged:true});
  const touched=store.getTurnSnapshot({taskId:"task-a",turnId:begin.turn_id});
  assert.equal(touched.last_executor_touch_at,"2026-10-22T10:01:00.000Z");
  assert.equal(touched.heartbeat.sequence,old.heartbeat.sequence);
  assert.deepEqual(touched.turn_history,old.turn_history);
  assert.deepEqual(touched.recent,old.recent);
  assert.equal(touched.last_ui_seen_at,null);
  const polled=store.observeUi({taskId:"task-a",turnId:begin.turn_id,now:new Date("2026-10-22T10:02:00Z")});
  assert.equal(polled.last_ui_seen_at,"2026-10-22T10:02:00.000Z");
  assert.equal(polled.last_executor_touch_at,touched.last_executor_touch_at);
  assert.deepEqual(polled.turn_history,old.turn_history);
  assert.throws(()=>store.touchTurn({sessionId:"chat-b",taskId:"task-a",turnId:begin.turn_id}),/CONVERSATION_MISMATCH/);
  assert.throws(()=>store.touchTurn({sessionId:"chat-a",taskId:"other",turnId:begin.turn_id}),/TASK_MISMATCH/);
  store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"next"});
  assert.throws(()=>store.touchTurn({sessionId:"chat-a",taskId:"task-a",turnId:begin.turn_id}),/TURN_STALE/);
});


test("delta poll returns no semantic payload when sequence is unchanged",()=>{
  const store=makeStore();
  const begin=store.beginTurn({
    sessionId:"chat-a",taskId:"task-a",message:"A1",state:"working",
    now:new Date("2026-10-26T20:00:00Z")
  });
  const poll=store.observeUiDelta({
    taskId:"task-a",turnId:begin.turn_id,afterSequence:begin.heartbeat.sequence,
    now:new Date("2026-10-26T20:00:01Z")
  });
  assert.equal(poll.turn_status,"active");
  assert.equal(poll.resync,false);
  assert.deepEqual(poll.updates,[]);
  assert.equal(poll.last_ui_seen_at,"2026-10-26T20:00:01.000Z");
  assert.equal(poll.last_executor_touch_at,"2026-10-26T20:00:00.000Z");
});

test("delta poll returns only entries newer than afterSequence",()=>{
  const store=makeStore();
  const begin=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A1",state:"working"});
  store.updateTurn({sessionId:"chat-a",taskId:"task-a",turnId:begin.turn_id,message:"A2",state:"working"});
  store.updateTurn({sessionId:"chat-a",taskId:"task-a",turnId:begin.turn_id,message:"A3",state:"waiting"});
  const poll=store.observeUiDelta({
    taskId:"task-a",turnId:begin.turn_id,afterSequence:begin.heartbeat.sequence
  });
  assert.equal(poll.resync,false);
  assert.deepEqual(poll.updates.map(x=>x.message),["A2","A3"]);
});

test("delta poll bounded-resyncs when caller predates retained turn history",()=>{
  const store=new HeartbeatStore({turnHistoryLimit:4,turnIdFactory:()=>"turn-bounded-delta"});
  const begin=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A1",state:"working"});
  for(let i=2;i<=6;i++) store.updateTurn({
    sessionId:"chat-a",taskId:"task-a",turnId:begin.turn_id,message:"A"+i,state:"working"
  });
  const poll=store.observeUiDelta({
    taskId:"task-a",turnId:begin.turn_id,afterSequence:1
  });
  assert.equal(poll.resync,true);
  assert.deepEqual(poll.updates.map(x=>x.message),["A3","A4","A5","A6"]);
});

test("delta poll exposes superseded state without creating semantic history",()=>{
  const store=makeStore();
  const a=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A1",state:"working"});
  store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"B1",state:"working"});
  const poll=store.observeUiDelta({taskId:"task-a",turnId:a.turn_id,afterSequence:a.heartbeat.sequence});
  assert.equal(poll.turn_status,"superseded");
  assert.deepEqual(poll.updates,[]);
  assert.equal(store.observeUiDelta({taskId:"wrong",turnId:a.turn_id,afterSequence:0}),null);
});
