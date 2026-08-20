import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { marked } from 'marked';

import { ChatPoruka, IzvorInfo, RanijaPoruka } from './models/chat.model';
import { ChatService } from './services/chat.service';

const PREDLOZENA_PITANJA = [
  'Koji su rokovi za prijavu ispita?',
  'Koliko ESPB treba za upis naredne godine?',
  'Koliko bodova je potrebno za budžet?',
  'Koliko traje stručna praksa?',
];

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly predlozi = PREDLOZENA_PITANJA;

  protected readonly pitanje = signal('');
  protected readonly poruke = signal<ChatPoruka[]>([]);
  protected readonly ucitavanje = signal(false);
  protected readonly greska = signal<string | null>(null);

  private bafer = '';
  private tajmerIspisa: ReturnType<typeof setInterval> | null = null;

  constructor(private chatService: ChatService) {}

  // model odgovara u markdownu (**podebljano**, liste, naslovi), pa se to
  // pretvara u HTML - Angular sam sanitizuje sadrzaj pri [innerHTML]
  uHtml(tekst: string): string {
    return marked.parse(tekst ?? '', { async: false }) as string;
  }

  naTipku(dogadjaj: KeyboardEvent): void {
    // Enter salje, Shift+Enter pravi novi red
    if (dogadjaj.key === 'Enter' && !dogadjaj.shiftKey) {
      dogadjaj.preventDefault();
      this.posaljiPitanje();
    }
  }

  prilagodiVisinu(dogadjaj: Event): void {
    const polje = dogadjaj.target as HTMLTextAreaElement;
    polje.style.height = 'auto';
    polje.style.height = `${Math.min(polje.scrollHeight, 140)}px`;
  }

  koristiPredlog(tekst: string): void {
    this.pitanje.set(tekst);
    this.posaljiPitanje();
  }

  posaljiPitanje(): void {
    const tekstPitanja = this.pitanje().trim();
    if (!tekstPitanja || this.ucitavanje()) {
      return;
    }

    // istorija se uzima prije nego se novo pitanje doda u listu
    const istorija: RanijaPoruka[] = this.poruke()
      .slice(-6)
      .map((p) => ({ uloga: p.tip, tekst: p.tekst }));

    this.poruke.update((trenutne) => [...trenutne, { tip: 'korisnik', tekst: tekstPitanja }]);
    this.pitanje.set('');
    this.ucitavanje.set(true);
    this.greska.set(null);

    this.primiOdgovor(tekstPitanja, istorija);
  }

  private async primiOdgovor(tekstPitanja: string, istorija: RanijaPoruka[]): Promise<void> {
    let indeks = -1;
    let izvori: IzvorInfo[] = [];

    try {
      for await (const dogadjaj of this.chatService.postaviPitanjeUDijelovima(
        tekstPitanja,
        istorija,
      )) {
        if (dogadjaj.vrsta === 'izvori') {
          // izvori stizu prije prvog slova odgovora - cuvaju se dok tekst ne krene,
          // da se ne pojavi prazan mjehur
          izvori = this.bezDuplikata(dogadjaj.izvori);
        } else if (dogadjaj.vrsta === 'tekst') {
          if (indeks < 0) {
            this.poruke.update((trenutne) => [
              ...trenutne,
              {
                tip: 'bot',
                tekst: '',
                prikazano: '',
                izvori,
                izvoriOtvoreni: false,
                pitanje: tekstPitanja,
              },
            ]);
            indeks = this.poruke().length - 1;
            this.ucitavanje.set(false);
          }
          this.dodajUBafer(indeks, dogadjaj.tekst);
        } else if (dogadjaj.vrsta === 'greska') {
          throw new Error(dogadjaj.poruka);
        }
      }
    } catch (e) {
      this.greska.set(this.objasniGresku(e));
    } finally {
      this.ucitavanje.set(false);
    }
  }

  private objasniGresku(e: unknown): string {
    const poruka = e instanceof Error ? e.message : String(e);

    if (poruka.includes('tokens per day') || poruka.includes('TPD')) {
      return 'Dostignuto je dnevno ograničenje besplatnog naloga za jezički model. Odgovori će ponovo raditi kada se ograničenje obnovi.';
    }
    if (poruka.includes('429') || poruka.toLowerCase().includes('rate limit')) {
      return 'Previše pitanja u kratkom roku. Sačekaj koji trenutak pa pokušaj ponovo.';
    }
    if (poruka.includes('Failed to fetch') || poruka.includes('NetworkError')) {
      return 'Nije moguće doći do servera. Provjeri da li backend radi, pa pokušaj ponovo.';
    }
    return 'Došlo je do greške pri dobijanju odgovora. Pokušaj ponovo.';
  }

  // Model salje tekst u naletima, pa bi se odgovor pojavljivao u skokovima.
  // Zato se prvo skuplja u bafer, a odatle isporucuje ravnomjerno.
  private dodajUBafer(indeks: number, tekst: string): void {
    this.bafer += tekst;
    if (this.tajmerIspisa !== null) {
      return;
    }

    this.tajmerIspisa = setInterval(() => {
      if (!this.bafer) {
        clearInterval(this.tajmerIspisa!);
        this.tajmerIspisa = null;
        return;
      }

      // sto vise zaostajemo, to brze ispisujemo - da odgovor ne kasni za modelom
      const korak = Math.max(2, Math.ceil(this.bafer.length / 10));
      const dio = this.bafer.slice(0, korak);
      this.bafer = this.bafer.slice(korak);

      this.izmijeniPoruku(indeks, (p) => ({
        ...p,
        tekst: p.tekst + dio,
        prikazano: p.tekst + dio,
      }));
    }, 25);
  }

  ocijeni(indeks: number, koristan: boolean): void {
    const poruka = this.poruke()[indeks];
    if (poruka.ocjena || !poruka.pitanje) {
      return;
    }

    // ocjenu prikazujemo odmah, ne cekamo odgovor servera - ako upis padne,
    // student svejedno nema sta da uradi povodom toga
    this.izmijeniPoruku(indeks, (p) => ({ ...p, ocjena: koristan ? 'koristan' : 'nekoristan' }));
    this.chatService.posaljiFeedback(poruka.pitanje, poruka.tekst, koristan).subscribe({
      error: () => {},
    });
  }

  prebaciIzvore(indeks: number): void {
    this.izmijeniPoruku(indeks, (p) => ({ ...p, izvoriOtvoreni: !p.izvoriOtvoreni }));
  }

  kopirajOdgovor(indeks: number): void {
    const poruka = this.poruke()[indeks];
    navigator.clipboard.writeText(poruka.tekst).then(() => {
      this.izmijeniPoruku(indeks, (p) => ({ ...p, kopirano: true }));
      setTimeout(() => this.izmijeniPoruku(indeks, (p) => ({ ...p, kopirano: false })), 1800);
    });
  }

  private bezDuplikata(izvori: IzvorInfo[]): IzvorInfo[] {
    const vidjeni = new Set<string>();
    return izvori.filter((i) => {
      const kljuc = `${i.naslov_dokumenta}|${i.sekcija}`;
      if (vidjeni.has(kljuc)) {
        return false;
      }
      vidjeni.add(kljuc);
      return true;
    });
  }

  private izmijeniPoruku(indeks: number, izmjena: (p: ChatPoruka) => ChatPoruka): void {
    this.poruke.update((trenutne) => trenutne.map((p, i) => (i === indeks ? izmjena(p) : p)));
  }
}
