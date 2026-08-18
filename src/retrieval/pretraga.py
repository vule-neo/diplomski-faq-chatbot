import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from normalizacija import u_latinicu, za_pretragu_kljucnim_rijecima

BAZA_PUTANJA = Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db"
KOLEKCIJA_NAZIV = "dokumenti"
MODEL_NAZIV = "paraphrase-multilingual-MiniLM-L12-v2"

VELICINA_BAZENA = 30  # koliko kandidata uzeti iz svakog pristupa prije spajanja
RRF_KONSTANTA = 15  # standardno 60, ali to je podeseno za ogromne (web) kolekcije;
                     # na nasem malom korpusu (~1000 chunkova) manja vrijednost daje
                     # vise tezine jakom pogotku iz samo jednog pristupa (npr. BM25
                     # tacno pogodi kljucni pojam a dense ga uopste ne rangira visoko)

_model = None
_kolekcija = None
_bm25 = None
_bm25_ids = None
_dokumenti_po_idu = None
_metadata_po_idu = None


def _ucitaj():
    global _model, _kolekcija, _bm25, _bm25_ids, _dokumenti_po_idu, _metadata_po_idu

    if _model is None:
        _model = SentenceTransformer(MODEL_NAZIV)
        client = chromadb.PersistentClient(path=str(BAZA_PUTANJA))
        _kolekcija = client.get_collection(name=KOLEKCIJA_NAZIV)

        svi = _kolekcija.get(include=["documents", "metadatas"])
        _bm25_ids = svi["ids"]
        _dokumenti_po_idu = dict(zip(svi["ids"], svi["documents"]))
        _metadata_po_idu = dict(zip(svi["ids"], svi["metadatas"]))

        tokenizovani = [za_pretragu_kljucnim_rijecima(tekst) for tekst in svi["documents"]]
        _bm25 = BM25Okapi(tokenizovani)

    return _model, _kolekcija


def _dense_rang_liste(upit, n):
    model, kolekcija = _ucitaj()
    embedding = model.encode([u_latinicu(upit)]).tolist()
    rezultati = kolekcija.query(query_embeddings=embedding, n_results=n)
    return rezultati["ids"][0]


def _bm25_rang_lista(upit, n):
    _ucitaj()
    tokeni = za_pretragu_kljucnim_rijecima(upit)
    skorovi = _bm25.get_scores(tokeni)
    poredak = sorted(range(len(skorovi)), key=lambda i: skorovi[i], reverse=True)
    return [_bm25_ids[i] for i in poredak[:n]]


def pretrazi(upit, n_results=4):
    _ucitaj()

    dense_ids = _dense_rang_liste(upit, VELICINA_BAZENA)
    bm25_ids = _bm25_rang_lista(upit, VELICINA_BAZENA)

    skorovi = {}
    for rang, chunk_id in enumerate(dense_ids):
        skorovi[chunk_id] = skorovi.get(chunk_id, 0) + 1 / (RRF_KONSTANTA + rang + 1)
    for rang, chunk_id in enumerate(bm25_ids):
        skorovi[chunk_id] = skorovi.get(chunk_id, 0) + 1 / (RRF_KONSTANTA + rang + 1)

    poredani_idevi = sorted(skorovi, key=skorovi.get, reverse=True)[:n_results]

    chunkovi = []
    for chunk_id in poredani_idevi:
        chunkovi.append({
            "tekst": _dokumenti_po_idu[chunk_id],
            "metadata": _metadata_po_idu[chunk_id],
            "skor": skorovi[chunk_id],
        })

    return chunkovi
