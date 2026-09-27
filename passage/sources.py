import concurrent.futures
import re
import unicodedata
import requests
from . import store

BASE = 'https://theses.fr/api/v1/theses'

def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if not unicodedata.combining(c))

def lab_matches(name, query):
    """Catalogue variants include 'et chimie' and 'et de chimie'."""
    stop = {'de', 'des', 'du', 'la', 'le', 'les', 'et', 'laboratoire'}
    words = lambda s: set(re.findall(r'[a-z0-9]+', normalized(s))) - stop
    return bool(words(query)) and words(query).issubset(words(name))

def people(items):
    return [{'name': ' '.join(filter(None, [x.get('prenom'), x.get('nom')])),
             'idref': x.get('ppn') or x.get('id', '')} for x in items or [] if isinstance(x, dict)]

def normalize(identifier, search, detail, collected_at=None):
    row = {**search, **detail}
    partners = (detail.get('partenairesRecherche') or []) + (search.get('partenairesDeRecherche') or [])
    labs = list(dict.fromkeys(p.get('nom', '') for p in partners if isinstance(p, dict) and p.get('nom')))
    resumes = detail.get('resumes') or {}
    keywords = search.get('sujets') or []
    if detail.get('mapSujets'):
        keywords = [x['keyword'] for lang in detail['mapSujets'].values() for x in lang if x.get('keyword')]
    keywords = list(dict.fromkeys(k if isinstance(k, str) else k.get('libelle', '') for k in keywords if isinstance(k, (str, dict))))
    institution = detail.get('etabSoutenance') or search.get('etabSoutenanceN') or ''
    if isinstance(institution, dict):
        institution = institution.get('nom', '')
    return {'id': str(identifier), 'title': row.get('titrePrincipal') or str(identifier),
            'title_en': (detail.get('titres') or {}).get('en') or search.get('titreEN') or '',
            'authors': people(row.get('auteurs')), 'directors': people(row.get('directeurs')),
            'status': row.get('status', 'inconnu'), 'date': row.get('dateSoutenance') or '',
            'start_date': row.get('datePremiereInscriptionDoctorat') or '',
            'discipline': row.get('discipline') or '', 'institution': str(institution),
            'labs': labs, 'is_lab': any(lab_matches(l, 'Réactivité Chimie Solides') for l in labs),
            'keywords': keywords, 'abstract': resumes.get('fr') or resumes.get('en') or '',
            'abstract_fr': resumes.get('fr') or '', 'abstract_en': resumes.get('en') or '',
            'source_url': 'https://theses.fr/' + str(identifier), 'collected_at': collected_at or store.now(),
            'visible': False, 'correction': '', 'source_kind': 'theses.fr', 'raw': {'search': search, 'detail': detail}}

def upsert(notice):
    with store.transaction() as c:
        previous = store.get('thesis', notice['id'], c)
        if previous:
            for key in ['visible', 'correction', 'correction_at', 'publication_at', 'publication_actor']:
                if key in previous:
                    notice[key] = previous[key]
        store.put('thesis', notice, c)
    return previous is None

def request(path, **params):
    response = requests.get(BASE + path, params=params, timeout=(8, 35))
    response.raise_for_status()
    return response.json()

def import_lab(query, lab_filter, limit, progress=lambda x: None):
    result = request('/recherche/', q=query, nombre=limit)
    found = result.get('theses', [])
    selected = [t for t in found if any(lab_matches(p.get('nom', ''), lab_filter) for p in t.get('partenairesDeRecherche', []))]
    stats = {'found': result.get('totalHits', len(found)), 'retained': len(selected), 'added': 0, 'updated': 0, 'errors': []}
    def load(t):
        try:
            return t, request('/these/' + str(t['id'])), None
        except requests.RequestException:
            return t, {}, 'Détail indisponible ; métadonnées conservées.'
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for index, (search, detail, error) in enumerate(pool.map(load, selected)):
            item = normalize(search['id'], search, detail)
            item['is_lab'] = True
            if error:
                stats['errors'].append({'id': item['id'], 'message': error})
                old = store.get('thesis', item['id'])
                if old and old['abstract']:
                    item = {**old, 'collected_at': item['collected_at']}
            stats['added' if upsert(item) else 'updated'] += 1
            progress(f'{index + 1}/{len(selected)} notices enregistrées')
    stats['truncated'] = stats['found'] > limit
    store.event('Import theses.fr', query, f"{stats['added']} ajouts, {stats['updated']} mises à jour, {len(stats['errors'])} détails indisponibles")
    return stats

def public_notice(t):
    return {k: v for k, v in t.items() if k != 'raw'}

def demo_library_ids(rows):
    """Small battery corpus for the stated demo; ranking is never keyed by ID."""
    candidates = [t for t in rows if t['abstract'] and any(w in normalized(t['title']) for w in ('batter', 'accumulateur'))][:8]
    return {t['id'] for t in candidates} | {'2014DIJOS078', '2019PSLEC037', 's352032'}

def seed():
    import json
    if not store.get('settings', 'main'):
        store.put('settings', {'id': 'main', 'lab_name': 'Laboratoire de Réactivité et Chimie des Solides',
                              'lab_short': 'LRCS', 'city': 'Amiens', 'company': 'Vélia Mobilité — entreprise fictive'})
    if not store.all_of('thesis'):
        corpus = store.ROOT / 'data' / 'corpus_theses.json'
        if corpus.exists():
            data = json.loads(corpus.read_text(encoding='utf-8'))
            rows = [normalize(x['id'], x['search'], x['detail'], data['collected_at']) for x in data['records']]
            # Public library starts with a clearly marked role-play publication of source notices.
            ids = demo_library_ids(rows)
            for t in rows:
                if 'bourseau' in normalized(' '.join(a['name'] for a in t['authors'])):
                    ids.add(t['id'])
                if t['id'] in ids:
                    t.update(visible=True, publication_actor='Scénario de démonstration — validation simulée', publication_at=store.now())
                upsert(t)
            store.event('Corpus public chargé', 'theses.fr', f'{len(rows)} notices ; publications simulées pour la démonstration')
    if not store.all_of('programme'):
        path = store.ROOT / 'data' / 'programmes_demo.json'
        for p in json.loads(path.read_text(encoding='utf-8')):
            store.put('programme', p)
