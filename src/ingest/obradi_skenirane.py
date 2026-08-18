import io
import sys
import json
import fitz
import pytesseract
from PIL import Image

from obradi_dokumente import RAW_DIR, PROCESSED_DIR, je_sken, strukturiraj, normalizuj, slugify

sys.stdout.reconfigure(encoding="utf-8")

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
JEZIK = "srp"
ZOOM = 2


def ocr_stranica(strana):
    matrica = fitz.Matrix(ZOOM, ZOOM)
    pix = strana.get_pixmap(matrix=matrica)
    slika = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(slika, lang=JEZIK)


def ocr_dokument(putanja):
    doc = fitz.open(putanja)
    strane = []
    for i, strana in enumerate(doc, start=1):
        print(f"  OCR strana {i}/{doc.page_count}...")
        strane.append(ocr_stranica(strana))
    doc.close()
    return "\n\n".join(strane)


def obradi_skenirani_fajl(putanja):
    rel = putanja.relative_to(RAW_DIR)
    kategorija = rel.parts[0]

    naslov = putanja.stem

    print(f"OCR: {rel}")
    tekst = ocr_dokument(putanja)
    tekst = strukturiraj(tekst)
    tekst = normalizuj(tekst, naslov=naslov)

    slug = slugify(naslov)
    izlazni_folder = PROCESSED_DIR / kategorija / slug
    izlazni_folder.mkdir(parents=True, exist_ok=True)

    (izlazni_folder / "document.md").write_text(f"# {naslov}\n\n{tekst}", encoding="utf-8")

    metadata = {
        "title": naslov,
        "category": kategorija,
        "source_type": "pdf",
        "original_file": str(rel),
        "ima_tabele": False,
        "ocr": True,
    }
    (izlazni_folder / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"obradjeno (OCR): {rel} -> {izlazni_folder.relative_to(PROCESSED_DIR)}")


def main():
    pdfovi = sorted(RAW_DIR.rglob("*.pdf"))
    skenirani = [p for p in pdfovi if je_sken(p)]

    print(f"Pronadjeno {len(skenirani)} skeniranih fajlova za OCR\n")

    for putanja in skenirani:
        try:
            obradi_skenirani_fajl(putanja)
        except Exception as e:
            print(f"greska na {putanja.relative_to(RAW_DIR)}: {e}")


if __name__ == "__main__":
    main()
