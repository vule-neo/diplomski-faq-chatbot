import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ChatPoruka, IzvorInfo } from './models/chat.model';
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

  constructor(private chatService: ChatService) {}

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

    this.poruke.update((trenutne) => [...trenutne, { tip: 'korisnik', tekst: tekstPitanja }]);
    this.pitanje.set('');
    this.ucitavanje.set(true);
    this.greska.set(null);

    this.chatService.postaviPitanje(tekstPitanja).subscribe({
      next: (odgovor) => {
        this.poruke.update((trenutne) => [
          ...trenutne,
          {
            tip: 'bot',
            tekst: odgovor.odgovor,
            prikazano: '',
            izvori: this.bezDuplikata(odgovor.izvori),
            izvoriOtvoreni: false,
            pitanje: tekstPitanja,
          },
        ]);
        this.ucitavanje.set(false);
        this.animirajKucanje(this.poruke().length - 1);
      },
      error: () => {
        this.greska.set('Nije moguće dobiti odgovor. Provjeri da li backend radi, pa pokušaj ponovo.');
        this.ucitavanje.set(false);
      },
    });
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

  // postepeno otkrivanje teksta, da odgovor "dolazi" umjesto da bljesne odjednom
  private animirajKucanje(indeks: number): void {
    const puniTekst = this.poruke()[indeks].tekst;
    const korak = Math.max(1, Math.round(puniTekst.length / 200));
    let otkriveno = 0;

    const tajmer = setInterval(() => {
      otkriveno = Math.min(puniTekst.length, otkriveno + korak);
      const dio = puniTekst.slice(0, otkriveno);
      this.izmijeniPoruku(indeks, (p) => ({ ...p, prikazano: dio }));

      if (otkriveno >= puniTekst.length) {
        clearInterval(tajmer);
      }
    }, 14);
  }

  private izmijeniPoruku(indeks: number, izmjena: (p: ChatPoruka) => ChatPoruka): void {
    this.poruke.update((trenutne) => trenutne.map((p, i) => (i === indeks ? izmjena(p) : p)));
  }
}
