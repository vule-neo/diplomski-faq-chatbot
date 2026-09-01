# Izvori baze znanja

Spisak dokumenata koji čine bazu znanja sistema. Kolone **Izvor** i **Datum preuzimanja**
popunjavaju se ručno, jer se odakle je koji dokument preuzet i kada ne može utvrditi iz
samog fajla.

Kolona **Obrada** označava kako je dokument obrađen:

- `tekst`: PDF sadrži pravi tekstualni sloj, izvučen direktno
- `OCR`: skenirani dokument, tekst dobijen optičkim prepoznavanjem (Tesseract, srpski)
- `ručno`: podaci prekucani iz originala, jer se iz PDF-a gubi veza red-kolona

Ukupno: **34 dokumenta**, od toga 25 tekstualnih, 4 skenirana i 5 prekucanih.

## Akti

| Naziv dokumenta | Obrada | Izvor | Datum preuzimanja | Napomena |
|---|---|---|---|---|
| Statut ETF-a (2018) | tekst | | | osnovni akt fakulteta |
| Izmena statuta | OCR | | | skeniran, izmjene iz 2019. |

## Pravilnici

| Naziv dokumenta | Obrada | Izvor | Datum preuzimanja | Napomena |
|---|---|---|---|---|
| Pravilnik o OAS (prečišćen, jun 2023) | tekst | | | glavni pravilnik za osnovne studije |
| Izmena Pravilnika o OAS (2024) | OCR | | | skeniran, dodat član o komisijskom polaganju |
| Izmena Pravilnika o OAS (2025) | OCR | | | skeniran, sadrži formulu koju OCR nije prepoznao |
| Pravilnik o master akademskim studijama | tekst | | | |
| Pravilnik o doktorskim studijama | tekst | | | |
| Pravilnik o upisu studenata | OCR | | | skeniran, 18 strana |
| Pravilnik o disciplinskoj odgovornosti studenata (2016) | tekst | | | |
| Pravilnik o korišćenju Računskog centra | tekst | | | |

## Zakoni

| Naziv dokumenta | Obrada | Izvor | Datum preuzimanja | Napomena |
|---|---|---|---|---|
| Zakon o visokom obrazovanju | tekst | | | |

## Upis i prijemni ispit

| Naziv dokumenta | Obrada | Izvor | Datum preuzimanja | Napomena |
|---|---|---|---|---|
| Upis korak po korak (2026) | tekst | | | |
| Uslovi upisa (prijemni ETF) | tekst | | | sadrži iznose školarine |
| Upis na Elektrotehnički fakultet | tekst | | | sadrži broj žiro računa |
| Prijavljivanje kandidata | tekst | | | |
| Način bodovanja na prijemnom ispitu | tekst | | | |
| Pravila o održavanju prijemnog ispita | tekst | | | |
| Ko može biti oslobođen polaganja prijemnog ispita | tekst | | | |
| Formiranje rang lista | tekst | | | |
| Primedbe i žalbe | tekst | | | |

## Stranice sa sajta fakulteta

| Naziv dokumenta | Obrada | Izvor | Datum preuzimanja | Napomena |
|---|---|---|---|---|
| Cenovnik | tekst | | | cijene usluga, u tabelama |
| Žiro račun | tekst | | | broj računa i pozivi na broj |
| Rokovi za prijavu ispita | tekst | | | |
| Studentski odsek | tekst | | | |
| Osnovne akademske studije | tekst | | | spisak modula i smjerova |
| Upis na osnovne akademske studije | tekst | | | |
| Kako napisati diplomski rad (PPK) | tekst | | | uputstvo za pisanje rada |

## Praktični podaci

| Naziv dokumenta | Obrada | Izvor | Datum preuzimanja | Napomena |
|---|---|---|---|---|
| Kalendar nastave 2025/26 | ručno | | | original je grafička tabela datuma |
| Studentski odsek, kontakti | ručno | | | radno vrijeme šaltera i telefona |
| Kontakti službi fakulteta | ručno | | | dekanat, računovodstvo, opšti odsek |
| Nastavnici Katedre za RTI | ručno | | | 40 osoba sa zvanjem, mejlom i telefonom |
| Predmeti, Računarska tehnika i informatika | ručno | | | predmeti po semestrima sa ESPB |

## Ostalo

| Naziv dokumenta | Obrada | Izvor | Datum preuzimanja | Napomena |
|---|---|---|---|---|
| Pitanja i odgovori (Q&A), eStudent | tekst | | | najčešća pitanja studenata |
| Stručna praksa (SI Wiki) | tekst | | | |

## Napomena o načinu preuzimanja

Dokumenti iz kategorija *Upis i prijemni ispit* i *Stranice sa sajta fakulteta* su
sačuvani štampanjem web stranice u PDF (Ctrl+P, Save as PDF). Zbog toga sadrže i
zaglavlja/podnožja koje browser dodaje (datum, URL, broj strane), pa se ti redovi
uklanjaju u koraku normalizacije prilikom obrade.

Dokumenti iz kategorije *Praktični podaci* su prekucani ručno. Originalni PDF-ovi su
zadržani u `data/raw/dopuna/` sa ekstenzijom `.bak`, da postoji trag odakle podaci
potiču, a da ih pipeline ne obrađuje duplo.
