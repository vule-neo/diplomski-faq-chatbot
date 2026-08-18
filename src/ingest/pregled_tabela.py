import sys
import pdfplumber
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"


MAX_PROSJECNA_DUZINA_CELIJE = 50


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


def main():
    if len(sys.argv) < 2:
        print("upotreba: python pregled_tabela.py <dio_imena_fajla>")
        return

    trazeno = sys.argv[1].lower()
    kandidati = [p for p in RAW_DIR.rglob("*.pdf") if trazeno in p.name.lower()]

    if not kandidati:
        print(f"nisam nasao fajl koji sadrzi '{trazeno}'")
        return

    putanja = kandidati[0]
    print(f"fajl: {putanja.relative_to(RAW_DIR)}\n")

    with pdfplumber.open(putanja) as pdf:
        redni_broj = 0
        odbaceno = 0
        for broj_strane, strana in enumerate(pdf.pages, start=1):
            tabele = strana.extract_tables()
            for tabela in tabele:
                if not je_prava_tabela(tabela):
                    odbaceno += 1
                    continue
                redni_broj += 1
                print(f"--- tabela {redni_broj} (strana {broj_strane}) ---")
                print(tabela_u_markdown(tabela))
                print()

        print(f"zadrzano: {redni_broj}, odbaceno kao sumnjivo: {odbaceno}")


if __name__ == "__main__":
    main()
