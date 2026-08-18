import sys
import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from normalizacija import u_latinicu

sys.stdout.reconfigure(encoding="utf-8")

PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
BAZA_PUTANJA = Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db"
KOLEKCIJA_NAZIV = "dokumenti"
MODEL_NAZIV = "paraphrase-multilingual-MiniLM-L12-v2"

TEST_UPIT = "Koji su rokovi za prijavu ispita?"


def ucitaj_chunkove():
    chunkovi = []
    with open(PROCESSED_DIR / "chunks.jsonl", encoding="utf-8") as f:
        for linija in f:
            chunkovi.append(json.loads(linija))
    return chunkovi


def main():
    chunkovi = ucitaj_chunkove()
    print(f"Ucitano {len(chunkovi)} chunkova iz chunks.jsonl")

    model = SentenceTransformer(MODEL_NAZIV)
    tekstovi = [c["tekst"] for c in chunkovi]
    tekstovi_za_embedding = [u_latinicu(t) for t in tekstovi]

    print("Racunam embeddinge...")
    embeddinzi = model.encode(tekstovi_za_embedding, show_progress_bar=True).tolist()

    client = chromadb.PersistentClient(path=str(BAZA_PUTANJA))
    kolekcija = client.get_or_create_collection(name=KOLEKCIJA_NAZIV)

    ids = [c["id"] for c in chunkovi]
    metadatas = [
        {
            "naslov_dokumenta": c["naslov_dokumenta"],
            "kategorija": c["kategorija"],
            "sekcija": c["sekcija"],
            "original_file": c["original_file"],
            "ocr": c["ocr"],
        }
        for c in chunkovi
    ]

    kolekcija.upsert(
        ids=ids,
        documents=tekstovi,
        embeddings=embeddinzi,
        metadatas=metadatas,
    )

    print(f"Upisano {len(chunkovi)} chunkova u kolekciju '{KOLEKCIJA_NAZIV}' ({BAZA_PUTANJA})")

    test_embedding = model.encode([u_latinicu(TEST_UPIT)]).tolist()
    rezultati = kolekcija.query(query_embeddings=test_embedding, n_results=3)

    print(f"\nTest upit: {TEST_UPIT}")
    for dokument, meta, distanca in zip(
        rezultati["documents"][0], rezultati["metadatas"][0], rezultati["distances"][0]
    ):
        print(f"  [{distanca:.3f}] {meta['naslov_dokumenta']} / {meta['sekcija']}")
        print(f"    {dokument[:120]}...")


if __name__ == "__main__":
    main()
