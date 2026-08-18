import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ChatPoruka } from './models/chat.model';
import { ChatService } from './services/chat.service';

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
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
          { tip: 'bot', tekst: odgovor.odgovor, izvori: odgovor.izvori },
        ]);
        this.ucitavanje.set(false);
      },
      error: () => {
        this.greska.set('Nije moguće dobiti odgovor. Provjeri da li backend radi, pa pokušaj ponovo.');
        this.ucitavanje.set(false);
      },
    });
  }
}
