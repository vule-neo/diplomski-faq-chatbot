import json
import re
from datetime import datetime
from pathlib import Path
from threading import Lock

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
UPITI_PUTANJA = DATA_DIR / "upiti.jsonl"
FEEDBACK_PUTANJA = DATA_DIR / "feedback.jsonl"

# vise zahtjeva moze stici istovremeno, a upisujemo u isti fajl
_brava = Lock()

# frazama kojima model odbija da odgovori - koristi se da se upit oznaci kao
# "nepoznat", pa se kasnije iz loga vidi koje teme fale u bazi znanja
FRAZE_ODBIJANJA = re.compile(
    r"ne znam|не знам|nemam informacij|немам информациј|"
    r"nije naveden|није наведен|ne postoji informacij|не постоји информациј|"
    r"nema informacij|нема информациј",
    re.IGNORECASE,
)


def je_odbijanje(odgovor):
    return bool(FRAZE_ODBIJANJA.search(odgovor))


def _upisi(putanja, zapis):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _brava:
        with open(putanja, "a", encoding="utf-8") as f:
            f.write(json.dumps(zapis, ensure_ascii=False) + "\n")


def zabiljezi_upit(pitanje, odgovor, izvori):
    _upisi(UPITI_PUTANJA, {
        "vrijeme": datetime.now().isoformat(timespec="seconds"),
        "pitanje": pitanje,
        "odgovor": odgovor,
        "izvori": izvori,
        "odbijeno": je_odbijanje(odgovor),
    })


def zabiljezi_feedback(pitanje, odgovor, koristan):
    _upisi(FEEDBACK_PUTANJA, {
        "vrijeme": datetime.now().isoformat(timespec="seconds"),
        "pitanje": pitanje,
        "odgovor": odgovor,
        "koristan": koristan,
    })
