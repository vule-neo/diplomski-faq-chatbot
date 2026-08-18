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

export interface ChatPoruka {
  tip: 'korisnik' | 'bot';
  tekst: string;
  izvori?: IzvorInfo[];
}
