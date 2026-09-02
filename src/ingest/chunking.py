import re
import json

from obradi_dokumente import PROCESSED_DIR

MAX_CHUNK_KARAKTERA = 1200
PREKLAPANJE_KARAKTERA = 250
NASLOV_H1_REGEX = re.compile(r'(?m)^# .+\n+')
NASLOV_SEKCIJE_REGEX = re.compile(r'(?m)^## (.+)$')
BROJ_CLANA_REGEX = re.compile(r'(\d+)')

IZMJENE_PUTANJA = PROCESSED_DIR / "izmjene.json"


def ucitaj_izmjene():
    if not IZMJENE_PUTANJA.exists():
        return {}
    return json.loads(IZMJENE_PUTANJA.read_text(encoding="utf-8"))


def upozorenje_o_izmjeni(izmjene, naslov_dokumenta, sekcija):
    if not sekcija or naslov_dokumenta not in izmjene:
        return None

    broj = BROJ_CLANA_REGEX.search(sekcija)
    if not broj:
        return None

    dokumenti = izmjene[naslov_dokumenta].get(broj.group(1))
    if not dokumenti:
        return None

    spisak = ", ".join(sorted(set(dokumenti)))
    return (
        f"[NAPOMENA: ovaj član je kasnije mijenjan dokumentom: {spisak}. "
        f"Tekst ispod je izvorna verzija, provjeriti izmjene prije nego se navede kao važeći.]"
    )


def podijeli_na_sekcije(tekst):
    delovi = NASLOV_SEKCIJE_REGEX.split(tekst)

    sekcije = []
    uvod = delovi[0].strip()
    if uvod:
        sekcije.append((None, uvod))

    for i in range(1, len(delovi), 2):
        naslov = delovi[i].strip()
        sadrzaj = delovi[i + 1].strip() if i + 1 < len(delovi) else ""
        if sadrzaj:
            sekcije.append((naslov, sadrzaj))

    return sekcije


def podijeli_tekst_do_granice(sadrzaj, max_karaktera, razdvajac='\n\n'):
    dijelovi = [d.strip() for d in sadrzaj.split(razdvajac) if d.strip()]
    grupe = []
    trenutna = []
    trenutna_duzina = 0

    for dio in dijelovi:
        if len(dio) > max_karaktera:
            if trenutna:
                grupe.append(razdvajac.join(trenutna))
                trenutna = []
                trenutna_duzina = 0
            if razdvajac == '\n\n':
                grupe.extend(podijeli_tekst_do_granice(dio, max_karaktera, razdvajac='\n'))
            else:
                # ni pojedinacan red se ne moze dalje usitniti, ostavi ga kako jeste
                grupe.append(dio)
            continue

        if trenutna and trenutna_duzina + len(dio) + len(razdvajac) > max_karaktera:
            grupe.append(razdvajac.join(trenutna))
            trenutna = []
            trenutna_duzina = 0

        trenutna.append(dio)
        trenutna_duzina += len(dio) + len(razdvajac)

    if trenutna:
        grupe.append(razdvajac.join(trenutna))

    return grupe


def dodaj_preklapanje(grupe, preklapanje=PREKLAPANJE_KARAKTERA):
    if len(grupe) < 2:
        return grupe

    sa_preklapanjem = [grupe[0]]
    for i in range(1, len(grupe)):
        rep = grupe[i - 1][-preklapanje:]
        prelom = rep.find('\n')
        if prelom != -1:
            rep = rep[prelom + 1:]
        sa_preklapanjem.append(f"{rep.strip()}\n{grupe[i]}" if rep.strip() else grupe[i])

    return sa_preklapanjem


def napravi_chunkove_za_dokument(folder, izmjene=None):
    izmjene = izmjene or {}
    tekst = (folder / "document.md").read_text(encoding="utf-8")
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))

    tekst = NASLOV_H1_REGEX.sub('', tekst, count=1)
    sekcije = podijeli_na_sekcije(tekst)

    chunkovi = []
    redni_broj = 0

    for naslov_sekcije, sadrzaj in sekcije:
        if len(sadrzaj) <= MAX_CHUNK_KARAKTERA:
            grupe = [sadrzaj]
        else:
            grupe = dodaj_preklapanje(podijeli_tekst_do_granice(sadrzaj, MAX_CHUNK_KARAKTERA))

        napomena = upozorenje_o_izmjeni(izmjene, metadata["title"], naslov_sekcije)
        if napomena:
            grupe = [f"{napomena}\n{g}" for g in grupe]

        for grupa in grupe:
            redni_broj += 1
            chunkovi.append({
                "id": f"{folder.name}__{redni_broj}",
                "tekst": grupa,
                "naslov_dokumenta": metadata["title"],
                "kategorija": metadata["category"],
                "sekcija": naslov_sekcije or "",
                "original_file": metadata["original_file"],
                "ocr": metadata.get("ocr", False),
            })

    return chunkovi


def main():
    svi_chunkovi = []
    broj_dokumenata = 0

    izmjene = ucitaj_izmjene()

    for meta_putanja in sorted(PROCESSED_DIR.rglob("metadata.json")):
        folder = meta_putanja.parent
        svi_chunkovi.extend(napravi_chunkove_za_dokument(folder, izmjene))
        broj_dokumenata += 1

    izlazna_putanja = PROCESSED_DIR / "chunks.jsonl"
    with open(izlazna_putanja, "w", encoding="utf-8") as f:
        for chunk in svi_chunkovi:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"Napravljeno {len(svi_chunkovi)} chunkova iz {broj_dokumenata} dokumenata -> {izlazna_putanja}")


if __name__ == "__main__":
    main()
