import re
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

# Groq besplatni tier: 8000 tokena po minuti, a jedan nas upit (6 chunkova) trosi
# oko 3.5k tokena - zato pauza od 35s (~6k/min, sigurno ispod limita).
PAUZA = 35.0
MAX_POKUSAJA = 5
PAUZA_POSLIJE_429 = 60.0


def pogodjen_izvor(ocekivani, dobijeni):
    if not ocekivani:
        return None
    return any(o in dobijeni for o in ocekivani)


def ucitaj_dosadasnje():
    # rezultati se snimaju poslije svakog pitanja, pa se prekinut prolaz
    # moze nastaviti umjesto da krece iz pocetka
    if not REZULTATI_JSON.exists():
        return {}
    try:
        stari = json.loads(REZULTATI_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {r["id"]: r for r in stari if not r.get("greska")}


def pitaj_sa_ponavljanjem(pitanje):
    for pokusaj in range(1, MAX_POKUSAJA + 1):
        try:
            odgovor, chunkovi = odgovori(pitanje)
            izvori = [c["metadata"]["naslov_dokumenta"] for c in chunkovi]
            return odgovor, izvori, None
        except Exception as e:
            greska = str(e)
            if ("rate_limit" in greska or "429" in greska) and pokusaj < MAX_POKUSAJA:
                print(f"    rate limit, cekam {PAUZA_POSLIJE_429:.0f}s (pokusaj {pokusaj})", flush=True)
                time.sleep(PAUZA_POSLIJE_429)
                continue
            return "", [], greska
    return "", [], "iscrpljeni pokusaji"


def main():
    pitanja = json.loads(PITANJA_PUTANJA.read_text(encoding="utf-8"))
    gotovi = ucitaj_dosadasnje()

    if gotovi:
        print(f"Nastavljam - vec je odradjeno {len(gotovi)} od {len(pitanja)} pitanja\n", flush=True)

    rezultati = []

    for i, stavka in enumerate(pitanja, start=1):
        if stavka["id"] in gotovi:
            print(f"[{i}/{len(pitanja)}] {stavka['id']}: preskacem (vec odradjeno)", flush=True)
            rezultati.append(gotovi[stavka["id"]])
            continue

        print(f"[{i}/{len(pitanja)}] {stavka['id']}: {stavka['pitanje'][:60]}...", flush=True)

        odgovor, izvori, greska = pitaj_sa_ponavljanjem(stavka["pitanje"])

        rezultati.append({
            **stavka,
            "odgovor": odgovor,
            "dobijeni_izvori": izvori,
            # kod greske API-ja nema smisla racunati pogodak izvora - upit nije ni izvrsen
            "izvor_pogodjen": None if greska else pogodjen_izvor(stavka["ocekivani_izvori"], izvori),
            "greska": greska,
        })

        # snimaj odmah, da prekid ne ponisti dosadasnji rad
        REZULTATI_JSON.write_text(
            json.dumps(rezultati, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        if greska:
            print(f"    GRESKA: {greska[:90]}", flush=True)

        time.sleep(PAUZA)

    napisi_markdown(rezultati)

    ukupno_sa_ocekivanim = [r for r in rezultati if r["izvor_pogodjen"] is not None]
    pogodjenih = [r for r in ukupno_sa_ocekivanim if r["izvor_pogodjen"]]
    sa_greskom = [r for r in rezultati if r["greska"]]

    print(f"\nObradjeno pitanja: {len(rezultati)}/{len(pitanja)}", flush=True)
    if ukupno_sa_ocekivanim:
        procenat = 100 * len(pogodjenih) / len(ukupno_sa_ocekivanim)
        print(f"Retrieval hit rate: {len(pogodjenih)}/{len(ukupno_sa_ocekivanim)} ({procenat:.0f}%)", flush=True)
    if sa_greskom:
        print(f"Pitanja sa greskom API-ja: {', '.join(r['id'] for r in sa_greskom)}", flush=True)
    else:
        print("Sva pitanja uspjesno odradjena.", flush=True)
    print(f"Rezultati: {REZULTATI_MD}", flush=True)


def procitaj_postojece_ocjene():
    # rezultati.md se pregenerise pri svakom prolazu, pa rucno upisane ocjene
    # moraju da se sacuvaju i vrate nazad - inace bi se izgubile
    if not REZULTATI_MD.exists():
        return {}

    tekst = REZULTATI_MD.read_text(encoding="utf-8")
    ocjene = {}
    trenutni_id = None

    for linija in tekst.split("\n"):
        naslov = re.match(r'^## (\S+) \(', linija)
        if naslov:
            trenutni_id = naslov.group(1)
            continue

        red = re.match(r'^\|(?!\s*-)(.*)\|(.*)\|\s*$', linija)
        if trenutni_id and red:
            ocjena = red.group(1).strip()
            napomena = red.group(2).strip()
            if ocjena.lower() in ("ocjena",) or set(ocjena) <= {"-", " "}:
                continue
            if ocjena or napomena:
                ocjene[trenutni_id] = (ocjena, napomena)
                trenutni_id = None

    return ocjene


def napisi_markdown(rezultati):
    ranije_ocjene = procitaj_postojece_ocjene()
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
        redovi.append(f"## {r['id']} ({r['kategorija']}): {r['pitanje']}")
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
        ocjena, napomena = ranije_ocjene.get(r["id"], ("", ""))
        redovi.append("| Ocjena | Napomena |")
        redovi.append("|---|---|")
        redovi.append(f"| {ocjena} | {napomena} |")
        redovi.append("")
        redovi.append("---")
        redovi.append("")

    REZULTATI_MD.write_text("\n".join(redovi), encoding="utf-8")


if __name__ == "__main__":
    main()
