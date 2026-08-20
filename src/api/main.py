import sys
from contextlib import asynccontextmanager
from pathlib import Path

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm.rag import odgovori, odgovori_u_dijelovima
from retrieval.pretraga import pretrazi
from evidencija import zabiljezi_upit, zabiljezi_feedback


@asynccontextmanager
async def lifespan(app: FastAPI):
    pretrazi("test", n_results=1)
    yield


app = FastAPI(title="FAQ Chatbot - Studentska služba ETF", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RanijaPoruka(BaseModel):
    uloga: str = Field(..., pattern="^(korisnik|bot)$")
    tekst: str


class PitanjeZahtev(BaseModel):
    pitanje: str = Field(..., min_length=3, description="Pitanje studenta")
    istorija: list[RanijaPoruka] = Field(
        default_factory=list, description="Prethodne poruke u razgovoru"
    )


class IzvorInfo(BaseModel):
    naslov_dokumenta: str
    sekcija: str


class OdgovorOdgovor(BaseModel):
    odgovor: str
    izvori: list[IzvorInfo]


class FeedbackZahtev(BaseModel):
    pitanje: str = Field(..., min_length=1)
    odgovor: str = Field(..., min_length=1)
    koristan: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=OdgovorOdgovor)
def ask(zahtev: PitanjeZahtev):
    try:
        odgovor, chunkovi = odgovori(
            zahtev.pitanje,
            istorija=[p.model_dump() for p in zahtev.istorija],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška pri generisanju odgovora: {e}")

    izvori = [
        IzvorInfo(
            naslov_dokumenta=c["metadata"]["naslov_dokumenta"],
            sekcija=c["metadata"]["sekcija"],
        )
        for c in chunkovi
    ]

    zabiljezi_upit(
        zahtev.pitanje,
        odgovor,
        [f"{i.naslov_dokumenta} / {i.sekcija}".strip(" /") for i in izvori],
    )

    return OdgovorOdgovor(odgovor=odgovor, izvori=izvori)


@app.post("/ask/stream")
def ask_stream(zahtev: PitanjeZahtev):
    def dogadjaji():
        izvori = []
        djelovi = []
        try:
            for stavka in odgovori_u_dijelovima(
                zahtev.pitanje,
                istorija=[p.model_dump() for p in zahtev.istorija],
            ):
                if stavka["vrsta"] == "izvori":
                    izvori = [
                        {
                            "naslov_dokumenta": c["metadata"]["naslov_dokumenta"],
                            "sekcija": c["metadata"]["sekcija"],
                        }
                        for c in stavka["chunkovi"]
                    ]
                    yield _sse({"vrsta": "izvori", "izvori": izvori})
                else:
                    djelovi.append(stavka["tekst"])
                    yield _sse({"vrsta": "tekst", "tekst": stavka["tekst"]})
        except Exception as e:
            yield _sse({"vrsta": "greska", "poruka": str(e)})
            return

        odgovor = "".join(djelovi)
        zabiljezi_upit(
            zahtev.pitanje,
            odgovor,
            [f"{i['naslov_dokumenta']} / {i['sekcija']}".strip(" /") for i in izvori],
        )
        yield _sse({"vrsta": "kraj"})

    return StreamingResponse(
        dogadjaji(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(podaci):
    return f"data: {json.dumps(podaci, ensure_ascii=False)}\n\n"


@app.post("/feedback")
def feedback(zahtev: FeedbackZahtev):
    zabiljezi_feedback(zahtev.pitanje, zahtev.odgovor, zahtev.koristan)
    return {"status": "zabilježeno"}
