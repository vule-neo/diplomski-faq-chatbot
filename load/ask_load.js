import http from 'k6/http';
import { check, sleep } from 'k6';

// Gdje gadjamo. Kad k6 radi u Docker mrezi, "frontend" je ime nginx servisa.
const BASE = __ENV.BASE_URL || 'http://frontend';

// Bazen pitanja - svaki virtuelni korisnik slucajno bira jedno.
const PITANJA = [
  'Koji su rokovi za prijavu ispita?',
  'Koliko ESPB treba za upis naredne godine?',
  'Kolika je skolarina za samofinansirajuce studente?',
  'Kako se prijavljuje ispit?',
  'Koji su uslovi za upis na master studije?',
];

export const options = {
  // "stages" = profil opterecenja kroz vrijeme. target = broj virtuelnih korisnika (VU).
  stages: [
    { duration: '30s', target: 10 },  // zagrijavanje: rampa do 10 korisnika
    { duration: '1m',  target: 10 },  // drzi 10
    { duration: '30s', target: 30 },  // pojacaj na 30
    { duration: '1m',  target: 30 },  // drzi 30 (ovdje trazimo granicu)
    { duration: '20s', target: 0 },   // hladjenje
  ],
  // Pragovi: ako ih prekrsimo, k6 izlazi sa greskom (korisno za CI kasnije).
  thresholds: {
    http_req_duration: ['p(95)<3000'], // p95 mora ispod 3s
    http_req_failed: ['rate<0.05'],    // manje od 5% neuspjelih zahtjeva
  },
};

export default function () {
  const pitanje = PITANJA[Math.floor(Math.random() * PITANJA.length)];
  const res = http.post(
    `${BASE}/api/ask`,
    JSON.stringify({ pitanje }),
    { headers: { 'Content-Type': 'application/json' }, timeout: '60s' },
  );
  check(res, {
    'status 200': (r) => r.status === 200,
    'ima odgovor': (r) => r.body && r.body.includes('odgovor'),
  });
  sleep(1); // "think time" izmedju pitanja jednog korisnika
}
