import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  FeedbackZahtev,
  OdgovorOdgovor,
  PitanjeZahtev,
  RanijaPoruka,
  StreamDogadjaj,
} from '../models/chat.model';

const API_URL = 'http://localhost:8000';

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  constructor(private http: HttpClient) {}

  postaviPitanje(pitanje: string, istorija: RanijaPoruka[] = []): Observable<OdgovorOdgovor> {
    const zahtev: PitanjeZahtev = { pitanje, istorija };
    return this.http.post<OdgovorOdgovor>(`${API_URL}/ask`, zahtev);
  }

  /**
   * Streaming verzija: odgovor stiže u dijelovima kako ga model piše, pa korisnik
   * ne gleda u prazan ekran dok traje pretraga i generisanje.
   */
  async *postaviPitanjeUDijelovima(
    pitanje: string,
    istorija: RanijaPoruka[] = [],
  ): AsyncGenerator<StreamDogadjaj> {
    const odgovor = await fetch(`${API_URL}/ask/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pitanje, istorija }),
    });

    if (!odgovor.ok || !odgovor.body) {
      throw new Error(`Server je vratio ${odgovor.status}`);
    }

    const citac = odgovor.body.getReader();
    const dekoder = new TextDecoder();
    let ostatak = '';

    while (true) {
      const { done, value } = await citac.read();
      if (done) {
        break;
      }

      ostatak += dekoder.decode(value, { stream: true });
      const redovi = ostatak.split('\n\n');
      ostatak = redovi.pop() ?? '';

      for (const red of redovi) {
        const podaci = red.replace(/^data: /, '').trim();
        if (podaci) {
          yield JSON.parse(podaci) as StreamDogadjaj;
        }
      }
    }
  }

  posaljiFeedback(pitanje: string, odgovor: string, koristan: boolean): Observable<unknown> {
    const zahtev: FeedbackZahtev = { pitanje, odgovor, koristan };
    return this.http.post(`${API_URL}/feedback`, zahtev);
  }
}
