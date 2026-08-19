# Kritička analiza sistema

Analiza rađena nakon završene evaluacije, sa ciljem da se utvrdi šta nedostaje da bi
sistem bio stvarno upotrebljiv u studentskoj službi, a ne samo tačan na test pitanjima.
Sve tvrdnje ispod su izmjerene na trenutnom stanju korpusa, ne procijenjene.

---

## Glavni zaključak

Sistem je **tačan, ali ne i koristan**. Tačnost od 84% na test pitanjima ne znači mnogo
ako pitanja koja studenti stvarno postavljaju uopšte nisu pokrivena dokumentima. Ovo
nije problem RAG arhitekture, prompta ni chunkinga — **primarno je problem sadržaja
baze znanja.**

---

## 1. Baza znanja je pravnički, a ne studentski orijentisana

Izmjereno na 1063 chunka:

| Dokument | Udio |
|---|---|
| Zakon o visokom obrazovanju | **23.8%** |
| Statut ETF-a | **22.1%** |
| Pravilnik o OAS | 9.1% |
| Pravilnik o doktorskim studijama | 9.0% |
| Pravilnik o master studijama | 8.8% |
| ... | |
| **Pitanja i odgovori (Q&A)** | **2.2%** |

**Zakon i Statut čine 46% baze.** To su dokumenti koji uređuju rad ustanove — biranje
dekana, nadležnosti Savjeta, akreditacija. Student ih gotovo nikad ne treba.

Istovremeno, u testu na 8 realnih studentskih pitanja, dokument `Pitanja i odgovori
(Q&A)` — koji čini svega **2.2% baze** — pojavio se u **15 od 48** dovučenih mjesta.
Dakle najkorisniji dokument je najmanji, a najveći su najmanje korisni.

**Posljedica:** pretraga stalno vuče pravne odredbe umjesto praktičnog odgovora, a one
zauzimaju mjesta u kontekstu koja bi trebalo da pripadnu konkretnoj informaciji.

## 2. Nedostaju dokumenti koje studenti zaista traže

U bazi **ne postoji ništa** o:

- rasporedu časova, terminima konsultacija, kalendaru nastave (kad počinje semestar,
  kad su praznici, kad je kolokvijumska nedjelja)
- spisku predmeta po godinama i modulima, silabusima, broju ESPB po predmetu
- nastavnicima (ko predaje šta, kontakt, kabinet)
- kontaktima službi (mejl, telefon, ko je zadužen za šta)
- studentskom domu, menzi, stipendijama, studentskim organizacijama
- praktičnim procedurama koje nisu u pravilniku (kako se piše molba, gdje se predaje,
  koliko traje obrada)

Test na 8 realnih pitanja ("Kad su konsultacije?", "Kad počinje semestar?", "Koji
predmeti se slušaju na prvoj godini?", "Kako da dobijem uverenje o statusu?") —
za većinu njih **odgovor ne postoji u bazi**, pa ma koliko dobra pretraga bila, sistem
ne može pomoći.

**Ovo je najveća pojedinačna rupa.** Bez ovih podataka sistem ostaje "pretraživač
pravilnika", a ne asistent studentske službe.

## 3. Izmjene dokumenata nisu povezane sa dokumentima koje mijenjaju

U bazi postoje istovremeno:
- `Statut_ETFa_2018` i `Izmena statuta` (2019)
- `Pravilnik_o_OAS_preciscen_jun_2023`, `Izmena_Pravilnika_o_OAS-2024`,
  `Izmena Pravilnika o osnovnim akademskim studijama-2025`

Izmjene su zasebni dokumenti u stilu *"u članu 41. riječi 'jednu školsku godinu'
zamjenjuju se riječima 'dvije školske godine'"*. Sistem nema nikakvu vezu između
izmjene i člana koji se mijenja.

Provjereno: na pitanje o mandatu prodekana pretraga vraća `Statut, Član 41` **ali ne i
izmjenu koja taj član mijenja**. Znači sistem može mirno servirati **ukinuti tekst kao
važeći**, bez ikakvog upozorenja.

Kod pitanja o mentoru završnog rada je slučajno vratio i osnovni član i izmjenu — ali
to je stvar sreće u rangiranju, ne mehanizma.

**Ovo je najozbiljniji rizik po tačnost** i jedini nalaz iz ove analize koji bi u
stvarnoj upotrebi mogao da naškodi studentu (npr. da propusti rok jer mu je servirana
stara odredba).

## 4. Smeće u indeksu

Od 1063 chunka:
- **59** su sadržaj dokumenta (redovi tipa `ЗАСТУПАЊЕ И ПРЕДСТАВЉАЊЕ ФАКУЛТЕТА .....`),
  navigacija sa sajta, ili skoro sami brojevi
- **33** su kraći od 160 znakova (često bez upotrebljivog sadržaja)

Ovi chunkovi nikad ne mogu odgovoriti ni na jedno pitanje, ali troše mjesto u indeksu i
povremeno se probiju u rezultate.

## 5. Duplikati u kontekstu — provjereno, NIJE problem

*(Ova tačka je prvobitno bila navedena kao ozbiljan nedostatak, pa opovrgnuta
provjerom. Ostavljena je jer ilustruje kako lako pogrešno postavljena metrika navede
na pogrešan zaključak.)*

Prvo mjerenje je pokazalo da se od 6 chunkova poslatih modelu ponavlja isti izvor — na
primjer "3/6 jedinstvenih" za pitanje o rokovima. Zaključak je bio da polovina konteksta
odlazi na duplikate.

**Taj zaključak je bio netačan.** Mjereno je po paru *(naziv dokumenta, sekcija)*, a
većina dokumenata koji nisu pravilnici (web-stranice, Q&A) uopšte nema sekcije — pa su
različiti chunkovi iz istog dokumenta izgledali kao isti unos.

Provjerom po stvarnom tekstu: **6/6 chunkova je jedinstveno** u oba testirana slučaja.
Duplikata praktično nema.

Jedino stvarno zapažanje je blaga *međudokumentna* sličnost — isti sadržaj se ponavlja
u Pravilniku o OAS i Pravilniku o master studijama (npr. odredba o ispitnim rokovima
skoro identična u oba). To povremeno zauzme dva mjesta umjesto jednog, ali nije
ozbiljno i ne zahtijeva intervenciju.

## 6. Retrieval nema drugi krug provjere

Trenutno: hibridna pretraga (embedding + BM25) → RRF spajanje → prvih 6 ide modelu.
Nema koraka koji bi ocijenio *da li dovučeni chunk zaista odgovara na pitanje*.

Posljedica su izmjerena lažna odbijanja:
- **A11** — "radno vrijeme studentskog odseka": podatak postoji u Q&A, nije dovučen
- **D2** — "disciplinska mjera za prepisivanje": dovučen pravi dokument, ali pogrešni
  članovi (procedura žalbi umjesto spiska prekršaja i kazni)
- "koliko košta školarina": relevantan chunk tek na **38. mjestu**

Zajednički obrazac: kod uopštenih pitanja česta riječ (npr. "školarina") se pojavljuje
u desetinama chunkova, pa konkretan podatak ne dolazi do vrha.

## 7. Metapodaci se ne koriste

Svaki chunk nosi `kategorija` (pravilnik, upis, web-stranice...), ali se ta informacija
**nigdje ne koristi** — ni za filtriranje, ni za rangiranje. Pitanje o upisu jednako
pretražuje Zakon o visokom obrazovanju kao i dokumente o upisu.

Nema ni podatka o **godini/važenju** dokumenta, pa se stariji i noviji tretiraju
identično (vidi tačku 3).

## 8. Šta sistem ne može, a korisnik očekuje

- **ne zna današnji datum** — na "kad je sledeći ispitni rok" ne može reći koji je
  sledeći, samo nabraja sve
- **ne razlikuje kome se obraća** — brucoš i student master studija dobijaju isti
  odgovor, iako pravila nisu ista
- **ne nudi sledeći korak** — kaže "obratite se studentskoj službi", ali nema ni mejl
  ni radno vrijeme ni link
- **nema poznat obim** — korisnik ne zna šta sistem uopšte pokriva, pa očekuje previše
- **odgovori su predugi** — često nabraja i ono što nije traženo

---

## Šta uraditi, po prioritetu

### Prioritet 1 — sadržaj (najveći efekat, najmanje tehnički rad)

1. **Dodati praktične dokumente**: akademski kalendar, raspored ispitnih rokova,
   kontakt i radno vrijeme službi, spisak predmeta po godinama, informacije o
   domu/menzi/stipendijama. Ovo je razgovor sa studentskom službom, ne programiranje.
2. **Proširiti Q&A dokument.** On je najkorisniji dio baze, a najmanji. Svako pitanje
   dodato u njega direktno popravlja kvalitet.
3. **Izbaciti ili razgraničiti Zakon i Statut.** Ne brisati ih, ali ih ne tretirati
   ravnopravno sa dokumentima koji se tiču studenata.

### Prioritet 2 — tačnost

4. **Riješiti izmjene dokumenata.** Minimalno: u `metadata.json` dodati polje o tome
   koji dokument je izmijenjen i kada, pa u prompt ubaciti upozorenje kad se u
   kontekstu nađe član koji je kasnije mijenjan. Bolje: ručno ugraditi izmjene u
   prečišćeni tekst.
5. **Očistiti smeće** (59 chunkova sadržaja/navigacije) i **ukloniti duplikate prije
   slanja modelu**, ne samo pri prikazu.

### Prioritet 3 — pretraga

6. **Rerank** dovučenih kandidata (uzeti 20-30 pa ih prerangirati prema pitanju).
   Ovo direktno cilja A11, D2 i slučaj sa školarinom.
7. **Koristiti kategoriju** kao signal pri rangiranju.

### Prioritet 4 — doživljaj korišćenja

8. Kraći odgovori, jasno rečen obim sistema na početku, konkretan sledeći korak
   (mejl/link/radno vrijeme) umjesto opšteg upućivanja, svijest o datumu.

---

## Napomena o obimu

Za diplomski rad sistem u trenutnom stanju **jeste dovoljan** — pokazuje RAG
arhitekturu, mjerenu evaluaciju i ozbiljnu analizu ograničenja. Sve gore navedeno
spada u "šta bi trebalo za produkciju", i kao takvo je vrijedan sadržaj poglavlja o
daljem radu.

Za stvarno uvođenje u studentsku službu, **Prioritet 1 i tačka 4 su neophodni** —
ostalo je poboljšanje kvaliteta, a to dvoje su uslov da sistem ne bude beskoristan
odnosno da ne obmane studenta.
