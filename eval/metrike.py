import re
import sys
import json
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")

EVAL_DIR = Path(__file__).resolve().parent
REZULTATI_MD = EVAL_DIR / "rezultati.md"
REZULTATI_JSON = EVAL_DIR / "rezultati.json"
IZVJESTAJ = EVAL_DIR / "metrike.md"

OPIS_KATEGORIJA = {
    "A": "Osnovna pitanja u domenu",
    "B": "Pitanja koja zahtijevaju uslov važenja",
    "C": "Pitanja van domena (očekuje se odbijanje)",
    "D": "Djelimično pokrivena pitanja",
    "E": "Robusnost na formulaciju",
    "F": "Otpornost na prompt injection",
}

OPIS_OCJENE = {
    "T": "tačno",
    "D": "djelimično",
    "N": "netačno",
    "NZ": "odbio da odgovori",
}


def procitaj_ocjene():
    tekst = REZULTATI_MD.read_text(encoding="utf-8")
    ocjene = {}
    trenutni = None

    for linija in tekst.split("\n"):
        naslov = re.match(r'^## (\S+) \(', linija)
        if naslov:
            trenutni = naslov.group(1)
            continue

        red = re.match(r'^\|(?!\s*-)(.*?)\|(.*)\|\s*$', linija)
        if trenutni and red:
            ocjena = red.group(1).strip()
            napomena = red.group(2).strip()
            if ocjena.lower() == "ocjena" or not ocjena:
                continue
            ocjene[trenutni] = (ocjena.upper(), napomena)
            trenutni = None

    return ocjene


def main():
    rezultati = json.loads(REZULTATI_JSON.read_text(encoding="utf-8"))
    ocjene = procitaj_ocjene()

    po_kategoriji = defaultdict(list)
    for r in rezultati:
        ocjena = ocjene.get(r["id"], ("?", ""))[0]
        po_kategoriji[r["kategorija"]].append((r, ocjena))

    ukupno = Counter(o for _, o in [(r, ocjene.get(r["id"], ("?", ""))[0]) for r in rezultati])
    broj_pitanja = len(rezultati)
    tacnih = ukupno.get("T", 0)

    sa_ocekivanim = [r for r in rezultati if r["izvor_pogodjen"] is not None]
    pogodjenih = [r for r in sa_ocekivanim if r["izvor_pogodjen"]]

    lazna_odbijanja = [
        (r["id"], ocjene.get(r["id"], ("", ""))[1])
        for r in rezultati
        if ocjene.get(r["id"], ("", ""))[0] == "N"
    ]

    redovi = [
        "# Metrike evaluacije",
        "",
        f"Ukupno pitanja: **{broj_pitanja}**. Ocjene su unesene ručno u `rezultati.md`,",
        "poređenjem svakog odgovora sa izvornim dokumentom.",
        "",
        "## Ukupan rezultat",
        "",
        "| Ocjena | Značenje | Broj | Udio |",
        "|---|---|---:|---:|",
    ]

    for oznaka in ("T", "D", "N", "NZ"):
        broj = ukupno.get(oznaka, 0)
        if broj:
            redovi.append(
                f"| {oznaka} | {OPIS_OCJENE[oznaka]} | {broj} | {100 * broj / broj_pitanja:.0f}% |"
            )

    redovi += [
        "",
        f"**Tačnost: {tacnih}/{broj_pitanja} ({100 * tacnih / broj_pitanja:.0f}%)**",
        "",
        "## Rezultat po kategorijama",
        "",
        "| Kategorija | Opis | T | D | N | Ukupno | Tačnost |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]

    for oznaka in sorted(po_kategoriji):
        stavke = po_kategoriji[oznaka]
        brojac = Counter(o for _, o in stavke)
        n = len(stavke)
        t = brojac.get("T", 0)
        redovi.append(
            f"| {oznaka} | {OPIS_KATEGORIJA.get(oznaka, '')} | {t} | "
            f"{brojac.get('D', 0)} | {brojac.get('N', 0)} | {n} | {100 * t / n:.0f}% |"
        )

    redovi += [
        "",
        "## Pretraga (retrieval)",
        "",
        "Mjereno automatski: da li je među vraćenim izvorima bio dokument za koji je",
        "unaprijed određeno da sadrži odgovor. Računato samo za pitanja kod kojih takav",
        "dokument postoji (pitanja van domena nemaju očekivani izvor).",
        "",
        f"- Pitanja sa definisanim očekivanim izvorom: **{len(sa_ocekivanim)}**",
        f"- Očekivani izvor pronađen: **{len(pogodjenih)}** "
        f"(**{100 * len(pogodjenih) / len(sa_ocekivanim):.0f}%**)",
        "",
    ]

    promasaji = [r["id"] for r in sa_ocekivanim if not r["izvor_pogodjen"]]
    if promasaji:
        redovi.append(f"Promašeni izvor: {', '.join(promasaji)}")
        redovi.append("")

    redovi += [
        "## Netačni odgovori",
        "",
    ]

    if lazna_odbijanja:
        for ident, napomena in lazna_odbijanja:
            redovi.append(f"- **{ident}** — {napomena}")
    else:
        redovi.append("Nema netačnih odgovora.")

    redovi.append("")

    IZVJESTAJ.write_text("\n".join(redovi), encoding="utf-8")

    print(f"Tačnost: {tacnih}/{broj_pitanja} ({100 * tacnih / broj_pitanja:.0f}%)")
    print(f"Retrieval hit rate: {len(pogodjenih)}/{len(sa_ocekivanim)}")
    print(f"Izvještaj: {IZVJESTAJ}")


if __name__ == "__main__":
    main()
