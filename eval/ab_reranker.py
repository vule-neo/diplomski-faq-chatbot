"""A/B poredjenje pretrage sa rerankerom i bez njega.

Ne poziva LLM - mjeri samo da li je medju vracenim izvorima onaj za koji je unaprijed
odredjeno da sadrzi odgovor. Zato je besplatno i moze se pokretati koliko god puta.
"""

import sys
import json
import time
from pathlib import Path

KORIJEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORIJEN / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import retrieval.pretraga as P

EVAL_DIR = Path(__file__).resolve().parent
IZVJESTAJ = EVAL_DIR / "ab_reranker.md"
BROJ_IZVORA = 10


def pogodak(stavka, chunkovi):
    izvori = [c["metadata"]["naslov_dokumenta"] for c in chunkovi]
    return any(o in izvori for o in stavka["ocekivani_izvori"])


def izmjeri(pitanja, koristi_reranker):
    P.KORISTI_RERANKER = koristi_reranker
    P.pretrazi("zagrijavanje", n_results=BROJ_IZVORA)  # da mjerenje ne uhvati ucitavanje

    rezultati = {}
    ukupno_vrijeme = 0.0

    for stavka in pitanja:
        pocetak = time.time()
        chunkovi = P.pretrazi(stavka["pitanje"], n_results=BROJ_IZVORA)
        ukupno_vrijeme += time.time() - pocetak
        rezultati[stavka["id"]] = pogodak(stavka, chunkovi)

    return rezultati, ukupno_vrijeme / len(pitanja)


def main():
    sva_pitanja = json.loads((EVAL_DIR / "pitanja.json").read_text(encoding="utf-8"))
    pitanja = [p for p in sva_pitanja if p["ocekivani_izvori"]]

    print(f"Mjerim na {len(pitanja)} pitanja koja imaju definisan ocekivani izvor.\n")

    print("bez rerankera...", flush=True)
    bez, vrijeme_bez = izmjeri(pitanja, False)

    print("sa rerankerom...", flush=True)
    sa, vrijeme_sa = izmjeri(pitanja, True)

    dobijeno = [p for p in pitanja if sa[p["id"]] and not bez[p["id"]]]
    izgubljeno = [p for p in pitanja if bez[p["id"]] and not sa[p["id"]]]
    n = len(pitanja)
    br_bez = sum(bez.values())
    br_sa = sum(sa.values())

    redovi = [
        "# A/B poređenje: pretraga sa rerankerom i bez njega",
        "",
        "Mjereno bez poziva LLM-a, provjerava se samo da li je među prvih "
        f"{BROJ_IZVORA} vraćenih izvora bio dokument za koji je unaprijed određeno da",
        "sadrži odgovor. Zbog toga mjerenje ne troši Groq kvotu i ponovljivo je.",
        "",
        f"Uzorak: **{n} pitanja** (od ukupno {len(sva_pitanja)}; pitanja van domena nemaju",
        "očekivani izvor pa nisu uključena).",
        "",
        "## Rezultat",
        "",
        "| | Pronađen izvor | Prosječno vrijeme |",
        "|---|---:|---:|",
        f"| Bez rerankera | {br_bez}/{n} ({100*br_bez/n:.0f}%) | {vrijeme_bez:.2f}s |",
        f"| Sa rerankerom | {br_sa}/{n} ({100*br_sa/n:.0f}%) | {vrijeme_sa:.2f}s |",
        "",
        f"Razlika: **{br_sa - br_bez:+d} pitanja**, uz **{vrijeme_sa - vrijeme_bez:+.2f}s** po upitu.",
        "",
    ]

    redovi += ["## Pitanja koja reranker dobija", ""]
    if dobijeno:
        for p in dobijeno:
            redovi.append(f"- **{p['id']}** ({p['kategorija']}): {p['pitanje']}")
    else:
        redovi.append("Nema.")

    redovi += ["", "## Pitanja koja reranker gubi", ""]
    if izgubljeno:
        for p in izgubljeno:
            redovi.append(f"- **{p['id']}** ({p['kategorija']}): {p['pitanje']}")
    else:
        redovi.append("Nema, reranker ne kvari nijedno pitanje koje je i prije radilo.")

    redovi += ["", "## Po pitanju", "", "| ID | Kategorija | Bez | Sa | |", "|---|---|:-:|:-:|---|"]
    for p in pitanja:
        b, s = bez[p["id"]], sa[p["id"]]
        oznaka = "dobija" if (s and not b) else ("gubi" if (b and not s) else "")
        redovi.append(
            f"| {p['id']} | {p['kategorija']} | {'da' if b else 'ne'} | {'da' if s else 'ne'} | {oznaka} |"
        )

    IZVJESTAJ.write_text("\n".join(redovi) + "\n", encoding="utf-8")

    print(f"\nBez rerankera: {br_bez}/{n} ({vrijeme_bez:.2f}s po upitu)")
    print(f"Sa rerankerom: {br_sa}/{n} ({vrijeme_sa:.2f}s po upitu)")
    print(f"Dobija: {[p['id'] for p in dobijeno]}")
    print(f"Gubi:   {[p['id'] for p in izgubljeno]}")
    print(f"\nIzvjestaj: {IZVJESTAJ}")


if __name__ == "__main__":
    main()
