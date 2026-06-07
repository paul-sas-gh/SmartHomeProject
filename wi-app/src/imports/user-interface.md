Mai jos ai un set complet de **specificații pentru o interfață React** prin care să vizualizezi Knowledge Graph-ul din GraphDB — structurat clar, astfel încât să-l poți folosi direct în documentație sau ca bază pentru implementare.

***

# 🖥️ React UI Specification — GraphDB Visualization

## 🎯 Scop

Interfața permite:

* ✅ Vizualizarea grafică a RDF triples din GraphDB
* ✅ Explorarea relațiilor între entități (Room, Device, RoutineStep)
* ✅ Filtrare și interogare SPARQL
* ✅ Integrare cu rezultatele NLP (entități + relații)

***

# 🧱 1. Stack UI recomandat

```md
Frontend:
- React (functional components + hooks)
- TypeScript (opțional, recomandat)
- Vite / Create React App

Graph Visualization:
- react-force-graph (recomandat)
SAU
- Cytoscape.js

Styling:
- TailwindCSS / Material UI

API:
- fetch / axios

SPARQL:
- SPARQL endpoint GraphDB (HTTP API)
```

***

# 🏗️ 2. Arhitectura UI

```
App
 ├── GraphView (vizualizare graph)
 ├── QueryPanel (SPARQL queries)
 ├── FilterPanel (filtrare entități)
 ├── DetailsPanel (detalii nod selectat)
 └── UploadPanel (optional NLP input)
```

***

# 🧩 3. Componente principale

***

## 3.1 ✅ GraphView (core component)

### Rol:

* afișează graful RDF ca noduri + muchii

### Props:

```ts
type GraphData = {
  nodes: Array<{ id: string; label: string; type: string }>;
  links: Array<{ source: string; target: string; label: string }>;
};
```

***

### Exemple UI behavior:

* noduri colorate după tip:
  * Room → albastru
  * Sensor → verde
  * Actuator → portocaliu
  * Action → roșu

* click pe nod:
  → deschide DetailsPanel

***

### Exemplu implementare:

```jsx
import ForceGraph2D from "react-force-graph";

const GraphView = ({ data }) => {
  return (
    <ForceGraph2D
      graphData={data}
      nodeLabel="label"
      linkLabel="label"
      nodeAutoColorBy="type"
    />
  );
};
```

***

## 3.2 ✅ QueryPanel (SPARQL editor)

### Rol:

* permite rularea de interogări

***

### UI:

* text editor
* buton: Run Query
* rezultat tabel

***

### Exemplu:

```jsx
const runQuery = async (query) => {
  const response = await fetch("http://localhost:7200/repositories/smarthome", {
    method: "POST",
    headers: {
      "Content-Type": "application/sparql-query",
      "Accept": "application/sparql-results+json"
    },
    body: query
  });

  return response.json();
};
```

***

## 3.3 ✅ FilterPanel

### Rol:

* filtrează graful

***

### Filtre:

* tip entitate:
  * Room
  * Device
  * Action

* relații:
  * requiresActuator
  * locatedIn

***

### Exemplu UI:

```jsx
<select>
  <option>All</option>
  <option>Room</option>
  <option>Device</option>
</select>
```

***

## 3.4 ✅ DetailsPanel

### Rol:

* afișează detalii despre nod selectat

***

### Conținut:

* tip entitate
* proprietăți RDF
* relații

***

### Exemple:

```
SmartLights
Type: Actuator
Located in: EntryHall
Brand: Philips
Price: 120
```

***

## 3.5 ✅ UploadPanel (optional — BONUS)

### Rol:

* upload fișier text NLP

```
Upload .txt
→ trimite la backend NLP
→ generează RDF
→ vizualizare automată
```

***

# 🔗 4. Integrare GraphDB

## Endpoint SPARQL

```
http://localhost:7200/repositories/{repo_name}
```

***

## Query Example

```sparql
SELECT ?s ?p ?o WHERE {
  ?s ?p ?o
} LIMIT 100
```

***

## Transformare rezultat → graph

```js
function toGraphData(bindings) {
  const nodes = {};
  const links = [];

  bindings.forEach(row => {
    const s = row.s.value;
    const o = row.o.value;

    nodes[s] = { id: s };
    nodes[o] = { id: o };

    links.push({
      source: s,
      target: o,
      label: row.p.value
    });
  });

  return {
    nodes: Object.values(nodes),
    links
  };
}
```

***

# 🎨 5. UX Design

## Layout recomandat

```
---------------------------------------
| QueryPanel       | DetailsPanel     |
---------------------------------------
|             GraphView               |
---------------------------------------
|            FilterPanel              |
---------------------------------------
```

***

## Interacțiuni

* click pe nod → highlight vecini
* hover → tooltip
* zoom + pan

***

# 🧠 6. Mapping RDF → UI

| RDF Concept | UI         |
| ----------- | ---------- |
| Subject     | Node       |
| Predicate   | Edge label |
| Object      | Node       |
| Class       | Node type  |

***

# 🚀 7. Extensii (pentru impresionat profesor)

## 🔹 1. Highlight relații din NLP

* highlight pentru:
  * requiresActuator
  * requiresSensor

***

## 🔹 2. Mode switch

* Graph View
* Table View

***

## 🔹 3. Query templates

ex:

```
• Show all actuators in LivingRoom
• Show all actions and devices
```

***

## 🔹 4. Color legend

```
Red     = Action
Blue    = Room
Green   = Sensor
Orange  = Actuator
Purple  = SmartHub
```

***

# ✅ 8. User Flow complet

```
1. User încarcă text (optional)
2. NLP → RDF
3. RDF → GraphDB
4. UI → SPARQL query
5. Data → Graph visualization
6. User explorează relațiile
```

***

# ✅ 9. Rezultat final (pentru proiect)

Interfața ta va:

* ✔ vizualiza graf RDF complet
* ✔ permite interogare SPARQL
* ✔ evidenția relații din NLP
* ✔ integra date externe OntoRefine

***


