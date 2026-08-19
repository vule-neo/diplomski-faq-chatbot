import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { FeedbackZahtev, OdgovorOdgovor, PitanjeZahtev } from '../models/chat.model';

const API_URL = 'http://localhost:8000';

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  constructor(private http: HttpClient) {}

  postaviPitanje(pitanje: string): Observable<OdgovorOdgovor> {
    const zahtev: PitanjeZahtev = { pitanje };
    return this.http.post<OdgovorOdgovor>(`${API_URL}/ask`, zahtev);
  }

  posaljiFeedback(pitanje: string, odgovor: string, koristan: boolean): Observable<unknown> {
    const zahtev: FeedbackZahtev = { pitanje, odgovor, koristan };
    return this.http.post(`${API_URL}/feedback`, zahtev);
  }
}
