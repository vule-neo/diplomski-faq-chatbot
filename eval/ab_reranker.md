# A/B poređenje: pretraga sa rerankerom i bez njega

Mjereno bez poziva LLM-a — provjerava se samo da li je među prvih 6 vraćenih izvora bio dokument za koji je unaprijed određeno da
sadrži odgovor. Zbog toga mjerenje ne troši Groq kvotu i ponovljivo je.

Uzorak: **29 pitanja** (od ukupno 37; pitanja van domena nemaju
očekivani izvor pa nisu uključena).

## Rezultat

| | Pronađen izvor | Prosječno vrijeme |
|---|---:|---:|
| Bez rerankera | 26/29 (90%) | 0.05s |
| Sa rerankerom | 29/29 (100%) | 4.83s |

Razlika: **+3 pitanja**, uz **+4.78s** po upitu.

## Pitanja koja reranker dobija

- **A1** (A) — Koliko bodova treba za budžet?
- **A11** (A) — Koliko je radno vrijeme studentskog odseka?
- **D4** (D) — Koliko puta mogu da ponavljam godinu?

## Pitanja koja reranker gubi

Nema — reranker ne kvari nijedno pitanje koje je i prije radilo.

## Po pitanju

| ID | Kategorija | Bez | Sa | |
|---|---|:-:|:-:|---|
| A1 | A | ne | da | dobija |
| A2 | A | da | da |  |
| A3 | A | da | da |  |
| A4 | A | da | da |  |
| A5 | A | da | da |  |
| A6 | A | da | da |  |
| A7 | A | da | da |  |
| A8 | A | da | da |  |
| A9 | A | da | da |  |
| A10 | A | da | da |  |
| A11 | A | ne | da | dobija |
| A12 | A | da | da |  |
| B1 | B | da | da |  |
| B2 | B | da | da |  |
| B3 | B | da | da |  |
| B4 | B | da | da |  |
| B5 | B | da | da |  |
| B6 | B | da | da |  |
| D1 | D | da | da |  |
| D2 | D | da | da |  |
| D3 | D | da | da |  |
| D4 | D | ne | da | dobija |
| E1a | E | da | da |  |
| E1b | E | da | da |  |
| E1c | E | da | da |  |
| E1d | E | da | da |  |
| E2a | E | da | da |  |
| E2b | E | da | da |  |
| F3 | F | da | da |  |
