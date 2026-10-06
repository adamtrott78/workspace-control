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

test("turn snapshot is rolling-three and never crosses turns",()=>{
  const store=makeStore();
  const a=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"A1",state:"working"});
  for(let i=2;i<=5;i++) store.updateTurn({
    sessionId:"chat-a",taskId:"task-a",turnId:a.turn_id,message:"A"+i,state:"working"
  });
  const b=store.beginTurn({sessionId:"chat-a",taskId:"task-a",message:"B1",state:"working"});
  assert.deepEqual(store.getTurnSnapshot({taskId:"task-a",turnId:a.turn_id}).recent.map(x=>x.message),["A3","A4","A5"]);
  assert.deepEqual(store.getTurnSnapshot({taskId:"task-a",turnId:b.turn_id}).recent.map(x=>x.message),["B1"]);
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
