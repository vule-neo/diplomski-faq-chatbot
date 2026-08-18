import re

CIR_U_LAT = {
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Ђ": "Đ", "Е": "E",
    "Ж": "Ž", "З": "Z", "И": "I", "Ј": "J", "К": "K", "Л": "L", "Љ": "Lj",
    "М": "M", "Н": "N", "Њ": "Nj", "О": "O", "П": "P", "Р": "R", "С": "S",
    "Т": "T", "Ћ": "Ć", "У": "U", "Ф": "F", "Х": "H", "Ц": "C", "Ч": "Č",
    "Џ": "Dž", "Ш": "Š",
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ђ": "đ", "е": "e",
    "ж": "ž", "з": "z", "и": "i", "ј": "j", "к": "k", "л": "l", "љ": "lj",
    "м": "m", "н": "n", "њ": "nj", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "ћ": "ć", "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "č",
    "џ": "dž", "ш": "š",
}

DIJAKRITIKA_U_OBICNA = str.maketrans({
    "č": "c", "ć": "c", "š": "s", "ž": "z", "đ": "dj",
    "Č": "c", "Ć": "c", "Š": "s", "Ž": "z", "Đ": "dj",
})

TOKEN_REGEX = re.compile(r'\w+')

DUZINA_KORIJENA = 5  # grubo korjenovanje: srpski je padezni jezik, "racuna" i "racun"
                      # se moraju poklopiti pri pretrazi kljucnim rijecima


def u_latinicu(tekst):
    return "".join(CIR_U_LAT.get(znak, znak) for znak in tekst)


def _korijen(token):
    return token[:DUZINA_KORIJENA] if len(token) > DUZINA_KORIJENA else token


def za_pretragu_kljucnim_rijecima(tekst):
    tekst = u_latinicu(tekst).lower()
    tekst = tekst.translate(DIJAKRITIKA_U_OBICNA)
    tokeni = TOKEN_REGEX.findall(tekst)
    return [_korijen(t) for t in tokeni]
