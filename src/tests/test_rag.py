import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from llm.rag import odgovori

PITANJA = [
    "Koliko iznosi školarina za samofinansirajuće studente prve godine?",
    "Koliko ESPB bodova je potrebno za upis u narednu godinu studija?",
    "Koja je disciplinska mjera za prepisivanje na ispitu?",
    "Koji je broj žiro računa fakulteta?",
    "Da li ETF ima teleport za studente?",
]

for pitanje in PITANJA:
    odgovor, chunkovi = odgovori(pitanje)
    print(f"PITANJE: {pitanje}")
    print(f"ODGOVOR: {odgovor}")
    print("IZVORI:")
    for c in chunkovi:
        print(f"  - {c['metadata']['naslov_dokumenta']} / {c['metadata']['sekcija']} (skor {c['skor']:.4f})")
    print("=" * 80)
