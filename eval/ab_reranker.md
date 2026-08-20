# A/B poređenje: pretraga sa rerankerom i bez njega

Mjereno bez poziva LLM-a — provjerava se samo da li je među prvih 10 vraćenih izvora bio dokument za koji je unaprijed određeno da
sadrži odgovor. Zbog toga mjerenje ne troši Groq kvotu i ponovljivo je.

Uzorak: **29 pitanja** (od ukupno 37; pitanja van domena nemaju
očekivani izvor pa nisu uključena).

## Rezultat

| | Pronađen izvor | Prosječno vrijeme |
|---|---:|---:|
| Bez rerankera | 29/29 (100%) | 0.04s |
| Sa rerankerom | 29/29 (100%) | 3.54s |

Razlika: **+0 pitanja**, uz **+3.50s** po upitu.

## Pitanja koja reranker dobija

Nema.

## Pitanja koja reranker gubi

Nema — reranker ne kvari nijedno pitanje koje je i prije radilo.

## Po pitanju

| ID | Kategorija | Bez | Sa | |
|---|---|:-:|:-:|---|
| A1 | A | da | da |  |
| A2 | A | da | da |  |
| A3 | A | da | da |  |
| A4 | A | da | da |  |
| A5 | A | da | da |  |
| A6 | A | da | da |  |
| A7 | A | da | da |  |
| A8 | A | da | da |  |
| A9 | A | da | da |  |
| A10 | A | da | da |  |
| A11 | A | da | da |  |
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
| D4 | D | da | da |  |
| E1a | E | da | da |  |
| E1b | E | da | da |  |
| E1c | E | da | da |  |
| E1d | E | da | da |  |
| E2a | E | da | da |  |
| E2b | E | da | da |  |
| F3 | F | da | da |  |
