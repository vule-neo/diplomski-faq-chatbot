"""Povezivanje dokumenata sa njihovim kasnijim izmjenama.

Izmjene pravilnika i statuta stoje u bazi kao zasebni dokumenti ("u članu 41. riječi
... zamjenjuju se riječima ..."), bez ikakve veze sa članom koji mijenjaju. Bez toga
sistem može servirati ukinutu odredbu kao da važi.

Ovdje se iz teksta izmjena izvlači koji su članovi dirani, pa se u chunkove osnovnog
dokumenta koji se odnose na te članove dodaje upozorenje.
"""

import re
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
MAPA_PUTANJA = PROCESSED_DIR / "izmjene.json"

# koji dokument mijenja koji (naslov izmjene -> naslov osnovnog dokumenta)
IZMJENE_DOKUMENATA = {
    "Izmena statuta": "Statut_ETFa_2018",
    "Izmena_Pravilnika_o_OAS-2024": "Pravilnik_o_OAS_preciscen_jun_2023",
    "Izmena Pravilnika o osnovnim akademskim studijama-2025": "Pravilnik_o_OAS_preciscen_jun_2023",
}

# "У члану 41. став" / "U članu 26." / "После члана 69."
CLAN_U_IZMJENI = re.compile(r'(?:члану|члана|čланu|članu|člana)\s+(\d+)', re.IGNORECASE)


def nadji_dokument(naslov):
    for meta_putanja in PROCESSED_DIR.rglob("metadata.json"):
        meta = json.loads(meta_putanja.read_text(encoding="utf-8"))
        if meta["title"] == naslov:
            return meta_putanja.parent
    return None


def izvuci_izmijenjene_clanove(folder):
    tekst = (folder / "document.md").read_text(encoding="utf-8")
    return sorted({int(b) for b in CLAN_U_IZMJENI.findall(tekst)})


def main():
    mapa = {}

    for naslov_izmjene, naslov_osnovnog in IZMJENE_DOKUMENATA.items():
        folder = nadji_dokument(naslov_izmjene)
        if folder is None:
            print(f"preskacem, nema dokumenta: {naslov_izmjene}")
            continue

        clanovi = izvuci_izmijenjene_clanove(folder)
        if not clanovi:
            print(f"nijedan clan nije prepoznat u: {naslov_izmjene}")
            continue

        stavka = mapa.setdefault(naslov_osnovnog, {})
        for broj in clanovi:
            stavka.setdefault(str(broj), []).append(naslov_izmjene)

        print(f"{naslov_izmjene} -> {naslov_osnovnog}: mijenja clanove {clanovi}")

    MAPA_PUTANJA.write_text(
        json.dumps(mapa, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nUpisano u {MAPA_PUTANJA}")


if __name__ == "__main__":
    main()
