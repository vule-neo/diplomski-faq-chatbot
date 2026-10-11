# 1) Bazni image: Linux + Python 3.11. "slim" = bez suvisnih alata, manji image.
FROM python:3.11-slim

# 2) Radni folder u imageu. Svaka sljedeca komanda se izvrsava odavde.
WORKDIR /app

# 3) CPU verzija torcha PRVA i zasebno. Ovaj sloj je ogroman (~200 MB) ali se
#    skoro nikad ne mijenja, pa Docker koristi kes i preskace ga pri svakom buildu.
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# 4) Prvo samo spisak paketa, pa instalacija. Posto kod jos nije kopiran,
#    promjena koda NE ponistava ovaj sloj. --no-cache-dir = pip ne cuva
#    preuzete .whl fajlove u imageu (manji image).
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# 5) Skini oba modela TOKOM builda, da zavrse u imageu (knjizi), a ne da se
#    skidaju pri svakom paljenju kontejnera. Imena su iz src/retrieval/pretraga.py.
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); \
CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')"

# 6) Tek sad kopiraj kod i bazu. Ovo je sloj koji se najcesce mijenja, zato je dole.
#    .dockerignore vec izbacuje frontend, data/raw, venv itd.
COPY . .

# 7) Dokumentacija: aplikacija slusa na 8000 (ne otvara nista samo po sebi).
EXPOSE 8000

# 8) Sta se pokrece kad se kontejner PALI. --host 0.0.0.0 = slusaj "interfon",
#    da zahtjevi spolja (preko -p) stignu do servera.
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
