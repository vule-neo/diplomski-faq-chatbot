# Metrike evaluacije

Ukupno pitanja: **37**. Ocjene su unesene ručno u `rezultati.md`,
poređenjem svakog odgovora sa izvornim dokumentom.

## Ukupan rezultat

| Ocjena | Značenje | Broj | Udio |
|---|---|---:|---:|
| T | tačno | 31 | 84% |
| D | djelimično | 4 | 11% |
| N | netačno | 2 | 5% |

**Tačnost: 31/37 (84%)**

## Rezultat po kategorijama

| Kategorija | Opis | T | D | N | Ukupno | Tačnost |
|---|---|---:|---:|---:|---:|---:|
| A | Osnovna pitanja u domenu | 10 | 1 | 1 | 12 | 83% |
| B | Pitanja koja zahtijevaju uslov važenja | 5 | 1 | 0 | 6 | 83% |
| C | Pitanja van domena (očekuje se odbijanje) | 6 | 0 | 0 | 6 | 100% |
| D | Djelimično pokrivena pitanja | 1 | 2 | 1 | 4 | 25% |
| E | Robusnost na formulaciju | 6 | 0 | 0 | 6 | 100% |
| F | Otpornost na prompt injection | 3 | 0 | 0 | 3 | 100% |

## Pretraga (retrieval)

Mjereno automatski: da li je među vraćenim izvorima bio dokument za koji je
unaprijed određeno da sadrži odgovor. Računato samo za pitanja kod kojih takav
dokument postoji (pitanja van domena nemaju očekivani izvor).

- Pitanja sa definisanim očekivanim izvorom: **29**
- Očekivani izvor pronađen: **28** (**97%**)

Promašeni izvor: A1

## Netačni odgovori

- **A11**: LAZNO ODBIJANJE. Rekao da ne zna, a podatak postoji: 'Radno vreme saltera je od 11-13h' (Pitanja i odgovori Q&A). Greska pretrage, ne generisanja.
- **D2**: LAZNO ODBIJANJE. Podatak POSTOJI: Pravilnik o disciplinskoj odgovornosti, Clan 9 (koriscenje nedozvoljenih sredstava na ispitu = teza povreda) i Clan 10 (mjere: zabrana polaganja ispita, privremeno udaljavanje, iskljucenje sa studija). Retrieval je dovukao pravi dokument ali pogresne clanove (18, 20, 35 - procedura umjesto prekrsaja i mjera).
