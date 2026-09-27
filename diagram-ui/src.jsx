import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Excalidraw } from '@excalidraw/excalidraw';

window.EXCALIDRAW_ASSET_PATH = '/static/diagram/';
const params = new URLSearchParams(location.search);
const workId = params.get('work_id');
const diagramId = params.get('diagram_id');
const editable = params.get('editable') === '1';
const endpoint = `/api/work/tasks/${encodeURIComponent(workId)}/diagrams/${encodeURIComponent(diagramId)}`;

async function request(path, options = {}) {
  const status = await fetch('/api/auth/status', { credentials: 'same-origin' }).then(r => r.json());
  if (!status.user) throw new Error('Connectez-vous à Passage pour ouvrir ce schéma.');
  const response = await fetch(path, {
    credentials: 'same-origin', ...options,
    headers: { 'Content-Type': 'application/json', 'X-Passage-CSRF': status.csrf, ...options.headers },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Erreur HTTP ${response.status}`);
  }
  return response.json();
}

function App() {
  const [diagram, setDiagram] = useState(null);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('Chargement du schéma…');
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const latest = useRef({ elements: [], app_state: {} });
  useEffect(() => {
    if (!workId || !diagramId) { setMessage('Identifiant de schéma manquant.'); return; }
    request(endpoint).then(item => {
      setDiagram(item); setTitle(item.title);
      latest.current = { elements: item.elements, app_state: item.app_state };
      setMessage(`Version ${item.version} · sauvegardée`);
    }).catch(error => setMessage(error.message));
  }, []);
  async function save() {
    if (!editable) return;
    setSaving(true);
    try {
      const item = await request(endpoint, { method: 'PUT', body: JSON.stringify({
        title, expected_version: diagram.version,
        elements: latest.current.elements,
        app_state: latest.current.app_state,
      }) });
      setDiagram(item); setDirty(false); setMessage(`Version ${item.version} · sauvegardée`);
      window.parent.postMessage({ type: 'passage-diagram-saved', work_id: workId }, location.origin);
    } catch (error) { setMessage(error.message); }
    finally { setSaving(false); }
  }
  if (!diagram) return <div className="loading">{message}</div>;
  return <div className="page">
    <header className="bar">
      <div className="brand">Passage · schéma de protocole</div>
      <input aria-label="Titre du schéma" value={title} maxLength={180} readOnly={!editable} onChange={e => { setTitle(e.target.value); setDirty(true); }} />
      <span role="status" className={dirty ? 'dirty' : ''}>{dirty ? 'Modifications non sauvegardées' : message}</span>
      {editable && <button onClick={save} disabled={!dirty || saving || title.trim().length < 2}>{saving ? 'Sauvegarde…' : 'Sauvegarder'}</button>}
    </header>
    <div className="instructions">Rectangle : étape · losange : décision · flèche reliée : transition · texte dans une forme : libellé. L’agent signalera ce qui manque.</div>
    <main className="canvas">
      <Excalidraw key={diagram.id} langCode="fr-FR" viewModeEnabled={!editable}
        initialData={{ elements: diagram.elements, appState: diagram.app_state, files: {} }}
        UIOptions={{ tools: { image: false }, canvasActions: {
          loadScene: false, saveToActiveFile: false, export: false, toggleTheme: false,
        } }}
        onChange={(elements, appState) => {
          const scene = { elements: [...elements], app_state: { viewBackgroundColor: appState.viewBackgroundColor } };
          // Initial onChange is not a user edit.
          if (JSON.stringify(scene.elements) !== JSON.stringify(latest.current.elements) ||
              scene.app_state.viewBackgroundColor !== latest.current.app_state.viewBackgroundColor) {
            latest.current = scene; setDirty(true);
          }
        }} />
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(<App />);
