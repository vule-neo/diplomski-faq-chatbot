import fitz
import pdfplumber
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
SKEN_PRAG = 50  # ispod ovoliko karaktera po strani u prosjeku, sumnjamo da je sken


def prosjek_karaktera_po_strani(putanja):
    doc = fitz.open(putanja)
    ukupno = 0
    for strana in doc:
        ukupno += len(strana.get_text())
    broj_strana = doc.page_count
    doc.close()
    if broj_strana == 0:
        return 0
    return ukupno / broj_strana


def broj_tabela(putanja):
    ukupno = 0
    with pdfplumber.open(putanja) as pdf:
        for strana in pdf.pages:
            ukupno += len(strana.extract_tables())
    return ukupno


def main():
    pdfovi = sorted(RAW_DIR.rglob("*.pdf"))
    print(f"Pronadjeno {len(pdfovi)} PDF fajlova u {RAW_DIR}\n")

    sumnjivi_na_sken = []
    sa_tabelama = []

    for putanja in pdfovi:
        rel_putanja = putanja.relative_to(RAW_DIR)
        try:
            prosjek = prosjek_karaktera_po_strani(putanja)
        except Exception as e:
            print(f"{rel_putanja} -> GRESKA pri citanju ({e})")
            continue

        if prosjek < SKEN_PRAG:
            status = "SUMNJIVO NA SKEN"
            sumnjivi_na_sken.append(rel_putanja)
        else:
            status = "OK"

        tabele = broj_tabela(putanja)
        if tabele > 0:
            sa_tabelama.append(rel_putanja)

        napomena = f", {tabele} tabela detektovano" if tabele > 0 else ""
        print(f"{rel_putanja} -> {status} ({prosjek:.0f} karaktera/strana{napomena})")

    print("\n--- rezime ---")
    print(f"Sumnjivo na sken ({len(sumnjivi_na_sken)}):")
    for p in sumnjivi_na_sken:
        print(f"  - {p}")
    print(f"\nSa tabelama ({len(sa_tabelama)}):")
    for p in sa_tabelama:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
