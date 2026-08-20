import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

from normalizacija import u_latinicu, za_pretragu_kljucnim_rijecima

BAZA_PUTANJA = Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db"
KOLEKCIJA_NAZIV = "dokumenti"
MODEL_NAZIV = "paraphrase-multilingual-MiniLM-L12-v2"
RERANKER_NAZIV = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

VELICINA_BAZENA = 40  # koliko kandidata uzeti iz svakog pristupa prije spajanja
RRF_KONSTANTA = 15  # standardno 60, ali to je podeseno za ogromne (web) kolekcije;
                     # na nasem malom korpusu (~1000 chunkova) manja vrijednost daje
                     # vise tezine jakom pogotku iz samo jednog pristupa (npr. BM25
                     # tacno pogodi kljucni pojam a dense ga uopste ne rangira visoko)

# koliko kandidata iz brze pretrage ide rerankeru na ocjenjivanje
BROJ_ZA_RERANK = 40
# Duzi tekst rerankeru ne donosi nista, a duplo je sporiji: sa 512 tokena
# prosjek je bio 9.0s, sa 192 tokena 4.7s, uz identicne rezultate.
RERANKER_MAX_TOKENA = 192
# koliko najboljih iz brze pretrage reranker ne smije da izbaci
GARANTOVANO_IZ_BRZE_PRETRAGE = 3
KORISTI_RERANKER = True

_model = None
_reranker = None
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


def _ucitaj_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_NAZIV, max_length=RERANKER_MAX_TOKENA)
    return _reranker


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

    poredani_idevi = sorted(skorovi, key=skorovi.get, reverse=True)

    if KORISTI_RERANKER and len(poredani_idevi) > n_results:
        # brza pretraga samo grubo suzava izbor; reranker cita pitanje i chunk
        # zajedno i ocjenjuje da li tekst zaista odgovara na pitanje
        kandidati = poredani_idevi[:BROJ_ZA_RERANK]
        reranker = _ucitaj_reranker()
        ocjene = reranker.predict(
            [(upit, _dokumenti_po_idu[i]) for i in kandidati], batch_size=64
        )
        rerank_poredak = [
            i for i, _ in sorted(zip(kandidati, ocjene), key=lambda p: p[1], reverse=True)
        ]

        # Reranker je bolji na proznom tekstu, ali losije rangira tabele (kontakti,
        # spiskovi predmeta) - zna da izbaci tacan dokument koji je brza pretraga
        # dobro rangirala. Zato se dva poretka spajaju, pa preziv i chunk koji je
        # jak u samo jednom od njih.
        spojeni = {}
        for rang, chunk_id in enumerate(kandidati):
            spojeni[chunk_id] = spojeni.get(chunk_id, 0) + 1 / (RRF_KONSTANTA + rang + 1)
        for rang, chunk_id in enumerate(rerank_poredak):
            spojeni[chunk_id] = spojeni.get(chunk_id, 0) + 1 / (RRF_KONSTANTA + rang + 1)

        spojeni_poredak = sorted(spojeni, key=spojeni.get, reverse=True)

        # Reranker i dalje zna da izbaci tacan chunk kad je u obliku spiska ili
        # tabele. Zato prva tri pogotka brze pretrage imaju zagarantovano mjesto -
        # reranker smije da mijenja redoslijed, ali ne i da ih ukloni.
        zagarantovani = kandidati[:GARANTOVANO_IZ_BRZE_PRETRAGE]
        konacni = list(zagarantovani)
        for chunk_id in spojeni_poredak:
            if len(konacni) >= n_results:
                break
            if chunk_id not in konacni:
                konacni.append(chunk_id)

        poredani_idevi = sorted(konacni, key=lambda i: spojeni.get(i, 0), reverse=True)
        skorovi = spojeni
    else:
        poredani_idevi = poredani_idevi[:n_results]

    chunkovi = []
    for chunk_id in poredani_idevi:
        chunkovi.append({
            "tekst": _dokumenti_po_idu[chunk_id],
            "metadata": _metadata_po_idu[chunk_id],
            "skor": skorovi[chunk_id],
        })

    return chunkovi
