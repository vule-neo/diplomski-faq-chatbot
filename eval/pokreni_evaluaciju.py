import sys
import json
import time
from pathlib import Path

KORIJEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORIJEN / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from llm.rag import odgovori

EVAL_DIR = Path(__file__).resolve().parent
PITANJA_PUTANJA = EVAL_DIR / "pitanja.json"
REZULTATI_MD = EVAL_DIR / "rezultati.md"
REZULTATI_JSON = EVAL_DIR / "rezultati.json"

# Groq besplatni tier ima limit od 8000 tokena po minuti, a jedan nas upit trosi
# oko 3-4k tokena (kontekst od 6 chunkova), pa realno mozemo oko 2 poziva u minuti.
PAUZA = 22.0
MAX_POKUSAJA = 4
PAUZA_POSLIJE_429 = 35.0


def pogodjen_izvor(ocekivani, dobijeni):
    if not ocekivani:
        return None
    return any(o in dobijeni for o in ocekivani)


def main():
    pitanja = json.loads(PITANJA_PUTANJA.read_text(encoding="utf-8"))
    rezultati = []

    for i, stavka in enumerate(pitanja, start=1):
        print(f"[{i}/{len(pitanja)}] {stavka['id']}: {stavka['pitanje'][:60]}...")

        odgovor, izvori, greska = "", [], None
        for pokusaj in range(1, MAX_POKUSAJA + 1):
            try:
                odgovor, chunkovi = odgovori(stavka["pitanje"])
                izvori = [c["metadata"]["naslov_dokumenta"] for c in chunkovi]
                greska = None
                break
            except Exception as e:
                greska = str(e)
                if "rate_limit" in greska or "429" in greska:
                    if pokusaj < MAX_POKUSAJA:
                        print(f"    rate limit, cekam {PAUZA_POSLIJE_429:.0f}s (pokusaj {pokusaj})")
                        time.sleep(PAUZA_POSLIJE_429)
                        continue
                break

        rezultati.append({
            **stavka,
            "odgovor": odgovor,
            "dobijeni_izvori": izvori,
            # kod greske API-ja nema smisla racunati pogodak izvora - upit nije ni izvrsen
            "izvor_pogodjen": None if greska else pogodjen_izvor(stavka["ocekivani_izvori"], izvori),
            "greska": greska,
        })

        time.sleep(PAUZA)

    REZULTATI_JSON.write_text(
        json.dumps(rezultati, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    napisi_markdown(rezultati)

    ukupno_sa_ocekivanim = [r for r in rezultati if r["izvor_pogodjen"] is not None]
    pogodjenih = [r for r in ukupno_sa_ocekivanim if r["izvor_pogodjen"]]
    sa_greskom = [r for r in rezultati if r["greska"]]

    if ukupno_sa_ocekivanim:
        procenat = 100 * len(pogodjenih) / len(ukupno_sa_ocekivanim)
        print(f"\nRetrieval hit rate: {len(pogodjenih)}/{len(ukupno_sa_ocekivanim)} ({procenat:.0f}%)")
    if sa_greskom:
        print(f"Pitanja sa greskom API-ja (nisu uracunata): {', '.join(r['id'] for r in sa_greskom)}")
    print(f"Rezultati: {REZULTATI_MD}")


def napisi_markdown(rezultati):
    redovi = [
        "# Rezultati evaluacije",
        "",
        "Automatski generisano skriptom `pokreni_evaluaciju.py`. **Kolonu `Ocjena` i",
        "`Napomena` popuniti ručno**, poređenjem sa originalnim dokumentom.",
        "",
        "Ocjene: `T` = tačno, `D` = djelimično, `N` = netačno, `NZ` = rekao da ne zna.",
        "Za kategoriju C (van domena) `T` znači da je ispravno odbio da odgovori.",
        "",
        "---",
        "",
    ]

    for r in rezultati:
        pogodak = {True: "da", False: "NE", None: "-"}[r["izvor_pogodjen"]]
        redovi.append(f"## {r['id']} ({r['kategorija']}) — {r['pitanje']}")
        redovi.append("")
        redovi.append(f"- **Očekivano ponašanje:** {r['ocekivano_ponasanje']}")
        if r["napomena"]:
            redovi.append(f"- **Napomena uz pitanje:** {r['napomena']}")
        redovi.append(f"- **Očekivani izvor pronađen:** {pogodak}")
        redovi.append(f"- **Vraćeni izvori:** {', '.join(dict.fromkeys(r['dobijeni_izvori'])) or '-'}")
        redovi.append("")
        if r["greska"]:
            redovi.append(f"> GREŠKA: {r['greska']}")
        else:
            redovi.append("**Odgovor:**")
            redovi.append("")
            for linija in r["odgovor"].split("\n"):
                redovi.append(f"> {linija}")
        redovi.append("")
        redovi.append("| Ocjena | Napomena |")
        redovi.append("|---|---|")
        redovi.append("|  |  |")
        redovi.append("")
        redovi.append("---")
        redovi.append("")

    REZULTATI_MD.write_text("\n".join(redovi), encoding="utf-8")


if __name__ == "__main__":
    main()
