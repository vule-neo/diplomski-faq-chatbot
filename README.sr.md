# FAQ chatbot za studentsku službu

[English](README.md) | **Srpski**

Sistem za automatsko odgovaranje na česta pitanja studenata, zasnovan na RAG
(Retrieval-Augmented Generation) arhitekturi. Odgovara isključivo na osnovu zvaničnih
dokumenata Elektrotehničkog fakulteta (pravilnici, statut, zakon, stranice sa sajta), a
kada odgovor nije pokriven dokumentima, jasno kaže da ne zna umjesto da improvizuje.

Diplomski rad, Elektrotehnički fakultet u Beogradu.

## Kako radi

```
pitanje studenta
      │
      ▼
  transliteracija (ćirilica → latinica)
      │
      ├──────────────┬──────────────┐
      ▼              ▼              │
  embedding       BM25              │  dvije nezavisne pretrage
  (semantika)  (ključne riječi)     │
      └──────┬───────┘              │
             ▼                      │
   spajanje rezultata (RRF)  ◄──────┘
             │
             ▼
   10 najrelevantnijih dijelova dokumenata
             │
             ▼
   Groq API (LLM) + prompt "odgovori samo iz konteksta"
             │
             ▼
   odgovor + izvori
```

Dokumenti se unaprijed obrađuju: iz PDF-ova se izvlači tekst (skenirani prolaze kroz
OCR), čisti se, dijeli na dijelove (chunkove) i pretvara u vektore koji se čuvaju u
lokalnoj ChromaDB bazi.

## Tehnologije

| Sloj | Tehnologija |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Vektorska baza | ChromaDB (lokalna, fajl-based) |
| Embeddings | sentence-transformers, `paraphrase-multilingual-MiniLM-L12-v2` |
| Leksička pretraga | rank_bm25 |
| LLM | Groq API, `openai/gpt-oss-120b` |
| Obrada PDF-a | PyMuPDF, pdfplumber, pytesseract (OCR) |
| Frontend | Angular |

## Preduslovi

- **Python 3.11+**
- **Node.js 20+** (za frontend)
- **Tesseract-OCR**, potreban samo za obradu skeniranih dokumenata
  - Windows: instalacija sa https://github.com/UB-Mannheim/tesseract/wiki
  - Obavezno dodati i srpski jezički paket: preuzeti `srp.traineddata` sa
    https://github.com/tesseract-ocr/tessdata i staviti ga u `tessdata` folder
    instalacije (npr. `C:\Program Files\Tesseract-OCR\tessdata\`)
  - Putanja do `tesseract.exe` je postavljena u `src/ingest/obradi_skenirane.py`,
    izmijeniti ako je instalacija na drugom mjestu
- **Groq API ključ**, besplatan, sa https://console.groq.com

## Instalacija

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

U korijenu projekta napraviti fajl `.env`:

```
GROQ_API_KEY=vas_kljuc_ovdje
```

## Priprema baze znanja

Originalni dokumenti stoje u `data/raw/`, organizovani po kategorijama. Skripte se
pokreću ovim redoslijedom (svaka se može pokretati više puta, rezultat je isti):

```bash
python src/ingest/obradi_dokumente.py    # PDF -> tekst, tabele, struktura
python src/ingest/obradi_skenirane.py    # OCR za skenirane PDF-ove
python src/ingest/chunking.py            # dijeljenje na chunkove
python src/retrieval/ucitaj_u_chromu.py  # embedding + upis u ChromaDB
```

Prvi put traje nekoliko minuta (OCR i embedding su spori). Rezultat su folderi
`data/processed/` i `data/chroma_db/`; oba se generišu iz `data/raw/` i nisu u
verzionisanju.

Pomoćna skripta za pregled: `python src/ingest/triage.py` ispisuje koji su dokumenti
skenirani i koji sadrže tabele.

## Pokretanje

Backend:

```bash
uvicorn src.api.main:app --port 8000
```

Dostupno na http://localhost:8000, interaktivna dokumentacija na
http://localhost:8000/docs

Frontend (u drugom terminalu):

```bash
cd frontend
npm install        # samo prvi put
ng serve --port 4200
```

Aplikacija: http://localhost:4200

## API

| Metod | Putanja | Opis |
|---|---|---|
| `POST` | `/ask` | Postavlja pitanje, vraća odgovor i listu izvora |
| `POST` | `/feedback` | Bilježi ocjenu odgovora (koristan / nekoristan) |
| `GET` | `/health` | Provjera da servis radi |

Primjer:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"pitanje\": \"Koji su rokovi za prijavu ispita?\"}"
```

## Evaluacija

```bash
python eval/pokreni_evaluaciju.py   # pokreće test pitanja kroz sistem
python eval/metrike.py              # računa metrike iz unesenih ocjena
```

- `eval/pitanja.json`: 37 test pitanja podijeljenih u šest kategorija (pitanja u
  domenu, pitanja koja traže uslov važenja, pitanja van domena, djelimično pokrivena
  pitanja, robusnost na formulaciju, otpornost na prompt injection)
- `eval/rezultati.md`: odgovori sistema; ocjene se unose ručno
- `eval/metrike.md`: sračunate metrike

Skripta snima rezultat poslije svakog pitanja, pa se prekinut prolaz nastavlja
pokretanjem iste komande (već odrađena pitanja se preskaču). Ručno unesene ocjene se
pritom čuvaju.

**Napomena o Groq limitima:** besplatni tier ima ograničenje od 200.000 tokena dnevno,
a jedan kompletan prolaz kroz evaluaciju troši oko 130.000. Ako se pojavi greška 429,
treba sačekati, jer je limit rolling prozor od 24h, ne resetuje se u ponoć.

## Struktura projekta

```
data/
├── raw/            originalni dokumenti (u verzionisanju)
├── processed/      obrađen tekst (generiše se)
└── chroma_db/      vektorska baza (generiše se)

src/
├── ingest/         obrada dokumenata: parsing, OCR, čišćenje, chunking
├── retrieval/      transliteracija, hibridna pretraga, ChromaDB
├── llm/            poziv ka Groq API-ju i sistemski prompt
├── api/            FastAPI aplikacija, logovanje upita
└── tests/          pomoćne skripte za ručnu provjeru

eval/               test pitanja, rezultati i metrike
frontend/           Angular aplikacija
```

## Poznata ograničenja

- OCR skeniranih dokumenata ne prepoznaje matematičke formule i tekst iz logoa/pečata
- Tabele se izvlače samo iz dokumenata koji nisu skenirani
- Pretraga povremeno pronađe pravi dokument, ali pogrešan član unutar njega
- Uopštena pitanja (npr. „koliko košta školarina") ne dolaze uvijek do konkretnog podatka
