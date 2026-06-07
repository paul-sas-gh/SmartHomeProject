# Smart Home Semantic Management

Proiectul implementează un flux semantic pentru gestionarea unei case inteligente:

**text în limbaj natural → procesare NLP/AI → generare RDF → GraphDB → SPARQL**

Repository-ul conține atât serviciile aplicației, cât și scripturi de inițializare, date suport și documentație tehnică.

---

## 1. Prezentare generală

Scopul proiectului este de a permite interogarea și administrarea datelor dintr-un sistem Smart Home fără a cunoaște direct schema RDF sau limbajul SPARQL. Sistemul combină:

- **date structurale** despre camere, hub-uri, senzori și actuatoare;
- **date comerciale** despre brand, preț și clasă energetică;
- **procesare NLP** pentru extragerea entităților și relațiilor din text;
- **integrare AI** pentru interpretarea cererilor complexe;
- **persistență semantică** în GraphDB.

---

## 2. Componente principale

### `svc-api/`
Serviciul FastAPI al proiectului. Expune endpoint-uri pentru:

- procesarea textului din fișiere sau direct din body JSON;
- generarea și exportul grafului Turtle;
- upload-ul în GraphDB;
- interogări SPARQL custom și predefinite;
- listarea entităților și relațiilor extrase;
- procesare asistată de LLM.

### `svc-smart-home-setup/`
Scripturi de pregătire a datelor pentru GraphDB:

- încărcarea modelului RDF de bază;
- combinarea datelor comerciale din CSV cu modelul semantic.

### `svc-llm/`
Resursele și configurațiile dedicate componentei LLM și infrastructurii asociate.

### `data/`
Datele proiectului: ontologie, fișiere de intrare, fișiere generate și resurse de suport.

### `images/`
Imagini și resurse grafice utilizate în documentație și prezentare.

### `scripts/`
Scripturi auxiliare pentru scenarii, exporturi și alte operații de suport.

---

## 3. Structura de nivel înalt

```text
SmartHomeProject/
├── data/
├── images/
├── scripts/
├── svc-api/
├── svc-llm/
├── svc-smart-home-setup/
├── SCENARIO.md
└── README.md
```

---

## 4. Cum se folosește proiectul

Fluxul uzual este:

1. pornești GraphDB;
2. rulezi scripturile din `svc-smart-home-setup/` pentru inițializarea repository-ului și încărcarea datelor;
3. pornești `svc-api/`;
4. trimiți cereri text către API sau rulezi interogări SPARQL;
5. consulți răspunsurile din GraphDB sau din endpoint-urile expuse.

---

## 5. Documentație aferentă

Documentele de mai jos oferă detalii suplimentare despre scenariu, structură și modulele proiectului:

- [`SCENARIO.md`](./SCENARIO.md) — descrierea scenariului de utilizare, a problemei și a structurii de ansamblu;
- [`svc-api/README.md`](./svc-api/README.md) — documentația principală pentru serviciul FastAPI;
- [`svc-api/STRUCTURE.md`](./svc-api/STRUCTURE.md) — prezentarea structurii interne a modulului `svc-api`;
- [`svc-smart-home-setup/README.md`](./svc-smart-home-setup/README.md) — instrucțiuni pentru încărcarea și combinarea datelor în GraphDB;
- [`svc-llm/docs/plan/gemma4-local-docker.md`](./svc-llm/docs/plan/gemma4-local-docker.md) — planul pentru componenta LLM locală;
- [`data/device_list.md`](./data/device_list.md) — listă de dispozitive și resurse asociate datelor;
- [`scripts/RutineSpec.agent.md`](./scripts/RutineSpec.agent.md) — specificații pentru rutine și scenarii de lucru.

---

## 6. Observații

- Proiectul este construit pentru rulare locală, cu servicii separate pentru API, GraphDB și componenta LLM.
- Fișierele Markdown din repository sunt folosite ca documentație operațională și de proiect.
- Dacă adaugi componente noi sau modifici fluxul de lucru, actualizează și documentele referențiate mai sus.

