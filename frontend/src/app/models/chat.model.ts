export interface IzvorInfo {
  naslov_dokumenta: string;
  sekcija: string;
}

export interface OdgovorOdgovor {
  odgovor: string;
  izvori: IzvorInfo[];
}

export interface PitanjeZahtev {
  pitanje: string;
}

export interface FeedbackZahtev {
  pitanje: string;
  odgovor: string;
  koristan: boolean;
}

export interface ChatPoruka {
  tip: 'korisnik' | 'bot';
  tekst: string;
  prikazano?: string;
  izvori?: IzvorInfo[];
  izvoriOtvoreni?: boolean;
  kopirano?: boolean;
  pitanje?: string;
  ocjena?: 'koristan' | 'nekoristan';
}
