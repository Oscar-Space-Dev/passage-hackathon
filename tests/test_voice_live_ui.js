'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

async function check(pending,sameProject=false){
  const calls=[];
  const session={projectId:sameProject?'new-project':null,pendingProjectId:'new-project',
    pendingReason:sameProject?'brain':'project',stopping:false,switching:false};
  const project={id:'new-project',approvals:pending?[{status:'pending'}]:[]};
  const context={
    S:{liveVoice:session,project:sameProject?project:null,projects:[]},
    window:{addEventListener:()=>{}},
    api:async url=>{calls.push('api '+url);return url==='/projects'?[project]:project;},
    stopLiveVoice:async()=>{calls.push('stop');context.S.liveVoice=null;},
    startLiveVoice:async()=>{calls.push('start');context.S.liveVoice={projectId:'new-project'};},
    renderView:()=>calls.push('render'),
    toast:text=>calls.push('toast '+text),
    encodeURIComponent,
  };
  const source=fs.readFileSync(path.join(__dirname,'../passage/static/voice-live.js'),'utf8');
  vm.runInNewContext(source,context);
  context.stopLiveVoice=async()=>{calls.push('stop');context.S.liveVoice=null;};
  context.startLiveVoice=async()=>{calls.push('start');context.S.liveVoice={projectId:'new-project'};};
  await context.switchLiveVoiceProject(session);
  assert.equal(context.S.project.id,'new-project');
  assert.deepEqual(calls.slice(0,4),[
    'api /projects/new-project','api /projects','stop','render']);
  assert.equal(calls.includes('start'),!pending);
  if(sameProject&&!pending)assert.ok(calls.includes('toast Modèle du projet mis à jour. La conversation continue.'));
}

(async()=>{
  await check(false);
  await check(true);
  await check(false,true);
  console.log('Voice project and model switch: 3 cases passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
