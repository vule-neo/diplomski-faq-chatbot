import re
import sys
import json
import fitz
import pdfplumber
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

SKEN_PRAG = 50
MAX_PROSJECNA_DUZINA_CELIJE = 50

CLAN_REGEX = re.compile(r'(?m)^((?:Члан|Član)\s+\d+\.?)')

DATUM_VRIJEME_REGEX = re.compile(r'^\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}$')
URL_REGEX = re.compile(r'^https?://\S+$')
BROJ_STRANE_REGEX = re.compile(r'^\d+/\d+$')
ZIRO_RACUN_REGEX = re.compile(r'^\d{2,3}-\d{4,}-\d{2}$')
SAMOSTALNA_STRANA_REGEX = re.compile(r'^\d{1,4}$')
SAMO_INTERPUNKCIJA_REGEX = re.compile(r'^[\W_]{1,3}$')
# red iz sadrzaja dokumenta: naslov pa niz tacaka pa broj strane
SADRZAJ_REGEX = re.compile(r'\.{5,}\s*\d*\s*$')
# ostaci navigacije sa sajta ("NAVIGACIJA", "Cenovnik | ETF", "Studentski odsek | ETF")
NAVIGACIJA_REGEX = re.compile(r'^[^|]{1,60}\s\|\s*ETF\s*$')
POZNATO_SMECE = {"Пријемни ЕТФ", "NAVIGACIJA"}


def je_sken(putanja):
    doc = fitz.open(putanja)
    ukupno = sum(len(strana.get_text()) for strana in doc)
    broj_strana = doc.page_count
    doc.close()
    if broj_strana == 0:
        return True
    return (ukupno / broj_strana) < SKEN_PRAG


def izvuci_tekst(putanja):
    doc = fitz.open(putanja)
    strane = [strana.get_text() for strana in doc]
    doc.close()
    return "\n\n".join(strane)


def je_prava_tabela(tabela):
    if len(tabela) < 2:
        return False
    sve_celije = [c.strip() for red in tabela for c in red if c and c.strip()]
    if not sve_celije:
        return False
    prosjecna_duzina = sum(len(c) for c in sve_celije) / len(sve_celije)
    return prosjecna_duzina <= MAX_PROSJECNA_DUZINA_CELIJE


def tabela_u_markdown(tabela):
    redovi = []
    for i, red in enumerate(tabela):
        celije = [c.strip() if c else "" for c in red]
        redovi.append("| " + " | ".join(celije) + " |")
        if i == 0:
            redovi.append("|" + "---|" * len(celije))
    return "\n".join(redovi)


def izvuci_prave_tabele(putanja):
    prave = []
    with pdfplumber.open(putanja) as pdf:
        for strana in pdf.pages:
            for tabela in strana.extract_tables():
                if je_prava_tabela(tabela):
                    prave.append(tabela)
    return prave


def strukturiraj(tekst):
    return CLAN_REGEX.sub(r'## \1', tekst)


def normalizuj(tekst, naslov=None):
    linije = []
    for linija in tekst.split('\n'):
        gola = linija.strip()
        if DATUM_VRIJEME_REGEX.match(gola):
            continue
        if URL_REGEX.match(gola):
            continue
        if BROJ_STRANE_REGEX.match(gola):
            continue
        if SAMOSTALNA_STRANA_REGEX.match(gola):
            continue
        if SAMO_INTERPUNKCIJA_REGEX.match(gola):
            continue
        if gola in POZNATO_SMECE:
            continue
        if SADRZAJ_REGEX.search(gola):
            continue
        if NAVIGACIJA_REGEX.match(gola):
            continue
        if naslov and gola == naslov:
            continue
        if ZIRO_RACUN_REGEX.match(gola):
            # ovakav broj se u tekstu inace pojavljuje "go", bez ikakve oznake ispred,
            # pa LLM kasnije ne zna sigurno da je to bas broj racuna (ili jos gore,
            # pobrka ga sa "poziv na broj" kodom iznad) - eksplicitno ga oznacimo
            linija = f"Broj žiro računa: {gola}"
        linije.append(linija)

    bez_duplikata = []
    for linija in linije:
        if bez_duplikata and linija.strip() and linija.strip() == bez_duplikata[-1].strip():
            continue
        bez_duplikata.append(linija)

    tekst = '\n'.join(bez_duplikata)
    tekst = re.sub(r'\n{3,}', '\n\n', tekst)
    return tekst.strip()


def slugify(ime):
    ime = re.sub(r'[\\/:*?"<>|]', '', ime)
    ime = ime.strip().replace(' ', '_')
    return ime[:80]


def obradi_fajl(putanja):
    rel = putanja.relative_to(RAW_DIR)
    kategorija = rel.parts[0]

    if je_sken(putanja):
        print(f"preskacem (sken, ceka OCR): {rel}")
        return

    naslov = putanja.stem

    tekst = izvuci_tekst(putanja)
    tekst = strukturiraj(tekst)
    tekst = normalizuj(tekst, naslov=naslov)

    tabele = izvuci_prave_tabele(putanja)
    if tabele:
        tekst += "\n\n## Tabele\n\n"
        for tabela in tabele:
            tekst += tabela_u_markdown(tabela) + "\n\n"

    slug = slugify(naslov)
    izlazni_folder = PROCESSED_DIR / kategorija / slug
    izlazni_folder.mkdir(parents=True, exist_ok=True)

    (izlazni_folder / "document.md").write_text(f"# {naslov}\n\n{tekst}", encoding="utf-8")

    metadata = {
        "title": naslov,
        "category": kategorija,
        "source_type": "pdf",
        "original_file": str(rel),
        "ima_tabele": len(tabele) > 0,
    }
    (izlazni_folder / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"obradjeno: {rel} -> {izlazni_folder.relative_to(PROCESSED_DIR)}")


def main():
    pdfovi = sorted(RAW_DIR.rglob("*.pdf"))
    for putanja in pdfovi:
        try:
            obradi_fajl(putanja)
        except Exception as e:
            print(f"greska na {putanja.relative_to(RAW_DIR)}: {e}")


if __name__ == "__main__":
    main()
