# FAQ Chatbot for Student Services

**English** | [Srpski](README.sr.md)

A system that automatically answers frequently asked student questions, built on a RAG
(Retrieval-Augmented Generation) architecture. It answers strictly from official
documents of the School of Electrical Engineering (regulations, statute, law, pages from
the faculty website), and when an answer is not covered by the documents, it clearly
says it doesn't know instead of improvising.

Bachelor's thesis, School of Electrical Engineering, University of Belgrade.

> The chatbot, the source documents and the code identifiers are in Serbian.

## How it works

```
student question
      │
      ▼
  transliteration (Cyrillic → Latin)
      │
      ├──────────────┬──────────────┐
      ▼              ▼              │
  embedding       BM25              │  two independent searches
  (semantic)   (keywords)           │
      └──────┬───────┘              │
             ▼                      │
   result fusion (RRF)  ◄───────────┘
             │
             ▼
   10 most relevant document chunks
             │
             ▼
   Groq API (LLM) + "answer only from the context" prompt
             │
             ▼
   answer + sources
```

Documents are processed in advance: text is extracted from the PDFs (scanned ones go
through OCR), cleaned, split into chunks and converted into vectors stored in a local
ChromaDB database.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Vector database | ChromaDB (local, file-based) |
| Embeddings | sentence-transformers, `paraphrase-multilingual-MiniLM-L12-v2` |
| Lexical search | rank_bm25 |
| LLM | Groq API, `openai/gpt-oss-120b` |
| PDF processing | PyMuPDF, pdfplumber, pytesseract (OCR) |
| Frontend | Angular |

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** (for the frontend)
- **Tesseract-OCR**, needed only for processing scanned documents
  - Windows: install from https://github.com/UB-Mannheim/tesseract/wiki
  - You also need the Serbian language pack: download `srp.traineddata` from
    https://github.com/tesseract-ocr/tessdata and put it in the installation's
    `tessdata` folder (e.g. `C:\Program Files\Tesseract-OCR\tessdata\`)
  - The path to `tesseract.exe` is set in `src/ingest/obradi_skenirane.py`; change it
    if Tesseract is installed elsewhere
- **Groq API key**, free, from https://console.groq.com

## Installation

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create a `.env` file in the project root (see `.env.example`):

```
GROQ_API_KEY=your_key_here
```

## Building the knowledge base

The original documents live in `data/raw/`, organized by category. Run the scripts in
this order (each one can be re-run safely and produces the same result):

```bash
python src/ingest/obradi_dokumente.py    # PDF -> text, tables, structure
python src/ingest/obradi_skenirane.py    # OCR for scanned PDFs
python src/ingest/chunking.py            # split into chunks
python src/retrieval/ucitaj_u_chromu.py  # embed + load into ChromaDB
```

The first run takes a few minutes (OCR and embedding are slow). It produces the
`data/processed/` and `data/chroma_db/` folders; both are generated from `data/raw/` and
are not under version control.

Helper script: `python src/ingest/triage.py` lists which documents are scanned and which
contain tables.

## Running

Backend:

```bash
uvicorn src.api.main:app --port 8000
```

Available at http://localhost:8000, interactive docs at http://localhost:8000/docs

Frontend (in a second terminal):

```bash
cd frontend
npm install        # first time only
ng serve --port 4200
```

App: http://localhost:4200

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/ask` | Asks a question, returns the answer and a list of sources |
| `POST` | `/feedback` | Records a rating of an answer (helpful / not helpful) |
| `GET` | `/health` | Checks that the service is running |

Example (the question means "What are the exam registration deadlines?"):

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"pitanje\": \"Koji su rokovi za prijavu ispita?\"}"
```

## Evaluation

```bash
python eval/pokreni_evaluaciju.py   # runs the test questions through the system
python eval/metrike.py              # computes metrics from the entered ratings
```

- `eval/pitanja.json`: 37 test questions in six categories (in-domain questions,
  questions that require a validity condition, out-of-domain questions, partially
  covered questions, robustness to phrasing, resistance to prompt injection)
- `eval/rezultati.md`: the system's answers; ratings are entered by hand
- `eval/metrike.md`: computed metrics

The script saves results after every question, so an interrupted run resumes by running
the same command again (questions already done are skipped). Manually entered ratings
are preserved.

**Note on Groq limits:** the free tier is limited to 200,000 tokens per day, and one full
evaluation run uses about 130,000. If you get a 429 error, wait: the limit is a rolling
24-hour window and does not reset at midnight.

## Project structure

```
data/
├── raw/            original documents (under version control)
├── processed/      processed text (generated)
└── chroma_db/      vector database (generated)

src/
├── ingest/         document processing: parsing, OCR, cleaning, chunking
├── retrieval/      transliteration, hybrid search, ChromaDB
├── llm/            Groq API call and system prompt
├── api/            FastAPI app, query logging
└── tests/          helper scripts for manual checks

eval/               test questions, results and metrics
frontend/           Angular app
```

## Known limitations

- OCR of scanned documents does not recognize math formulas or text in logos/stamps
- Tables are extracted only from documents that are not scanned
- Search sometimes finds the right document but the wrong article within it
- General questions (e.g. "how much is tuition") don't always reach the specific figure
