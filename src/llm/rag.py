import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from retrieval.pretraga import pretrazi

load_dotenv()

klijent = Groq(api_key=os.getenv("GROQ_API_KEY"))

SISTEM_PROMPT = """Ti si asistent studentske službe Elektrotehničkog fakulteta u Beogradu.

Odgovaraj isključivo na osnovu konteksta koji ti je dat ispod. Ne izmišljaj informacije
koje nisu u kontekstu, čak i ako misliš da ih znaš iz opšteg znanja.

Ako se odgovor na pitanje ne nalazi u priloženom kontekstu, jasno reci da ne znaš
odgovor i posavjetuj studenta da se obrati studentskoj službi ili pogleda zvaničnu
stranicu fakulteta. Nemoj pogađati ni davati približne odgovore.

Posebno strogo pravilo za konkretne podatke: nazive (smjerova, modula, predmeta,
organa), brojeve, iznose, rokove i datume smiješ navesti SAMO ako se doslovno nalaze
u kontekstu. Nikada ih ne dopunjuj iz svog opšteg znanja, čak ni ako ti djeluju
poznato ili logično.

Ako kontekst sadrži samo dio nekog spiska, navedi samo ono što zaista piše i izričito
napomeni da spisak možda nije potpun. Nikada nemoj sam produžavati nabrajanje.

Vrlo važno: ako podatak u kontekstu važi samo pod nekim uslovom — na primjer samo za
studente upisane prije određene godine, samo za određeni studijski program ili smjer,
ili se radi o starom nazivu koji je zamijenjen novim — OBAVEZNO navedi taj uslov uz
podatak. Nikada ne prenosi takav podatak kao da važi za sve.

Odgovaraj kratko i jasno, na srpskom jeziku. Odgovor napiši istim pismom kojim je
postavljeno pitanje — ako je pitanje na latinici, odgovori latinicom; ako je na
ćirilici, odgovori ćirilicom. Pismo kojim su napisani dokumenti u kontekstu ne utiče
na to.

Cijeli odgovor mora biti u jednom pismu, uključujući i dijelove koje prepisuješ iz
dokumenata. Ako citiraš ili prepričavaš tekst napisan drugim pismom, preslovi ga —
nikada ne miješaj latinicu i ćirilicu u istom odgovoru."""


def izgradi_kontekst(chunkovi):
    dijelovi = []
    for c in chunkovi:
        izvor = c["metadata"]["naslov_dokumenta"]
        if c["metadata"]["sekcija"]:
            izvor += f", {c['metadata']['sekcija']}"
        dijelovi.append(f"[Izvor: {izvor}]\n{c['tekst']}")
    return "\n\n---\n\n".join(dijelovi)


def odgovori(pitanje, n_results=6):
    chunkovi = pretrazi(pitanje, n_results=n_results)
    kontekst = izgradi_kontekst(chunkovi)

    poruke = [
        {"role": "system", "content": SISTEM_PROMPT},
        {"role": "user", "content": f"Kontekst:\n{kontekst}\n\nPitanje: {pitanje}"},
    ]

    odgovor = klijent.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=poruke,
        temperature=0.2,
    )

    return odgovor.choices[0].message.content, chunkovi
