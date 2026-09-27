'use strict';

function liveVoiceStatus(message, state='listening') {
  const label=document.getElementById('live-voice-status');
  const orb=document.getElementById('live-voice-orb');
  if(label)label.textContent=message;
  if(orb)orb.dataset.state=state;
}

function liveVoiceTranscript({text,turnIdx,isUser}) {
  if(!S.liveVoice || !text?.trim())return;
  const session=S.liveVoice;
  const list=document.getElementById('live-voice-transcript');
  if(!list)return;
  const role=isUser?'user':'assistant';
  let row=session.transcriptRow;
  if(session.transcriptBoundary||!row||row.dataset.role!==role||row.dataset.turn!==String(turnIdx??'unknown'))row=null;
  if(!row){
    row=document.createElement('article');
    row.className=`live-voice-line ${role}`;
    row.dataset.turn=String(turnIdx??'unknown');
    row.dataset.role=role;
    const who=document.createElement('strong');who.textContent=isUser?'Vous':session.mode==='guide'?'Marguerite':'Passage';
    const content=document.createElement('p');
    row.append(who,content);
    if(!isUser){
      const replay=document.createElement('button');
      replay.type='button';replay.className='btn ghost small live-voice-replay';
      replay.dataset.action='voice-replay';replay.textContent='Écouter';
      row.append(replay);
    }
    list.append(row);session.transcriptRow=row;
  }
  session.transcriptBoundary=false;
  const content=row.querySelector('p');
  content.textContent+=(content.textContent && !/^\s/.test(text)?' ':'')+text;
  list.scrollTop=list.scrollHeight;
  liveVoiceStatus(isUser?'Je vous écoute…':session.mode==='guide'?'Marguerite répond…':'Passage répond…',isUser?'listening':'speaking');
}

async function switchLiveVoiceProject(session){
  if(session.stopping||session.switching||S.liveVoice!==session||!session.pendingProjectId)return;
  session.switching=true;
  const target=session.pendingProjectId;
  const reason=session.pendingReason;
  session.pendingProjectId=null;
  session.pendingReason=null;
  try{
    const project=await api('/projects/'+encodeURIComponent(target));
    const projects=await api('/projects');
    if(session.stopping||S.liveVoice!==session)return;
    await stopLiveVoice();
    S.project=project;S.projects=projects;renderView();
    if(project.approvals?.some(a=>a.status==='pending')){
      toast('Une action attend votre validation dans le projet.');return;
    }
    await startLiveVoice();
    toast(reason==='brain'?'Modèle du projet mis à jour. La conversation continue.':'Projet ouvert. La conversation continue ici.');
  }catch(error){session.switching=false;toast(error.message,true);}
}

async function startLiveVoice(mode='project'){
  if(S.liveVoice)return;
  const guideMode=mode==='guide';
  if(typeof SyncedAudioPlayer==='undefined')throw new Error('Le module de conversation vocale n’a pas pu se charger. Rechargez la page.');
  const status=await api('/voice/status');
  if(!status.configured||!status.voice_id)throw new Error('Configurez une clé et une voix Gradium dans Connexions.');
  const brain=guideMode?{engine:'direct',provider:'codex',model:'auto'}:projectBrain();
  const localExplicit=Boolean(!guideMode&&S.project?.brain_provider==='agent'&&brain?.provider==='ollama');
  if(brain?.engine!=='direct'||(brain?.provider!=='codex'&&!localExplicit))throw new Error('Choisissez un coordinateur direct et connectez votre compte ChatGPT dans Connexions.');
  if(brain.provider==='codex'){
    const account=await api('/brains/chatgpt/status');
    if(!account.connected)throw new Error('Connectez votre compte ChatGPT dans Connexions avant la conversation vocale.');
  }
  if(S.recording)await stopRecording(false);
  stopPlayingAudio();
  const root=document.getElementById('live-voice-root');
  const who=guideMode?'Marguerite':'Passage';
  root.innerHTML=`<section class="live-voice-stage" role="dialog" aria-modal="true" aria-label="Conversation vocale avec ${who}"><div class="live-voice-panel"><header><span>${who} · ${esc(S.project?.name||'Accueil')} · ${brain.provider==='codex'?'ChatGPT via Codex':'Ollama local'} + Gradium</span><button type="button" class="live-voice-close" data-action="voice-conversation" aria-label="Terminer la conversation">×</button></header><div id="live-voice-orb" class="live-voice-orb" data-state="connecting" aria-hidden="true">${icon('mic')}</div><h2 id="live-voice-status" role="status">Ouverture du micro…</h2><p class="live-voice-hint">${guideMode?'Parlez naturellement à Marguerite. Elle répond à voix haute et conserve vos échanges. Un plan d’actions apparaîtra pour votre validation.':'Parlez naturellement. Vous pouvez interrompre Passage en reprenant la parole.'+(S.project?'':' Pour conserver l’échange, créez ou ouvrez un projet à la voix.')}</p><div id="live-voice-transcript" class="live-voice-transcript" aria-label="Transcription de la conversation" aria-live="polite"></div><button type="button" class="btn live-voice-end" data-action="voice-conversation">Terminer</button></div></section>`;
  const session={mode,projectId:S.project?.id||null,player:null,ws:null,stopping:false,pendingProjectId:null,pendingReason:null,pendingGuideReview:false,switching:false,transcriptRow:null,transcriptBoundary:false,audioPackets:0,lastAssistantAudioPackets:0,spokenRows:new WeakSet()};
  S.liveVoice=session;
  syncVoiceControls();
  try{
    session.player=new SyncedAudioPlayer({
      basePath:'/voice-assets',sampleRate:24000,pcmOutput:true,echoCancellation:true,
      onEncodedAudio:data=>{if(!session.stopping&&session.ws?.readyState===WebSocket.OPEN)session.ws.send(data);},
      onText:liveVoiceTranscript,
      onEvent:event=>{
        if(event==='push_to_llm'){
          session.transcriptBoundary=true;
          session.lastAssistantAudioPackets=session.audioPackets;
        }
        if(event==='push_to_llm'||event==='llm_started')liveVoiceStatus(who+' prépare sa réponse…','thinking');
        if(event==='first_word'||event==='first_tts_audio')liveVoiceStatus(who+' répond…','speaking');
        if(event==='end_tts_audio')session.player?.scheduleEndOfTurn();
        if(event==='interrupted')liveVoiceStatus('Je vous écoute…');
      },
      onEndOfTurn:()=>{
        session.transcriptBoundary=true;
        const row=session.transcriptRow;
        const assistant=row?.dataset.role==='assistant' ? row.querySelector('p')?.textContent : '';
        const afterVoice=()=>{
          if(session.stopping||S.liveVoice!==session)return;
          if(session.pendingGuideReview){
            G.open=true;
            void stopLiveVoice().then(()=>guideRender());
          }else if(session.pendingProjectId)void switchLiveVoiceProject(session);
          else liveVoiceStatus('Je vous écoute…');
        };
        if(assistant&&session.audioPackets===session.lastAssistantAudioPackets&&!session.spokenRows.has(row)){
          session.spokenRows.add(row);
          liveVoiceStatus('Lecture de la réponse…','speaking');
          void speakReply(assistant,true).finally(afterVoice);
        }else afterVoice();
      },
      onError:error=>{if(!session.stopping){toast(error?.message||'Erreur audio.',true);stopLiveVoice();}}
    });
    await session.player.start();
    if(S.liveVoice!==session){session.player.stop();return;}
    const protocol=location.protocol==='https:'?'wss:':'ws:';
    session.ws=new WebSocket(`${protocol}//${location.host}/ws/voice/${guideMode?'guide':'live'}${session.projectId?'/'+encodeURIComponent(session.projectId):''}`);
    session.ws.onopen=()=>{if(!session.stopping){session.ws.send(JSON.stringify({type:'start'}));liveVoiceStatus('Je vous écoute…');}};
    session.ws.onmessage=async event=>{
      if(session.stopping)return;
      if(typeof event.data==='string'){
        let msg;try{msg=JSON.parse(event.data);}catch{return;}
        if(msg.type==='guide_update'&&guideMode){
          try{
            G.state=await api('/guide');G.error='';guideRender();guidePoll();
            if(msg.plan_pending){
              G.open=true;
              await stopLiveVoice();
              guideRender();
              if(msg.spoken_answer)void speakReply(msg.spoken_answer);
            }
          }catch(error){G.error=error.message;guideRender();}
          return;
        }
        if(msg.type==='project_update'){
          try{
            if(msg.project_id&&(msg.project_id!==session.projectId||msg.restart_voice)){
              session.pendingProjectId=msg.project_id;
              session.pendingReason=msg.restart_voice?'brain':'project';
              liveVoiceStatus(msg.restart_voice?'Modèle choisi. Passage termine sa réponse…':'Projet prêt. Passage termine sa réponse…','speaking');
              return;
            }
            await reloadProject();
            if(S.project?.approvals?.some(a=>a.status==='pending')){
              toast('Une action attend votre validation dans le projet.');
              await stopLiveVoice();renderView();return;
            }
            toast('Mission mise à jour dans le projet.');return;
          }catch(error){toast(error.message,true);return;}
        }
      }
      if(event.data instanceof Blob||event.data instanceof ArrayBuffer)session.audioPackets++;
      session.player.handleMessage(event.data);
    };
    session.ws.onerror=()=>{if(!session.stopping)liveVoiceStatus('Connexion vocale indisponible','error');};
    session.ws.onclose=event=>{
      if(S.liveVoice===session&&!session.stopping){
        toast(event.code===4401?'Session expirée ou accès au projet refusé.':'Conversation vocale interrompue.',true);
        stopLiveVoice();
      }
    };
  }catch(error){await stopLiveVoice();throw error;}
}

document.addEventListener('click', event=>{
  const replay=event.target.closest('[data-action="voice-replay"]');
  if(!replay||!S.liveVoice)return;
  const text=replay.closest('.live-voice-line')?.querySelector('p')?.textContent;
  if(text)void speakReply(text);
});

async function stopLiveVoice(){
  const session=S.liveVoice;
  if(!session||session.stopping)return;
  session.stopping=true;S.liveVoice=null;
  const socket=session.ws;
  session.player?.stop();
  if(socket){
    if(socket.readyState===WebSocket.OPEN)socket.send(JSON.stringify({type:'stop'}));
    if(socket.readyState<2){
      await Promise.race([new Promise(resolve=>socket.addEventListener('close',resolve,{once:true})),
                          new Promise(resolve=>setTimeout(resolve,1200))]);
      if(socket.readyState<2)socket.close();
    }
  }
  document.getElementById('live-voice-root').innerHTML='';
  syncVoiceControls('Conversation terminée. Le micro est fermé.');
  if(session.mode==='guide'&&typeof guideRender==='function')guideRender();
  if(S.project?.id===session.projectId){
    try{await reloadProject();if(S.view==='chat')renderView();}catch(error){toast(error.message,true);}
  }
}

window.addEventListener('beforeunload',()=>{
  const session=S.liveVoice;
  if(!session)return;
  session.player?.stop();
  if(session.ws?.readyState===WebSocket.OPEN)session.ws.send(JSON.stringify({type:'stop'}));
  session.ws?.close();
});
