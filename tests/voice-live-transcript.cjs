// Regression: Gradbot can reuse turn_idx; the UI must still show separate turns.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor(tag) { this.tag=tag; this.children=[]; this.dataset={}; this.textContent=''; }
  append(...items) { this.children.push(...items); }
  querySelector(tag) { return this.children.find(item=>item.tag===tag); }
}
const list = new Element('div');
const session = {transcriptRow:null,transcriptBoundary:false};
const context = {
  S:{liveVoice:session},
  document:{getElementById:id=>id==='live-voice-transcript'?list:null,
    createElement:tag=>new Element(tag),addEventListener:()=>{}},
  window:{addEventListener:()=>{}},
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('passage/static/voice-live.js','utf8'),context);
context.liveVoiceTranscript({text:'Première question',turnIdx:0,isUser:true});
context.liveVoiceTranscript({text:'Première réponse',turnIdx:0,isUser:false});
context.liveVoiceTranscript({text:'Deuxième question',turnIdx:0,isUser:true});
assert.deepEqual(list.children.map(row=>row.querySelector('p').textContent),
  ['Première question','Première réponse','Deuxième question']);
session.transcriptBoundary=true;
context.liveVoiceTranscript({text:'Troisième question',turnIdx:0,isUser:true});
assert.equal(list.children.length,4);
console.log('4 tours vocaux distincts');
