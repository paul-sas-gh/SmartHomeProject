# svc-smart-home-setup

Scripturi de inițializare pentru încărcarea și combinarea datelor Smart Home în GraphDB.

## Scop

Acest director conține utilitare Python pentru:

1. încărcarea modelului RDF în GraphDB;
2. generarea de triplete RDF din CSV și încărcarea lor în același repository.

## Structura

- `1_load_to_graphdb.py` — creează repository-ul `smarthome` dacă nu există și încarcă modelul RDF din `data/SmartHomeModel.ttl`.
- `2_combine_data.py` — citește un CSV cu atribute comerciale pentru dispozitive și generează Turtle, apoi îl trimite în GraphDB.
- `devices.csv` — date de intrare pentru scriptul de combinare.

## Cerințe

- Python 3.10+;
- pachetul `requests` instalat;
- GraphDB pornit local la `http://localhost:7200`;
- repository-ul țintă: `smarthome`.

## Instalare

Dacă rulezi scripturile dintr-un mediu Python separat, instalează dependențele:

```powershell
pip install requests
```

## Cum se rulează

### 1. Încărcarea modelului RDF în GraphDB

Din directorul `svc-smart-home-setup`:

```powershell
python .\1_load_to_graphdb.py
```

Ce face scriptul:

- verifică dacă GraphDB este disponibil;
- verifică dacă repository-ul `smarthome` există;
- creează repository-ul dacă este necesar;
- încarcă fișierul `data/SmartHomeModel.ttl`.

### 2. Combinarea datelor din CSV cu modelul RDF

```powershell
python .\2_combine_data.py
```

Ce face scriptul:

- citește `devices.csv`;
- generează triplete Turtle pentru brand, preț și clasă energetică;
- încarcă datele rezultate în repository-ul `smarthome`.

## Observații importante

- Scripturile presupun că GraphDB rulează local pe portul `7200`.
- Repository-ul folosit este `smarthome`.
- Dacă structura proiectului se schimbă, verifică și actualizează căile către fișierele de intrare.

## Rezultat așteptat

După rularea celor două scripturi, repository-ul `smarthome` ar trebui să conțină:

- modelul RDF de bază;
- datele comerciale pentru dispozitive;
- informațiile necesare pentru interogările SPARQL din aplicație.

## Notă

Dacă primești erori de tip „file not found”, verifică:

- că ești în directorul corect;
- că fișierele de intrare există;
- că GraphDB este pornit și accesibil.

