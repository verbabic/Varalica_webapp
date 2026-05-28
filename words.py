from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter, defaultdict
import random
import re
import unicodedata

DEFAULT_CATEGORY = "Sve kategorije"
WORD_CATEGORIES = [
    "Kuća",
    "Hrana",
    "Životinje",
    "Sport",
    "Škola",
    "Posao",
    "Tehnologija",
    "Putovanja",
    "Priroda",
    "Prevoz",
    "Odeća",
    "Zdravlje",
    "Zabava",
    "Balkan"
]
ALLOWED_CATEGORIES = [DEFAULT_CATEGORY, *WORD_CATEGORIES]
ALLOWED_DIFFICULTIES = {"easy", "normal", "hard"}

SUSPICIOUS_PREFIXES = (
    "svakodnevni ", "svakodnevna ", "svakodnevno ",
    "profesionalni ", "profesionalna ", "profesionalno ",
    "mali ", "mala ", "malo ", "veliki ", "velika ", "veliko ",
    "moderni ", "moderna ", "moderno ", "zanimljiv ", "zanimljiva ",
    "poseban ", "posebna ", "brzi ", "brza ", "brzo ",
)

BANNED_DIRECT_HINTS = {
    "prevod", "prevođenje", "tekst", "slova", "subtitles", "subtitle",
    "sinonim", "prijevod", "definicija", "tačan naziv", "točan naziv",
    "zaštita od kiše", "osoba koja predaje", "uređaj", "predmet",
}

ASCII_DIACRITIC_EXPECTATIONS = {
    "kuca": "kuća", "vozac": "vozač", "cebe": "ćebe", "djak": "đak",
    "zivotinja": "životinja", "macka": "mačka", "casa": "čaša",
    "rucak": "ručak", "suma": "šuma", "zaba": "žaba", "noz": "nož",
    "sesir": "šešir", "kisobran": "kišobran", "carapa": "čarapa",
}

EXACT_HINT_POOLS = {
    "kuća": ["porodica", "ključ", "dvorište", "večer"],
    "stan": ["zgrada", "lift", "komšije", "balkon"],
    "soba": ["prozor", "vrata", "tišina", "svjetlo"],
    "kuhinja": ["ručak", "miris", "šporet", "stol"],
    "kupatilo": ["pločice", "para", "ručnik", "jutro"],
    "dnevni boravak": ["kauč", "televizor", "gosti", "večer"],
    "spavaća soba": ["noć", "ormar", "jastuk", "tišina"],
    "hodnik": ["cipele", "ključevi", "vrata", "žurba"],
    "balkon": ["biljke", "kafa", "sunce", "pogled"],
    "stol": ["ručak", "stolice", "porodica", "tanjir"],
    "krevet": ["san", "noć", "jastuk", "spavaća soba"],
    "ormar": ["odjeća", "vješalice", "ladice", "spavaća soba"],
    "stolica": ["sjedenje", "kuhinja", "učionica", "naslon"],
    "lampa": ["večer", "svjetlo", "noćni ormarić", "soba"],
    "kanta za smeće": ["čišćenje", "kuhinja", "vreća", "miris"],
    "kanta za đubre": ["čišćenje", "kuhinja", "vreća", "miris"],
    "žlica": ["supa", "tanjir", "ručak", "kuhinja"],
    "kašika": ["supa", "tanjir", "ručak", "kuhinja"],
    "vilica": ["ručak", "tanjir", "restoran", "stol"],
    "viljuška": ["ručak", "tanjir", "restoran", "stol"],
    "nož": ["ručak", "daska", "kuhinja", "oprez"],
    "čaša": ["voda", "stol", "kuhinja", "gost"],
    "šalica": ["jutro", "kafa", "čaj", "pauza"],
    "šolja": ["jutro", "kafa", "čaj", "pauza"],
    "jastuk": ["san", "noć", "krevet", "glava"],
    "tepih": ["pod", "dnevna soba", "bosonogo", "usisavanje"],
    "zavjesa": ["prozor", "jutro", "svjetlost", "soba"],
    "zavesa": ["prozor", "jutro", "svetlost", "soba"],
    "ključ": ["vrata", "džep", "brava", "povratak"],
    "prozor": ["kuća", "svjetlost", "soba", "zavjesa"],
    "kruh": ["doručak", "pekara", "namaz", "sendvič"],
    "hleb": ["doručak", "pekara", "namaz", "sendvič"],
    "sir": ["doručak", "sendvič", "frižider", "pijaca"],
    "mlijeko": ["doručak", "čaša", "frižider", "kafa"],
    "mleko": ["doručak", "čaša", "frižider", "kafa"],
    "jaje": ["doručak", "tava", "kuhinja", "ljuska"],
    "maslac": ["namaz", "doručak", "frižider", "kruh"],
    "puter": ["namaz", "doručak", "frižider", "hleb"],
    "jabuka": ["voće", "škola", "torba", "užina"],
    "naranča": ["zima", "sok", "miris", "vitamin"],
    "pomorandža": ["zima", "sok", "miris", "vitamin"],
    "krumpir": ["ručak", "pećnica", "prilog", "selo"],
    "krompir": ["ručak", "rerna", "prilog", "selo"],
    "čokolada": ["slatko", "poklon", "film", "poslastica"],
    "kava": ["jutro", "šoljica", "razgovor", "pauza"],
    "kafa": ["jutro", "šoljica", "razgovor", "pauza"],
    "banana": ["voće", "užina", "pijaca", "žuto"],
    "jogurt": ["doručak", "frižider", "kašika", "voće"],
    "lubenica": ["ljeto", "plaža", "nož", "sok"],
    "burek": ["jutro", "pekara", "jogurt", "red"],
    "ćevapi": ["roštilj", "lepinja", "društvo", "dim"],
    "sarma": ["praznik", "porodica", "lonac", "zima"],
    "ajvar": ["zimnica", "paprika", "tegla", "roštilj"],
    "pas": ["šetnja", "povodac", "dvorište", "lavež"],
    "mačka": ["kauč", "prozor", "noć", "šapa"],
    "konj": ["selo", "sedlo", "trka", "štala"],
    "koza": ["selo", "brdo", "mlijeko", "stado"],
    "zec": ["mrkva", "livada", "uši", "tišina"],
    "lav": ["savana", "rikanje", "griva", "zoološki vrt"],
    "slon": ["savana", "surla", "veličina", "zoološki vrt"],
    "pčela": ["cvijet", "med", "košnica", "ljeto"],
    "nogomet": ["stadion", "lopta", "navijanje", "gol"],
    "fudbal": ["stadion", "lopta", "navijanje", "gol"],
    "košarka": ["parket", "obruč", "patike", "utakmica"],
    "tenis": ["reket", "mreža", "teren", "servis"],
    "šah": ["tišina", "tabla", "potez", "koncentracija"],
    "plivanje": ["bazen", "voda", "ljeto", "trening"],
    "posao": ["jutro", "kafa", "rok", "sastanak"],
    "ured": ["kancelarija", "stol", "računar", "pauza"],
    "kancelarija": ["stol", "računar", "pauza", "telefon"],
    "radni stol": ["laptop", "papiri", "kafa", "rok"],
    "radni sto": ["laptop", "papiri", "kafa", "rok"],
    "sastanak": ["kafa", "stol", "plan", "kolege"],
    "pauza": ["kafa", "hodnik", "razgovor", "sendvič"],
    "kalendar": ["datum", "rok", "zid", "plan"],
    "plaća": ["mjesec", "banka", "račun", "posao"],
    "plata": ["mesec", "banka", "račun", "posao"],
    "profesor": ["škola", "učionica", "ispit", "tabla"],
    "učitelj": ["razred", "dnevnik", "tabla", "ocjena"],
    "matematika": ["brojevi", "zadatak", "ispit", "bilježnica"],
    "fizika": ["eksperiment", "formula", "laboratorij", "tabla"],
    "kemija": ["laboratorij", "epruveta", "miris", "zaštitne naočale"],
    "hemija": ["laboratorija", "epruveta", "miris", "zaštitne naočare"],
    "ravnalo": ["crta", "geometrija", "pernica", "škola"],
    "lenjir": ["crta", "geometrija", "pernica", "škola"],
    "odvjetnik": ["sud", "dokumenti", "odijelo", "sastanak"],
    "advokat": ["sud", "dokumenti", "odijelo", "sastanak"],
    "vozač": ["volan", "cesta", "smjena", "gorivo"],
    "kuhar": ["tava", "restoran", "miris", "večera"],
    "kuvar": ["tiganj", "restoran", "miris", "večera"],
    "frizer": ["ogledalo", "škare", "stolica", "termin"],
    "liječnik": ["pregled", "čekaonica", "bijeli mantil", "termin"],
    "lekar": ["pregled", "čekaonica", "beli mantil", "termin"],
    "zub": ["osmijeh", "četkica", "bol", "pasta"],
    "ljekarna": ["recept", "red", "tablete", "savjet"],
    "apoteka": ["recept", "red", "tablete", "savjet"],
    "naočale": ["vid", "knjiga", "ekran", "okvir"],
    "naočare": ["vid", "knjiga", "ekran", "okvir"],
    "jakna": ["zima", "vješalica", "rukav", "izlazak"],
    "cipela": ["ulica", "pertle", "hodanje", "ormar"],
    "kapa": ["glava", "sunce", "zima", "stil"],
    "čarapa": ["stopala", "ladica", "pranje", "par"],
    "kišobran": ["jesen", "ulica", "oblaci", "torba"],
    "sunce": ["ljeto", "plaža", "svjetlost", "nebo"],
    "kiša": ["oblaci", "ulica", "jesen", "kapljice"],
    "šuma": ["drveće", "hlad", "staza", "mir"],
    "rijeka": ["most", "obala", "voda", "šetnja"],
    "reka": ["most", "obala", "voda", "šetnja"],
    "hotel": ["recepcija", "kofer", "ključ", "doručak"],
    "autocesta": ["radio", "brzina", "gorivo", "odmor"],
    "auto-put": ["radio", "brzina", "gorivo", "odmor"],
    "putovnica": ["granica", "aerodrom", "kontrola", "torba"],
    "pasoš": ["granica", "aerodrom", "kontrola", "torba"],
    "plaža": ["more", "peškir", "sunce", "odmor"],
    "karta grada": ["put", "orijentacija", "grad", "telefon"],
    "mapa grada": ["put", "orijentacija", "grad", "telefon"],
    "automobil": ["parking", "volan", "put", "gorivo"],
    "auto": ["parking", "volan", "put", "gorivo"],
    "autobus": ["stanica", "karta", "gužva", "jutro"],
    "metro": ["podzemlje", "stanica", "karta", "grad"],
    "vlak": ["peron", "karta", "putovanje", "pruga"],
    "voz": ["peron", "karta", "putovanje", "pruga"],
    "bicikl": ["pedale", "park", "lanac", "vožnja"],
    "baterija": ["punjenje", "daljinski", "telefon", "struja"],
    "računalo": ["tastatura", "posao", "ekran", "stol"],
    "računar": ["tastatura", "posao", "ekran", "sto"],
    "laptop": ["posao", "torba", "tastatura", "sastanak"],
    "tablet": ["kauč", "ekran", "crtanje", "putovanje"],
    "kamera": ["slika", "putovanje", "uspomena", "objektiv"],
    "aplikacija": ["telefon", "ikonica", "poruka", "ekran"],
    "web stranica": ["preglednik", "link", "ekran", "internet"],
    "veb stranica": ["pregledač", "link", "ekran", "internet"],
    "router": ["Wi-Fi", "stan", "lozinka", "signal"],
    "ruter": ["Wi-Fi", "stan", "lozinka", "signal"],
    "telefon": ["poruka", "poziv", "džep", "aplikacija"],
    "mobitel": ["poruka", "poziv", "džep", "aplikacija"],
    "kod": ["programiranje", "ekran", "lozinka", "greška"],
    "kôd": ["programiranje", "ekran", "lozinka", "greška"],
    "titlovi": ["bioskop", "epizoda", "Netflix", "ekran"],
    "film": ["kokice", "mrak", "kauč", "večer"],
    "serija": ["epizoda", "kauč", "Netflix", "vikend"],
    "kino": ["kokice", "film", "mrak", "platno"],
    "bioskop": ["kokice", "film", "mrak", "platno"],
    "kazalište": ["scena", "publika", "glumci", "aplauz"],
    "pozorište": ["scena", "publika", "glumci", "aplauz"],
    "koncert": ["publika", "svjetla", "muzika", "večer"],
    "gitara": ["pjesma", "koncert", "žica", "društvo"],
    "poklon": ["rođendan", "iznenađenje", "slavlje", "kutija"],
    "društvena igra": ["smijeh", "ekipa", "večer", "izazov"],
    "kafana": ["muzika", "društvo", "čaša", "noć"],
    "pekara": ["jutro", "burek", "miris", "red"],
    "tržnica": ["tezga", "voće", "subota", "gužva"],
    "pijaca": ["tezga", "voće", "subota", "gužva"],
    "susjed": ["zgrada", "dvorište", "pozdrav", "vrata"],
    "komšija": ["zgrada", "dvorište", "pozdrav", "vrata"],
    "dijaspora": ["granica", "kofer", "praznici", "porodica"],
    "sok od bazge": ["ljeto", "dvorište", "čaša", "domaće"],
    "sok od zove": ["leto", "dvorište", "čaša", "domaće"],
    "košulja": ["dugmad", "ormar", "posao", "pegla"],
    "poraz": ["utakmica", "tišina", "svlačionica", "razočaranje"],
    "krava": ["selo", "štala", "mlijeko", "livada"],
    "medicinske rukavice": ["pregled", "ordinacija", "maska", "higijena"],
    "rukavice medicinske": ["pregled", "ordinacija", "maska", "higijena"],
}


# Targeted repairs for weak generated hint pools found in the full 1000-word audit.
# Keys are ascii-folded (category, HR word), so they are stable across diacritics/case.
CATEGORY_EXACT_HINT_POOLS = {
    ("balkan", "djed"): ["priča","dvorište","novine","porodica"],
    ("balkan", "dzezva"): ["kafa","šporet","miris","jutro"],
    ("balkan", "kafana"): ["muzika","društvo","čaša","noć"],
    ("balkan", "kajmak na stolu"): ["trpeza","lepinja","doručak","selo"],
    ("balkan", "kuma"): ["kuhinja","ručak","ruke","stol"],
    ("balkan", "papirnati rucnik"): ["priča","dvorište","novine","porodica"],
    ("balkan", "priganice"): ["tijesto","ulje","doručak","porodica"],
    ("balkan", "rakija"): ["čašica","slavlje","gost","zima"],
    ("balkan", "seoski vrt"): ["dvorište","povrće","ljeto","selo"],
    ("balkan", "zimnica"): ["kuhinja","ručak","ruke","stol"],
    ("hrana", "kruska"): ["čaša","žeđ","ljeto","trening"],
    ("hrana", "kukuruz"): ["klip","roštilj","ljeto","putar"],
    ("hrana", "kupus"): ["sendvič","doručak","frižider","narezano"],
    ("hrana", "paprika"): ["klip","roštilj","ljeto","putar"],
    ("hrana", "salata"): ["sendvič","doručak","frižider","narezano"],
    ("hrana", "sunka"): ["zdjela","ljeto","povrće","ručak"],
    ("hrana", "voda"): ["sendvič","doručak","frižider","narezano"],
    ("odeca", "cizma"): ["pegla","košulja","para","daska"],
    ("odeca", "donje rublje"): ["pegla","košulja","para","daska"],
    ("odeca", "duks"): ["zima","vješalica","hladnoća","izlazak"],
    ("odeca", "kaput"): ["haljina","meko","sjaj","svečano"],
    ("odeca", "majica"): ["džemper","pletivo","toplina","zima"],
    ("odeca", "nausnica"): ["uho","nakit","ogledalo","kutija"],
    ("odeca", "peglanje"): ["rukav","ljeto","ormar","pranje"],
    ("odeca", "pidzama"): ["kapuljača","jesen","trening","ormar"],
    ("odeca", "sal"): ["džemper","pletivo","toplina","zima"],
    ("odeca", "svila"): ["ladica","pranje","jutro","privatno"],
    ("odeca", "vuna"): ["ladica","pranje","jutro","privatno"],
    ("posao", "alat"): ["radionica","popravka","majstor","garaža"],
    ("posao", "blagajnik"): ["garaža","popravka","majstor","ulje"],
    ("posao", "direktor"): ["ured","sastanak","odluka","potpis"],
    ("posao", "kaciga na gradilistu"): ["ured","odluka","sastanak","potpis"],
    ("posao", "kava na poslu"): ["pauza","šoljica","kolege","jutro"],
    ("posao", "poljoprivrednik"): ["pauza","šoljica","kolege","jutro"],
    ("posao", "programer"): ["kod","laptop","kafa","bug"],
    ("posao", "sef"): ["kancelarija","odluka","sastanak","rok"],
    ("posao", "stolar"): ["drvo","radionica","pila","namještaj"],
    ("posao", "sudac na poslu"): ["ugovor","potpis","pravila","dokumenti"],
    ("posao", "ugovor"): ["potpis","dokument","sastanak","pravila"],
    ("posao", "vizitka"): ["sastanak","džep","ime","kontakt"],
    ("prevoz", "benzin"): ["stanica","karta","čekanje","kofer"],
    ("prevoz", "bicikl za prevoz"): ["nebo","buka","propeler","spasavanje"],
    ("prevoz", "brodska luka"): ["more","brodovi","obala","putnici"],
    ("prevoz", "cesta"): ["asfalt","auto","krivina","putovanje"],
    ("prevoz", "cestovni tunel"): ["mrak","cesta","svjetla","planina"],
    ("prevoz", "helikopter"): ["nebo","buka","propeler","spasavanje"],
    ("prevoz", "kolodvor za prevoz"): ["pumpa","auto","cijena","miris"],
    ("prevoz", "kolona"): ["gužva","auta","čekanje","granica"],
    ("prevoz", "kruzni tok"): ["raskrsnica","grad","skretanje","vozač"],
    ("prevoz", "mjenjac"): ["auto","ruka","brzina","vožnja"],
    ("prevoz", "motor vozila"): ["auto","ulje","buka","garaža"],
    ("prevoz", "navigacija u autu"): ["raskrsnica","grad","skretanje","vozač"],
    ("prevoz", "peron za voz"): ["stanica","pruga","karta","čekanje"],
    ("prevoz", "prometni semafor"): ["raskrsnica","crveno","pješaci","grad"],
    ("prevoz", "pruga"): ["šine","peron","vlak","putovanje"],
    ("prevoz", "putnik"): ["kofer","karta","stanica","sjedalo"],
    ("prevoz", "sjediste"): ["asfalt","auto","krivina","putovanje"],
    ("prevoz", "skretanje"): ["raskrsnica","grad","žmigavac","vozač"],
    ("prevoz", "skuter"): ["stanica","karta","čekanje","kofer"],
    ("prevoz", "tablica"): ["auto","parking","policija","brojevi"],
    ("prevoz", "taksi vozilo"): ["pojas","prozor","vožnja","putnik"],
    ("prevoz", "tramvaj"): ["pedale","park","lanac","vožnja"],
    ("putovanja", "autobusna karta za put"): ["mapa","telefon","raskrsnica","adresa"],
    ("putovanja", "avionska karta"): ["peron","pruga","kofer","prozor"],
    ("putovanja", "dorucak u hotelu"): ["jutro","švedski sto","recepcija","putovanje"],
    ("putovanja", "granica"): ["šator","vatra","šuma","noć"],
    ("putovanja", "izlet za vikend"): ["ruksak","društvo","priroda","subota"],
    ("putovanja", "kamp"): ["šator","vatra","šuma","vreća"],
    ("putovanja", "kampiranje"): ["hotel","ključ","recepcija","doručak"],
    ("putovanja", "kofer"): ["aerodrom","odjeća","hotel","točkići"],
    ("putovanja", "ljetovanje"): ["more","plaža","apartman","sunce"],
    ("putovanja", "luka"): ["vrijeme","tabla","čekanje","stanica"],
    ("putovanja", "most"): ["brodovi","obala","putnici","luka"],
    ("putovanja", "navigacija za put"): ["hotel","ključ","recepcija","doručak"],
    ("putovanja", "plan puta"): ["more","plaža","apartman","sunce"],
    ("putovanja", "putna torba"): ["šator","vatra","šuma","noć"],
    ("putovanja", "putnicki vlak"): ["peron","pruga","kofer","prozor"],
    ("putovanja", "raspored"): ["more","plaža","apartman","sunce"],
    ("putovanja", "recepcija hotela"): ["hotel","ključ","prijava","kofer"],
    ("putovanja", "rent-a-car"): ["ključevi","parking","ugovor","putovanje"],
    ("putovanja", "rezervacija"): ["datum","hotel","potvrda","telefon"],
    ("putovanja", "sator"): ["ruksak","društvo","priroda","subota"],
    ("putovanja", "soba u hotelu"): ["magnet","uspomena","grad","poklon"],
    ("putovanja", "suvenir"): ["magnet","uspomena","grad","poklon"],
    ("putovanja", "taksi"): ["adresa","aplikacija","noć","vožnja"],
    ("putovanja", "tunel"): ["mrak","cesta","svjetla","planina"],
    ("putovanja", "valuta"): ["mjenjačnica","novčanik","putovanje","račun"],
    ("putovanja", "vodic"): ["šator","vatra","šuma","noć"],
    ("putovanja", "vozna karta za put"): ["vrijeme","tabla","čekanje","stanica"],
    ("putovanja", "zimovanje"): ["snijeg","planina","skije","rukavice"],
    ("skola", "biologija"): ["riječi","izgovor","knjiga","čas"],
    ("skola", "engleski"): ["brojevi","zadatak","torba","tipke"],
    ("skola", "hrvatski"): ["lektira","gramatika","učionica","sveska"],
    ("skola", "kalkulator"): ["boje","tabla","pernica","prezentacija"],
    ("skola", "markeri"): ["ispit","tabla","učionica","škola"],
    ("skola", "njemacki"): ["torba","klupa","razred","odmor"],
    ("skola", "profesor"): ["boje","tabla","pernica","prezentacija"],
    ("skola", "skola"): ["zvono","tabla","učionica","torba"],
    ("skola", "ucenik"): ["brojevi","zadatak","torba","tipke"],
    ("sport", "atletika"): ["cesta","pedale","kaciga","trka"],
    ("sport", "biciklizam"): ["teren","navijanje","rezultat","ekipa"],
    ("sport", "boks"): ["ring","rukavice","znoj","sudija"],
    ("sport", "gol"): ["mreža","stadion","navijanje","lopta"],
    ("sport", "jedrenje"): ["more","vjetar","jedro","luka"],
    ("sport", "judo"): ["tatami","kimono","pojas","borba"],
    ("sport", "kladivo"): ["atletika","bacanje","teren","mjerenje"],
    ("sport", "kopacke"): ["trava","svlačionica","pertle","utakmica"],
    ("sport", "kup"): ["trofej","finale","ekipa","slavlje"],
    ("sport", "liga"): ["sezona","tabela","klub","utakmica"],
    ("sport", "lopta"): ["ring","rukavice","sudija","publika"],
    ("sport", "nerijeseno"): ["rezultat","semafor","kraj","utakmica"],
    ("sport", "obrana"): ["stadion","staza","start","znoj"],
    ("sport", "palica"): ["teren","lopta","udarac","oprema"],
    ("sport", "pecat pobjede"): ["trofej","slavlje","finale","uspomena"],
    ("sport", "pikado"): ["meta","strelica","koncentracija","pub"],
    ("sport", "pobjeda"): ["slavlje","ekipa","rezultat","svlačionica"],
    ("sport", "poraz"): ["svlačionica","tišina","rezultat","razočaranje"],
    ("sport", "rezerva"): ["klupa","trener","dres","utakmica"],
    ("sport", "ronjenje"): ["zviždaljka","pravila","teren","pritisak"],
    ("sport", "rukavice"): ["ring","trening","oprema","torba"],
    ("sport", "semafor"): ["rezultat","dvorana","utakmica","svjetla"],
    ("sport", "skijanje"): ["zviždaljka","pravila","teren","pritisak"],
    ("sport", "sprint"): ["start","staza","brzina","dah"],
    ("sport", "stitnici"): ["koljena","oprema","trening","torba"],
    ("sport", "sudac"): ["zviždaljka","pravila","teren","utakmica"],
    ("sport", "trcanje"): ["snijeg","staza","kaciga","planina"],
    ("sport", "utakmica"): ["teren","navijanje","ekipa","rezultat"],
    ("sport", "vaterpolo"): ["bazen","lopta","gol","kapica"],
    ("tehnologija", "cloud servis"): ["podaci","kablovi","noć","server"],
    ("tehnologija", "konzola"): ["ruter","lozinka","signal","stan"],
    ("tehnologija", "poruka"): ["kamera","sastanak","ekran","poziv"],
    ("tehnologija", "pretraga"): ["kamera","sastanak","ekran","poziv"],
    ("tehnologija", "server"): ["podaci","fajlovi","internet","backup"],
    ("tehnologija", "signal"): ["preglednik","link","stranica","ekran"],
    ("tehnologija", "video poziv"): ["kamera","sastanak","ekran","poziv"],
    ("tehnologija", "web stranica"): ["Wi-Fi","telefon","brdo","mreža"],
    ("tehnologija", "wi-fi"): ["igrica","kontroler","kauč","ekran"],
    ("zabava", "audio emisija"): ["red","koncert","džep","kontrola"],
    ("zabava", "diskoteka"): ["muzika","svjetla","ples","noć"],
    ("zabava", "glazba"): ["vikend","radost","ekipa","hobi"],
    ("zabava", "hobi"): ["slobodno vrijeme","vikend","radost","ekipa"],
    ("zabava", "igraca konzola"): ["mikrofon","pjesma","društvo","smijeh"],
    ("zabava", "karaoke"): ["slušalice","glas","epizoda","šetnja"],
    ("zabava", "klovn"): ["igrica","kontroler","kauč","ekran"],
    ("zabava", "kokice u kinu"): ["torta","poklon","svijeće","slavlje"],
    ("zabava", "pjesma"): ["radio","glas","refren","društvo"],
    ("zabava", "rođendan"): ["cirkus","smijeh","djeca","kostim"],
    ("zabava", "sajam"): ["štand","gužva","ulaznica","vikend"],
    ("zabava", "serija"): ["slušalice","glas","epizoda","šetnja"],
    ("zabava", "sjedalo u kinu"): ["cirkus","smijeh","djeca","kostim"],
    ("zabava", "titlovi"): ["cirkus","smijeh","djeca","kostim"],
    ("zabava", "ulaznica"): ["mikrofon","pjesma","društvo","smijeh"],
    ("zabava", "zabava"): ["red","koncert","džep","kontrola"],
    ("zdravlje", "alergija"): ["proljeće","kihanje","polen","apoteka"],
    ("zdravlje", "ambulanta"): ["čekaonica","pregled","termin","bijeli mantil"],
    ("zdravlje", "caj za grlo"): ["apoteka","papir","savjet","red"],
    ("zdravlje", "disanje"): ["čekaonica","termin","stolica","pitanja"],
    ("zdravlje", "glava"): ["kapa","jastuk","misli","bol"],
    ("zdravlje", "grlo"): ["čaj","zima","glas","šal"],
    ("zdravlje", "higijena"): ["tanjir","navika","povrće","energija"],
    ("zdravlje", "joga"): ["prostirka","tišina","disanje","jutro"],
    ("zdravlje", "kontrola"): ["park","patike","jutro","dah"],
    ("zdravlje", "kratak odmor"): ["pauza","kauč","voda","tišina"],
    ("zdravlje", "lagano trcanje"): ["park","patike","jutro","dah"],
    ("zdravlje", "lijecnik opce prakse"): ["čekaonica","termin","bijeli mantil","recept"],
    ("zdravlje", "masaza"): ["opuštanje","stol","ulje","termin"],
    ("zdravlje", "med za grlo"): ["park","patike","jutro","dah"],
    ("zdravlje", "naocale za vid"): ["prostirka","tišina","disanje","jutro"],
    ("zdravlje", "nos"): ["torbica","koljeno","flaster","prst"],
    ("zdravlje", "oko"): ["pogled","naočale","svjetlo","lice"],
    ("zdravlje", "ordinacija"): ["čekaonica","pregled","stolica","termin"],
    ("zdravlje", "pregled"): ["čekaonica","termin","stolica","pitanja"],
    ("zdravlje", "prehlada"): ["zima","čaj","maramice","krevet"],
    ("zdravlje", "prehrana"): ["tanjir","navika","povrće","energija"],
    ("zdravlje", "puls"): ["zglob","sat","ritam","trčanje"],
    ("zdravlje", "recept"): ["apoteka","papir","lijek","doktor"],
    ("zdravlje", "rucnik za zdravlje"): ["tuš","kupatilo","voda","torba"],
    ("zdravlje", "ruka"): ["tanjir","navika","povrće","energija"],
    ("zdravlje", "san"): ["torbica","koljeno","flaster","prst"],
    ("zdravlje", "sapunjanje"): ["kupatilo","voda","tuš","peškir"],
    ("zdravlje", "setnja"): ["park","koraci","zrak","veče"],
    ("zdravlje", "sluh"): ["uho","zvuk","tišina","muzika"],
    ("zdravlje", "srce"): ["emocija","trčanje","grudi","ritam"],
    ("zdravlje", "stomak"): ["ručak","čaj","pojas","mir"],
    ("zdravlje", "uho"): ["zvuk","slušalice","muzika","tišina"],
    ("zdravlje", "vjezba"): ["čekaonica","termin","stolica","pitanja"],
    ("zdravlje", "zavoj"): ["dlan","rukav","pozdrav","sat"],
    ("zivotinje", "bubamara"): ["trava","tišina","koža","oprez"],
    ("zivotinje", "dabar"): ["rijeka","brana","drvo","zubi"],
    ("zivotinje", "dupin"): ["trg","mrvice","grad","krila"],
    ("zivotinje", "flamingo"): ["lišće","bodlje","vrt","noć"],
    ("zivotinje", "golub"): ["trg","mrvice","grad","krila"],
    ("zivotinje", "jez"): ["lišće","bodlje","vrt","noć"],
    ("zivotinje", "kokos"): ["dvorište","jaje","perje","selo"],
    ("zivotinje", "komarac"): ["plaža","pijesak","talasi","more"],
    ("zivotinje", "labud"): ["jezero","bijelo","vrat","mir"],
    ("zivotinje", "muha"): ["trg","mrvice","grad","krila"],
    ("zivotinje", "noj"): ["ljeto","zujanje","noć","ubod"],
    ("zivotinje", "ovca"): ["vuna","stado","livada","selo"],
    ("zivotinje", "papiga"): ["list","crveno","tačkice","vrt"],
    ("zivotinje", "skoljka"): ["trava","tišina","koža","oprez"],
    ("zivotinje", "srna"): ["šuma","livada","tišina","jutro"],
    ("zivotinje", "svinja"): ["blato","farma","korito","selo"],
    ("zivotinje", "tigar"): ["ljeto","zujanje","noć","ubod"],
    ("zivotinje", "zmija"): ["jezero","perje","voda","mir"],
}

def category_exact_hint_pool(category: str, hr: str, sr: str) -> list[str] | None:
    category_fold = ascii_fold(category)
    return (
        CATEGORY_EXACT_HINT_POOLS.get((category_fold, ascii_fold(hr)))
        or CATEGORY_EXACT_HINT_POOLS.get((category_fold, ascii_fold(sr)))
    )

CATEGORY_EXACT_HINT_POOLS.update({
    # Batch 2A: reviewed Putovanja, Prevoz and Sport medium entries.
    ("putovanja", "putovanje"): ["kofer", "karta", "polazak", "uspomena"],
    ("putovanja", "kofer"): ["aerodrom", "odjeća", "hotel", "točkići"],
    ("putovanja", "putna torba"): ["vikend", "rame", "odjeća", "stanica"],
    ("putovanja", "putovnica"): ["granica", "aerodrom", "kontrola", "torba"],
    ("putovanja", "osobna iskaznica"): ["novčanik", "kontrola", "dokument", "granica"],
    ("putovanja", "avionska karta"): ["aerodrom", "gejt", "let", "kofer"],
    ("putovanja", "vozna karta za put"): ["peron", "vlak", "kontrola", "sjedalo"],
    ("putovanja", "autobusna karta za put"): ["stanica", "sjedalo", "kontrola", "ruksak"],
    ("putovanja", "hotel"): ["recepcija", "kofer", "ključ", "doručak"],
    ("putovanja", "apartman"): ["ključ", "more", "kuhinja", "odmor"],
    ("putovanja", "recepcija hotela"): ["hotel", "ključ", "prijava", "kofer"],
    ("putovanja", "soba u hotelu"): ["ključ", "krevet", "recepcija", "kofer"],
    ("putovanja", "kljuc od sobe"): ["vrata", "recepcija", "džep", "hotel"],
    ("putovanja", "plaza"): ["more", "peškir", "sunce", "odmor"],
    ("putovanja", "more na odmoru"): ["plaža", "talasi", "peškir", "ljeto"],
    ("putovanja", "planina na odmoru"): ["ruksak", "pogled", "zrak", "staza"],
    ("putovanja", "grad za vikend"): ["šetnja", "mapa", "kafić", "ulice"],
    ("putovanja", "selo za odmor"): ["dvorište", "tišina", "rodbina", "jutro"],
    ("putovanja", "granica"): ["kontrola", "pasoš", "kolona", "put"],
    ("putovanja", "carina"): ["kontrola", "kofer", "granica", "pitanja"],
    ("putovanja", "aerodrom"): ["kofer", "kontrola", "gejt", "red"],
    ("putovanja", "kolodvor"): ["peron", "tabla", "kofer", "čekanje"],
    ("putovanja", "peron"): ["vlak", "kofer", "stanica", "čekanje"],
    ("putovanja", "putnicki vlak"): ["peron", "pruga", "kofer", "prozor"],
    ("putovanja", "putnicki autobus"): ["stanica", "karta", "gužva", "jutro"],
    ("putovanja", "taksi"): ["adresa", "aplikacija", "noć", "vožnja"],
    ("putovanja", "rent-a-car"): ["ključevi", "parking", "ugovor", "izlet"],
    ("putovanja", "karta grada"): ["ulice", "orijentacija", "telefon", "centar"],
    ("putovanja", "vodic"): ["grupa", "grad", "priča", "šetnja"],
    ("putovanja", "turist"): ["fotoaparat", "mapa", "kofer", "suvenir"],
    ("putovanja", "suvenir"): ["magnet", "uspomena", "grad", "poklon"],
    ("putovanja", "razglednica"): ["markica", "slika", "pošta", "uspomena"],
    ("putovanja", "fotografija s puta"): ["uspomena", "kamera", "pejzaž", "album"],
    ("putovanja", "kamp"): ["šator", "vatra", "šuma", "vreća"],
    ("putovanja", "sator"): ["kamp", "trava", "noć", "vreća"],
    ("putovanja", "kampiranje"): ["šator", "vatra", "šuma", "noć"],
    ("putovanja", "izlet za vikend"): ["ruksak", "društvo", "priroda", "subota"],
    ("putovanja", "godisnji odmor"): ["slobodni dani", "kofer", "more", "plan"],
    ("putovanja", "ljetovanje"): ["more", "plaža", "apartman", "sunce"],
    ("putovanja", "zimovanje"): ["snijeg", "planina", "skije", "rukavice"],
    ("putovanja", "krstarenje"): ["brod", "paluba", "more", "luka"],
    ("putovanja", "trajekt"): ["brod", "auta", "paluba", "luka"],
    ("putovanja", "luka"): ["brodovi", "more", "putnici", "obala"],
    ("putovanja", "most"): ["rijeka", "grad", "šetnja", "pogled"],
    ("putovanja", "tunel"): ["mrak", "cesta", "svjetla", "planina"],
    ("putovanja", "autocesta"): ["radio", "brzina", "gorivo", "odmor"],
    ("putovanja", "putokaz"): ["raskrsnica", "tabla", "smjer", "vožnja"],
    ("putovanja", "raspored"): ["vrijeme", "tabla", "čekanje", "stanica"],
    ("putovanja", "rezervacija"): ["datum", "hotel", "potvrda", "telefon"],
    ("putovanja", "krevet u hotelu"): ["soba", "ključ", "noć", "jastuk"],
    ("putovanja", "dorucak u hotelu"): ["jutro", "švedski sto", "recepcija", "kafa"],
    ("putovanja", "bazen u hotelu"): ["peškir", "ležaljka", "odmor", "dvorište"],
    ("putovanja", "rucnik za plazu"): ["more", "pijesak", "torba", "sunce"],
    ("putovanja", "krema za sunce"): ["plaža", "ramena", "ljeto", "torba"],
    ("putovanja", "suncane naocale"): ["sunce", "plaža", "lice", "kofer"],
    ("putovanja", "fotoaparat"): ["slika", "uspomena", "objektiv", "pejzaž"],
    ("putovanja", "viza"): ["ambasada", "pasoš", "granica", "formular"],
    ("putovanja", "valuta"): ["mjenjačnica", "novčanik", "putovanje", "račun"],
    ("putovanja", "mjenjacnica"): ["novac", "šalter", "kurs", "grad"],
    ("putovanja", "rucna prtljaga"): ["aerodrom", "kabina", "torba", "kontrola"],
    ("putovanja", "prtljaga"): ["kofer", "aerodrom", "traka", "čekanje"],
    ("putovanja", "ukrcaj"): ["gejt", "red", "karta", "avion"],
    ("putovanja", "let"): ["avion", "nebo", "gejt", "sjedalo"],
    ("putovanja", "kasnjenje"): ["tabla", "čekanje", "aerodrom", "nervoza"],
    ("putovanja", "smjestaj"): ["ključ", "recepcija", "noćenje", "adresa"],
    ("putovanja", "plan puta"): ["bilješke", "mapa", "vrijeme", "dogovor"],
    ("putovanja", "adresa"): ["mapa", "telefon", "ulica", "dolazak"],
    ("putovanja", "navigacija za put"): ["mapa", "telefon", "raskrsnica", "adresa"],
    ("putovanja", "turisticki ured"): ["brošura", "mapa", "šalter", "grad"],
    ("putovanja", "slikanje"): ["kamera", "uspomena", "pogled", "telefon"],
    ("putovanja", "setnja gradom"): ["ulice", "izlog", "mapa", "kafa"],
    ("putovanja", "nocenje"): ["krevet", "ključ", "torba", "jutro"],

    ("prevoz", "automobil"): ["parking", "volan", "put", "gorivo"],
    ("prevoz", "auto"): ["parking", "volan", "put", "gorivo"],
    ("prevoz", "autobus"): ["stanica", "karta", "gužva", "jutro"],
    ("prevoz", "vlak"): ["peron", "karta", "putovanje", "pruga"],
    ("prevoz", "tramvaj"): ["šine", "stanica", "grad", "gužva"],
    ("prevoz", "trolejbus"): ["žice", "stanica", "grad", "karta"],
    ("prevoz", "taksi vozilo"): ["adresa", "aplikacija", "noć", "vožnja"],
    ("prevoz", "motocikl"): ["kaciga", "vjetar", "buka", "cesta"],
    ("prevoz", "skuter"): ["grad", "kaciga", "parking", "dostava"],
    ("prevoz", "bicikl za prevoz"): ["pedale", "park", "lanac", "vožnja"],
    ("prevoz", "kamion"): ["teret", "autocesta", "gorivo", "kabina"],
    ("prevoz", "kombi"): ["teret", "porodica", "parking", "put"],
    ("prevoz", "traktor"): ["selo", "polje", "blato", "sporo"],
    ("prevoz", "avion"): ["aerodrom", "kofer", "nebo", "karta"],
    ("prevoz", "helikopter"): ["nebo", "buka", "propeler", "spasavanje"],
    ("prevoz", "brod"): ["more", "luka", "paluba", "putovanje"],
    ("prevoz", "camac"): ["rijeka", "veslo", "obala", "voda"],
    ("prevoz", "trajektna linija"): ["luka", "auta", "paluba", "more"],
    ("prevoz", "metro"): ["podzemlje", "stanica", "karta", "grad"],
    ("prevoz", "stanica"): ["čekanje", "tabla", "karta", "gužva"],
    ("prevoz", "autobusno stajaliste"): ["klupa", "red vožnje", "jutro", "kiša"],
    ("prevoz", "kolodvor za prevoz"): ["peron", "karta", "kofer", "čekanje"],
    ("prevoz", "terminal"): ["gejt", "kofer", "tabla", "red"],
    ("prevoz", "cesta"): ["asfalt", "auto", "krivina", "putovanje"],
    ("prevoz", "ulica"): ["semafor", "pješaci", "parkirana auta", "grad"],
    ("prevoz", "izlaz s autoceste"): ["tabla", "traka", "skretanje", "putarina"],
    ("prevoz", "prometni semafor"): ["raskrsnica", "crveno", "pješaci", "grad"],
    ("prevoz", "pjesacki prijelaz"): ["zebra", "semafor", "pješaci", "škola"],
    ("prevoz", "kruzni tok"): ["raskrsnica", "grad", "skretanje", "vozač"],
    ("prevoz", "most na cesti"): ["rijeka", "ograda", "auto", "pogled"],
    ("prevoz", "cestovni tunel"): ["mrak", "cesta", "svjetla", "planina"],
    ("prevoz", "parkiraliste"): ["auto", "mjesto", "kazna", "grad"],
    ("prevoz", "garaza za auto"): ["parking", "ulaz", "beton", "ključ"],
    ("prevoz", "volan"): ["ruke", "auto", "skretanje", "vožnja"],
    ("prevoz", "kocnica"): ["stopalo", "semafor", "naglo", "auto"],
    ("prevoz", "gas"): ["pedala", "ubrzanje", "auto", "cesta"],
    ("prevoz", "mjenjac"): ["auto", "ruka", "brzina", "vožnja"],
    ("prevoz", "guma"): ["točak", "asfalt", "pumpa", "rezerva"],
    ("prevoz", "rezervna guma"): ["prtljažnik", "alat", "put", "problem"],
    ("prevoz", "motor vozila"): ["auto", "ulje", "buka", "garaža"],
    ("prevoz", "prtljaznik"): ["kofer", "auto", "poklopac", "put"],
    ("prevoz", "sjediste"): ["pojas", "prozor", "vožnja", "putnik"],
    ("prevoz", "pojas"): ["sjedalo", "sigurnost", "kopča", "auto"],
    ("prevoz", "kaciga za motor"): ["glava", "motor", "vožnja", "sigurnost"],
    ("prevoz", "mjesecna karta"): ["tramvaj", "novčanik", "kontrola", "mjesec"],
    ("prevoz", "vozni red"): ["stanica", "vrijeme", "tabla", "čekanje"],
    ("prevoz", "putnik"): ["kofer", "karta", "stanica", "sjedalo"],
    ("prevoz", "vozac autobusa"): ["volan", "stanica", "smjena", "putnici"],
    ("prevoz", "kontrolor"): ["karta", "tramvaj", "uniforma", "provjera"],
    ("prevoz", "kondukter"): ["vlak", "karta", "hodnik", "putnici"],
    ("prevoz", "guzva u prometu"): ["kolona", "sirena", "jutro", "nervoza"],
    ("prevoz", "kolona"): ["gužva", "auta", "čekanje", "granica"],
    ("prevoz", "skretanje"): ["raskrsnica", "grad", "žmigavac", "vozač"],
    ("prevoz", "raskrizje"): ["semafor", "pješaci", "skretanje", "grad"],
    ("prevoz", "benzinska postaja"): ["pumpa", "auto", "račun", "miris"],
    ("prevoz", "gorivo"): ["pumpa", "auto", "put", "cijena"],
    ("prevoz", "benzin"): ["pumpa", "auto", "cijena", "miris"],
    ("prevoz", "dizel"): ["pumpa", "kamion", "miris", "cijena"],
    ("prevoz", "elektricni auto"): ["punjenje", "kabl", "parking", "tišina"],
    ("prevoz", "punjac za auto"): ["kabl", "parking", "struja", "stanica"],
    ("prevoz", "navigacija u autu"): ["mapa", "telefon", "raskrsnica", "adresa"],
    ("prevoz", "retrovizor"): ["pogled", "auto", "staklo", "traka"],
    ("prevoz", "brisaci"): ["kiša", "staklo", "vožnja", "ručica"],
    ("prevoz", "far"): ["noć", "cesta", "svjetlo", "auto"],
    ("prevoz", "sirena"): ["buka", "gužva", "upozorenje", "ulica"],
    ("prevoz", "tablica"): ["auto", "parking", "policija", "brojevi"],
    ("prevoz", "taxi aplikacija"): ["telefon", "adresa", "vožnja", "noć"],
    ("prevoz", "pruga"): ["šine", "peron", "vlak", "putovanje"],
    ("prevoz", "tracnice"): ["vlak", "peron", "metal", "stanica"],
    ("prevoz", "peron za voz"): ["stanica", "pruga", "karta", "čekanje"],
    ("prevoz", "brodska luka"): ["more", "brodovi", "obala", "putnici"],

    ("sport", "nogomet"): ["stadion", "lopta", "navijanje", "gol"],
    ("sport", "kosarka"): ["parket", "obruč", "patike", "utakmica"],
    ("sport", "rukomet"): ["dvorana", "lopta", "gol", "ekipa"],
    ("sport", "odbojka"): ["mreža", "dvorana", "servis", "ekipa"],
    ("sport", "tenis"): ["reket", "mreža", "teren", "servis"],
    ("sport", "stolni tenis"): ["mali reket", "stol", "loptica", "brzina"],
    ("sport", "plivanje"): ["bazen", "voda", "staza", "trening"],
    ("sport", "trcanje"): ["staza", "patike", "znoj", "jutro"],
    ("sport", "biciklizam"): ["cesta", "pedale", "kaciga", "trka"],
    ("sport", "skijanje"): ["snijeg", "staza", "planina", "kaciga"],
    ("sport", "klizanje"): ["led", "dvorana", "ravnoteža", "zima"],
    ("sport", "boks"): ["ring", "rukavice", "znoj", "sudija"],
    ("sport", "karate"): ["kimono", "pojas", "dvorana", "pokret"],
    ("sport", "judo"): ["tatami", "kimono", "pojas", "borba"],
    ("sport", "gimnastika"): ["strunjača", "dvorana", "ravnoteža", "publika"],
    ("sport", "atletika"): ["stadion", "staza", "trening", "start"],
    ("sport", "golf"): ["trava", "palica", "rupa", "mir"],
    ("sport", "sah"): ["tišina", "tabla", "potez", "koncentracija"],
    ("sport", "biljar"): ["stol", "kugle", "kreda", "pub"],
    ("sport", "pikado"): ["meta", "strelica", "koncentracija", "pub"],
    ("sport", "lopta"): ["teren", "ruke", "noge", "igra"],
    ("sport", "gol"): ["mreža", "stadion", "navijanje", "lopta"],
    ("sport", "kos"): ["obruč", "parket", "šut", "patike"],
    ("sport", "mreza"): ["teren", "servis", "lopta", "granica"],
    ("sport", "reket"): ["teren", "servis", "ruka", "loptica"],
    ("sport", "palica"): ["teren", "lopta", "udarac", "oprema"],
    ("sport", "kopacke"): ["trava", "svlačionica", "pertle", "utakmica"],
    ("sport", "tenisice"): ["vezice", "trening", "parket", "torba"],
    ("sport", "dres"): ["svlačionica", "broj", "ekipa", "utakmica"],
    ("sport", "trener"): ["plan", "ekipa", "zviždaljka", "savjet"],
    ("sport", "sudac"): ["zviždaljka", "pravila", "teren", "utakmica"],
    ("sport", "navijac"): ["tribina", "šal", "pjesma", "stadion"],
    ("sport", "stadion"): ["tribine", "navijanje", "teren", "reflektori"],
    ("sport", "dvorana"): ["parket", "publika", "svjetla", "znoj"],
    ("sport", "teren"): ["linije", "lopta", "trening", "ekipa"],
    ("sport", "utakmica"): ["teren", "navijanje", "ekipa", "rezultat"],
    ("sport", "trening"): ["znoj", "oprema", "plan", "ponavljanje"],
    ("sport", "medalja"): ["postolje", "takmičenje", "vrpca", "ponos"],
    ("sport", "pecat pobjede"): ["trofej", "slavlje", "finale", "uspomena"],
    ("sport", "semafor"): ["rezultat", "dvorana", "utakmica", "svjetla"],
    ("sport", "zvizdaljka"): ["sudija", "prekid", "pravila", "teren"],
    ("sport", "kaciga za sport"): ["glava", "brzina", "oprema", "sigurnost"],
    ("sport", "stitnici"): ["koljena", "oprema", "trening", "torba"],
    ("sport", "rukavice"): ["ring", "trening", "oprema", "torba"],
    ("sport", "skateboard"): ["park", "rampa", "trik", "točkovi"],
    ("sport", "surfanje"): ["talasi", "daska", "more", "ravnoteža"],
    ("sport", "vaterpolo"): ["bazen", "lopta", "gol", "kapica"],
    ("sport", "kuglanje"): ["kugla", "staza", "čunjevi", "dvorana"],
    ("sport", "planinarenje"): ["ruksak", "staza", "vrh", "umor"],
    ("sport", "ronjenje"): ["voda", "maska", "dubina", "peraje"],
    ("sport", "jedrenje"): ["more", "vjetar", "jedro", "luka"],
    ("sport", "maraton"): ["duga staza", "broj", "voda", "publika"],
    ("sport", "sprint"): ["start", "staza", "brzina", "dah"],
    ("sport", "skok u dalj"): ["pijesak", "zalet", "atletika", "mjerenje"],
    ("sport", "skok u vis"): ["letvica", "strunjača", "zalet", "atletika"],
    ("sport", "bacanje kugle"): ["krug", "težina", "atletika", "mjerenje"],
    ("sport", "kladivo"): ["atletika", "bacanje", "teren", "mjerenje"],
    ("sport", "disk"): ["bacanje", "atletika", "krug", "mjerenje"],
    ("sport", "bazen"): ["voda", "staza", "peškir", "trening"],
    ("sport", "svlacionica"): ["dres", "klupa", "torba", "priprema"],
    ("sport", "tabela"): ["bodovi", "klubovi", "sezona", "rezultat"],
    ("sport", "liga"): ["sezona", "tabela", "klub", "utakmica"],
    ("sport", "kup"): ["trofej", "finale", "ekipa", "slavlje"],
    ("sport", "kapetan"): ["traka", "ekipa", "svlačionica", "vođstvo"],
    ("sport", "rezerva"): ["klupa", "trener", "dres", "utakmica"],
    ("sport", "napad"): ["gol", "pritisak", "teren", "ekipa"],
    ("sport", "obrana"): ["gol", "ekipa", "teren", "blok"],
    ("sport", "pobjeda"): ["slavlje", "ekipa", "rezultat", "svlačionica"],
    ("sport", "poraz"): ["svlačionica", "tišina", "rezultat", "razočaranje"],
    ("sport", "nerijeseno"): ["rezultat", "semafor", "kraj", "utakmica"],
    ("sport", "penal"): ["golman", "tačka", "stadion", "pritisak"],
    ("sport", "aut"): ["linija", "teren", "lopta", "prekid"],
})

CATEGORY_EXACT_HINT_POOLS.update({
    # Batch 2B: reviewed Zdravlje, Tehnologija and Posao medium entries.
    ("zdravlje", "zdravlje"): ["odmor", "navika", "šetnja", "san"],
    ("zdravlje", "lijecnik opce prakse"): ["čekaonica", "termin", "bijeli mantil", "recept"],
    ("zdravlje", "doktorica"): ["ordinacija", "pregled", "termin", "stetoskop"],
    ("zdravlje", "ambulanta"): ["čekaonica", "pregled", "termin", "bijeli mantil"],
    ("zdravlje", "ordinacija"): ["čekaonica", "pregled", "stolica", "termin"],
    ("zdravlje", "bolnica"): ["hodnik", "posjeta", "čekaonica", "bijeli mantil"],
    ("zdravlje", "ljekarna"): ["recept", "red", "tablete", "savjet"],
    ("zdravlje", "lijek"): ["apoteka", "recept", "kutija", "čaša vode"],
    ("zdravlje", "tableta"): ["čaša vode", "kutija", "jutro", "apoteka"],
    ("zdravlje", "sirup"): ["kašika", "grlo", "zima", "dijete"],
    ("zdravlje", "vitamin"): ["doručak", "bočica", "energija", "apoteka"],
    ("zdravlje", "toplomjer"): ["temperatura", "krevet", "zima", "čelo"],
    ("zdravlje", "zavoj"): ["ruka", "torbica", "prva pomoć", "rana"],
    ("zdravlje", "flaster"): ["prst", "rana", "torbica", "djeca"],
    ("zdravlje", "maska"): ["lice", "apoteka", "autobus", "čekaonica"],
    ("zdravlje", "rukavice medicinske"): ["pregled", "ordinacija", "maska", "higijena"],
    ("zdravlje", "pregled"): ["čekaonica", "termin", "stolica", "pitanja"],
    ("zdravlje", "recept"): ["apoteka", "papir", "doktor", "red"],
    ("zdravlje", "kontrola"): ["termin", "rezultat", "ordinacija", "pitanja"],
    ("zdravlje", "cekaonica"): ["pregled", "termin", "mantil", "red"],
    ("zdravlje", "zubar"): ["stolica", "osmijeh", "četkica", "svjetlo"],
    ("zdravlje", "cetkica za zube"): ["jutro", "kupatilo", "pasta", "osmijeh"],
    ("zdravlje", "pasta za zube"): ["četkica", "kupatilo", "jutro", "osmijeh"],
    ("zdravlje", "zub"): ["osmijeh", "četkica", "bol", "pasta"],
    ("zdravlje", "oko"): ["pogled", "naočale", "svjetlo", "lice"],
    ("zdravlje", "uho"): ["zvuk", "slušalice", "muzika", "tišina"],
    ("zdravlje", "nos"): ["maramica", "miris", "prehlada", "kihanje"],
    ("zdravlje", "grlo"): ["čaj", "zima", "glas", "šal"],
    ("zdravlje", "ruka"): ["sat", "dlan", "rukav", "pozdrav"],
    ("zdravlje", "noga"): ["šetnja", "patika", "koljeno", "stepenice"],
    ("zdravlje", "leda"): ["stolica", "jastuk", "masaža", "sjedenje"],
    ("zdravlje", "glava"): ["kapa", "jastuk", "misli", "bol"],
    ("zdravlje", "srce"): ["emocija", "trčanje", "grudi", "ritam"],
    ("zdravlje", "stomak"): ["ručak", "čaj", "pojas", "mir"],
    ("zdravlje", "koza"): ["krema", "sunce", "ruka", "dodir"],
    ("zdravlje", "kosa"): ["češalj", "šampon", "ogledalo", "jutro"],
    ("zdravlje", "san"): ["noć", "jastuk", "tišina", "odmor"],
    ("zdravlje", "kratak odmor"): ["pauza", "kauč", "voda", "tišina"],
    ("zdravlje", "casa vode"): ["stol", "jutro", "trening", "pauza"],
    ("zdravlje", "setnja"): ["park", "koraci", "zrak", "veče"],
    ("zdravlje", "lagano trcanje"): ["park", "patike", "jutro", "dah"],
    ("zdravlje", "vjezba"): ["prostirka", "trening", "znoj", "rutina"],
    ("zdravlje", "teretana"): ["tegovi", "ogledalo", "znoj", "trening"],
    ("zdravlje", "joga"): ["prostirka", "tišina", "disanje", "jutro"],
    ("zdravlje", "disanje"): ["mir", "zrak", "pauza", "ritam"],
    ("zdravlje", "temperatura"): ["čelo", "krevet", "zima", "toplomjer"],
    ("zdravlje", "kasalj"): ["grlo", "zima", "čaj", "noć"],
    ("zdravlje", "prehlada"): ["zima", "čaj", "maramice", "krevet"],
    ("zdravlje", "alergija"): ["proljeće", "kihanje", "polen", "apoteka"],
    ("zdravlje", "kapi za nos"): ["prehlada", "maramica", "bočica", "jutro"],
    ("zdravlje", "krema"): ["koža", "ruka", "sunce", "apoteka"],
    ("zdravlje", "masaza"): ["opuštanje", "stol", "ulje", "termin"],
    ("zdravlje", "fizioterapija"): ["vježba", "termin", "leđa", "strunjača"],
    ("zdravlje", "naocale za vid"): ["knjiga", "ekran", "okvir", "pogled"],
    ("zdravlje", "leca"): ["oko", "kutijica", "ogledalo", "jutro"],
    ("zdravlje", "sluh"): ["uho", "zvuk", "tišina", "muzika"],
    ("zdravlje", "puls"): ["zglob", "sat", "ritam", "trčanje"],
    ("zdravlje", "tlak"): ["pregled", "manžeta", "mir", "doktor"],
    ("zdravlje", "prehrana"): ["tanjir", "navika", "povrće", "energija"],
    ("zdravlje", "svjeze voce"): ["doručak", "zdjela", "pijaca", "boje"],
    ("zdravlje", "svjeze povrce"): ["salata", "pijaca", "ručak", "daska"],
    ("zdravlje", "zdrav dorucak"): ["jutro", "zob", "voće", "čaša"],
    ("zdravlje", "caj za grlo"): ["zima", "šolja", "med", "glas"],
    ("zdravlje", "med za grlo"): ["kašika", "čaj", "zima", "tegla"],
    ("zdravlje", "sapunjanje"): ["kupatilo", "voda", "tuš", "peškir"],
    ("zdravlje", "higijena"): ["kupatilo", "sapun", "ručnik", "navika"],
    ("zdravlje", "tusiranje"): ["kupatilo", "para", "ručnik", "večer"],
    ("zdravlje", "rucnik za zdravlje"): ["tuš", "kupatilo", "voda", "torba"],
    ("zdravlje", "dezinfekcija"): ["ruke", "bočica", "ulaz", "miris"],
    ("zdravlje", "prva pomoc"): ["torbica", "flaster", "zavoj", "izlet"],

    ("tehnologija", "racunalo"): ["tastatura", "posao", "ekran", "stol"],
    ("tehnologija", "laptop"): ["posao", "torba", "tastatura", "sastanak"],
    ("tehnologija", "tablet"): ["kauč", "ekran", "crtanje", "putovanje"],
    ("tehnologija", "mobitel"): ["poruka", "džep", "aplikacija", "punjač"],
    ("tehnologija", "telefon"): ["poziv", "broj", "slušalica", "razgovor"],
    ("tehnologija", "ekran"): ["film", "svjetlo", "prst", "stol"],
    ("tehnologija", "tipkovnica"): ["tipkanje", "stol", "laptop", "kafa"],
    ("tehnologija", "mis za racunar"): ["stol", "klik", "podloga", "tastatura"],
    ("tehnologija", "kamera"): ["slika", "putovanje", "uspomena", "objektiv"],
    ("tehnologija", "slusalice"): ["muzika", "autobus", "šetnja", "kabl"],
    ("tehnologija", "zvucnik"): ["muzika", "soba", "glasnoća", "zabava"],
    ("tehnologija", "mikrofon"): ["glas", "snimanje", "podkast", "stol"],
    ("tehnologija", "punjac za uredaj"): ["utičnica", "kabl", "noćni ormarić", "baterija"],
    ("tehnologija", "baterija"): ["punjenje", "daljinski", "telefon", "struja"],
    ("tehnologija", "kabel"): ["utičnica", "stol", "punjenje", "torba"],
    ("tehnologija", "usb"): ["laptop", "fajl", "priključak", "torba"],
    ("tehnologija", "internet"): ["pretraga", "poruka", "Wi-Fi", "stranica"],
    ("tehnologija", "wi-fi"): ["stan", "lozinka", "signal", "ruter"],
    ("tehnologija", "lozinka"): ["polje", "prijava", "bilješka", "zaborav"],
    ("tehnologija", "aplikacija"): ["telefon", "ikonica", "poruka", "ekran"],
    ("tehnologija", "poruka"): ["notifikacija", "telefon", "chat", "večer"],
    ("tehnologija", "poziv"): ["broj", "slušalica", "glas", "vibracija"],
    ("tehnologija", "video poziv"): ["kamera", "sastanak", "ekran", "glas"],
    ("tehnologija", "fotografija"): ["uspomena", "album", "kamera", "putovanje"],
    ("tehnologija", "snimka"): ["kamera", "glas", "datoteka", "uspomena"],
    ("tehnologija", "datoteka"): ["folder", "laptop", "slanje", "posao"],
    ("tehnologija", "mapa na racunaru"): ["fajlovi", "radna površina", "ikona", "posao"],
    ("tehnologija", "printer"): ["papir", "ured", "dokument", "tinta"],
    ("tehnologija", "skener"): ["papir", "ured", "dokument", "svjetlo"],
    ("tehnologija", "router"): ["Wi-Fi", "stan", "lozinka", "signal"],
    ("tehnologija", "server"): ["podaci", "fajlovi", "internet", "backup"],
    ("tehnologija", "cloud servis"): ["fajlovi", "backup", "internet", "pristup"],
    ("tehnologija", "preglednik"): ["stranica", "tab", "pretraga", "adresa"],
    ("tehnologija", "web stranica"): ["link", "preglednik", "klik", "adresa"],
    ("tehnologija", "link"): ["poruka", "klik", "stranica", "slanje"],
    ("tehnologija", "profil"): ["slika", "ime", "mreža", "podešavanja"],
    ("tehnologija", "avatar"): ["profil", "slika", "igrica", "nadimak"],
    ("tehnologija", "emoji"): ["poruka", "smijeh", "chat", "reakcija"],
    ("tehnologija", "igrica"): ["kontroler", "ekran", "večer", "ekipa"],
    ("tehnologija", "konzola"): ["televizor", "kontroler", "kauč", "igrica"],
    ("tehnologija", "kontroler"): ["dugmad", "kauč", "igrica", "ruke"],
    ("tehnologija", "pametni televizor"): ["kauč", "film", "aplikacija", "daljinski"],
    ("tehnologija", "daljinski za tv"): ["kauč", "dugmad", "televizor", "večer"],
    ("tehnologija", "pametni sat"): ["zglob", "koraci", "notifikacija", "punjenje"],
    ("tehnologija", "dron"): ["nebo", "kamera", "daljinski", "buka"],
    ("tehnologija", "robot"): ["fabrika", "program", "pokret", "budućnost"],
    ("tehnologija", "cip"): ["ploča", "mali dio", "struja", "krug"],
    ("tehnologija", "azuriranje"): ["čekanje", "restart", "aplikacija", "procenat"],
    ("tehnologija", "signal"): ["antena", "crtice", "telefon", "slab domet"],
    ("tehnologija", "racunalna mreza"): ["kablovi", "ured", "server", "veza"],
    ("tehnologija", "bluetooth"): ["slušalice", "uparivanje", "telefon", "zvučnik"],
    ("tehnologija", "navigacija digitalna"): ["auto", "ruta", "glas", "mapa"],
    ("tehnologija", "gps"): ["mapa", "auto", "lokacija", "put"],
    ("tehnologija", "mapa u telefonu"): ["ruta", "grad", "lokacija", "šetnja"],
    ("tehnologija", "ekran osjetljiv na dodir"): ["prst", "telefon", "ikonica", "staklo"],
    ("tehnologija", "notifikacija"): ["zvuk", "ekran", "poruka", "vibracija"],
    ("tehnologija", "alarm"): ["jutro", "zvuk", "sat", "buđenje"],
    ("tehnologija", "kalendar u telefonu"): ["datum", "rok", "podsjetnik", "plan"],
    ("tehnologija", "biljeska"): ["telefon", "ideja", "lista", "podsjetnik"],
    ("tehnologija", "pretraga"): ["pitanje", "preglednik", "rezultati", "tipkanje"],
    ("tehnologija", "kod"): ["programiranje", "ekran", "lozinka", "greška"],
    ("tehnologija", "lozinka za wi-fi"): ["ruter", "gosti", "papirić", "signal"],
    ("tehnologija", "snimanje"): ["kamera", "glas", "crvena tačka", "uspomena"],
    ("tehnologija", "streaming"): ["film", "internet", "kauč", "serija"],
    ("tehnologija", "podcast"): ["slušalice", "epizoda", "glas", "šetnja"],
    ("tehnologija", "selfie"): ["kamera", "lice", "ruka", "uspomena"],
    ("tehnologija", "filter za sliku"): ["kamera", "boje", "profil", "objava"],
    ("tehnologija", "memorija"): ["fajlovi", "telefon", "prostor", "backup"],
    ("tehnologija", "procesor"): ["brzina", "laptop", "ploča", "toplina"],
    ("tehnologija", "tvrdi disk"): ["fajlovi", "backup", "laptop", "prostor"],
    ("tehnologija", "monitor"): ["stol", "ekran", "kabl", "posao"],
    ("tehnologija", "projektor"): ["zid", "mrak", "prezentacija", "sastanak"],

    ("posao", "posao"): ["jutro", "kafa", "rok", "sastanak"],
    ("posao", "ured"): ["stol", "računar", "pauza", "sastanak"],
    ("posao", "radni stol"): ["laptop", "papiri", "kafa", "rok"],
    ("posao", "sastanak"): ["kafa", "stol", "plan", "kolege"],
    ("posao", "pauza"): ["kafa", "hodnik", "razgovor", "sendvič"],
    ("posao", "kolega"): ["tim", "kafa", "poruka", "rok"],
    ("posao", "kolegica"): ["tim", "kafa", "poruka", "rok"],
    ("posao", "sef"): ["kancelarija", "odluka", "sastanak", "rok"],
    ("posao", "direktor"): ["ured", "sastanak", "odluka", "potpis"],
    ("posao", "radnik"): ["smjena", "alat", "pauza", "jutro"],
    ("posao", "radnica"): ["smjena", "tim", "pauza", "jutro"],
    ("posao", "lijecnik"): ["pregled", "čekaonica", "bijeli mantil", "termin"],
    ("posao", "medicinska sestra"): ["ordinacija", "smjena", "pacijenti", "uniforma"],
    ("posao", "uciteljica"): ["razred", "tabla", "dnevnik", "ocjena"],
    ("posao", "profesorica"): ["učionica", "ispit", "tabla", "dnevnik"],
    ("posao", "inzenjer"): ["nacrt", "projekt", "kaciga", "sastanak"],
    ("posao", "programer"): ["kod", "laptop", "kafa", "bug"],
    ("posao", "dizajner"): ["boje", "ekran", "skica", "klijent"],
    ("posao", "konobar"): ["restoran", "kafa", "miris", "večer"],
    ("posao", "kuhar"): ["tava", "restoran", "miris", "večera"],
    ("posao", "pekar"): ["brašno", "peć", "jutro", "miris"],
    ("posao", "vozac"): ["volan", "cesta", "smjena", "gorivo"],
    ("posao", "policajac"): ["uniforma", "ulica", "zviždaljka", "patrola"],
    ("posao", "vatrogasac"): ["sirena", "kaciga", "crijevo", "ekipa"],
    ("posao", "postar"): ["pismo", "zgrada", "torba", "adresa"],
    ("posao", "frizer"): ["ogledalo", "škare", "stolica", "termin"],
    ("posao", "krojac"): ["igla", "tkanina", "mjera", "mašina"],
    ("posao", "stolar"): ["drvo", "radionica", "pila", "namještaj"],
    ("posao", "vodoinstalater"): ["cijev", "kupatilo", "alat", "voda"],
    ("posao", "elektricar"): ["kabl", "utičnica", "alat", "struja"],
    ("posao", "mehanicar"): ["garaža", "alat", "auto", "ulje"],
    ("posao", "prodavac"): ["kasa", "polica", "kupac", "smjena"],
    ("posao", "blagajnik"): ["kasa", "račun", "red", "novac"],
    ("posao", "cistac"): ["metla", "kanta", "pod", "jutro"],
    ("posao", "zastitar"): ["ulaz", "kamera", "uniforma", "noć"],
    ("posao", "novinar"): ["pitanja", "kamera", "članak", "rok"],
    ("posao", "fotograf"): ["kamera", "svjetlo", "slika", "vjenčanje"],
    ("posao", "glumac"): ["scena", "uloga", "kamera", "publika"],
    ("posao", "pjevac"): ["mikrofon", "pozornica", "pjesma", "publika"],
    ("posao", "slikar"): ["boje", "platno", "četka", "atelje"],
    ("posao", "vrtlar"): ["zemlja", "biljke", "alat", "dvorište"],
    ("posao", "poljoprivrednik"): ["njiva", "traktor", "selo", "sezona"],
    ("posao", "ribar"): ["mreža", "čamac", "jutro", "voda"],
    ("posao", "pilot"): ["kokpit", "nebo", "aerodrom", "uniforma"],
    ("posao", "stjuardesa"): ["avion", "putnici", "kolica", "osmijeh"],
    ("posao", "odvjetnik"): ["sud", "dokumenti", "odijelo", "sastanak"],
    ("posao", "sudac na poslu"): ["sudnica", "pravila", "odluka", "čekić"],
    ("posao", "racunovoda"): ["brojevi", "račun", "tabela", "rok"],
    ("posao", "tajnica"): ["telefon", "raspored", "ured", "poruke"],
    ("posao", "recepcija"): ["pult", "gosti", "telefon", "osmijeh"],
    ("posao", "vizitka"): ["sastanak", "džep", "ime", "kontakt"],
    ("posao", "ugovor"): ["potpis", "dokument", "sastanak", "pravila"],
    ("posao", "placa"): ["mjesec", "banka", "račun", "posao"],
    ("posao", "radno vrijeme"): ["smjena", "sat", "raspored", "pauza"],
    ("posao", "smjena"): ["raspored", "kolege", "jutro", "umor"],
    ("posao", "uniforma"): ["smjena", "ormar", "pravila", "identitet"],
    ("posao", "kaciga na gradilistu"): ["gradilište", "glava", "sigurnost", "prašina"],
    ("posao", "alat"): ["radionica", "popravka", "majstor", "garaža"],
    ("posao", "kutija za alat"): ["radionica", "garaža", "šarafi", "popravka"],
    ("posao", "laptop za posao"): ["sastanak", "torba", "mail", "rok"],
    ("posao", "sluzbeni mobitel"): ["poziv", "poruka", "rok", "džep"],
    ("posao", "e-mail"): ["inbox", "rok", "odgovor", "sastanak"],
    ("posao", "dokument"): ["papir", "folder", "potpis", "ured"],
    ("posao", "pecat"): ["dokument", "tinta", "šalter", "potpis"],
    ("posao", "potpis"): ["papir", "olovka", "ugovor", "sastanak"],
    ("posao", "kalendar"): ["datum", "rok", "zid", "plan"],
    ("posao", "rok"): ["datum", "stres", "kafa", "plan"],
    ("posao", "plan"): ["tabla", "sastanak", "bilješke", "cilj"],
    ("posao", "zadatak"): ["lista", "rok", "tim", "laptop"],
    ("posao", "tim"): ["dogovor", "sastanak", "poruke", "zajedno"],
    ("posao", "kava na poslu"): ["pauza", "šoljica", "kolege", "jutro"],
    ("posao", "kopirni uredaj"): ["papir", "ured", "dugme", "dokument"],
})

WORD_RENAMES = {
    ("Zabava", "Glavni vokal", "glavni vokal"): ("Vokal", "vokal"),
    ("Zabava", "Karaoke mikrofon", "karaoke mikrofon"): ("Mikrofon za karaoke", "mikrofon za karaoke"),
    ("Zabava", "Maska za maskenbal", "maska za maskenbal"): ("Karnevalska maska", "karnevalska maska"),
    ("Zabava", "Knjiga za odmor", "knjiga za odmor"): ("Roman za odmor", "roman za odmor"),
    ("Zabava", "Park za zabavu", "zabavni park"): ("Zabavni park", "zabavni park"),
    ("Zabava", "Kokice u kinu", "kokice u bioskopu"): ("Kokice za kino", "kokice za bioskop"),
    ("Zabava", "Sjedalo u kinu", "sedište u bioskopu"): ("Kino sjedalo", "bioskopsko sedište"),
    ("Zabava", "Audio emisija", "audio emisija"): ("Audio emisija", "audio emisija"),
    ("Balkan", "Kava u kafani", "kafa u kafani"): ("Kafa u kafani", "kafa u kafani"),
    ("Balkan", "Roštilj u dvorištu", "roštilj u dvorištu"): ("Dvorišni roštilj", "dvorišni roštilj"),
    ("Balkan", "Sarma za praznik", "sarma za praznik"): ("Sarma za praznik", "sarma za praznik"),
    ("Balkan", "Ajvar iz zimnice", "ajvar iz zimnice"): ("Domaći ajvar", "domaći ajvar"),
    ("Balkan", "Vinograd za berbu", "vinograd za berbu"): ("Vinograd za berbu", "vinograd za berbu"),
    ("Balkan", "Kajmak na stolu", "kajmak na stolu"): ("Kajmak na stolu", "kajmak na stolu"),
    ("Balkan", "Dnevnik na TV-u", "dnevnik na TV-u"): ("TV dnevnik", "TV dnevnik"),
    ("Balkan", "Daljinski kod kuće", "daljinski kod kuće"): ("Daljinski", "daljinski"),
    ("Balkan", "Jadransko more", "Jadransko more"): ("Jadran", "Jadran"),
    ("Odeća", "Sat na ruci", "ručni sat"): ("Ručni sat", "ručni sat"),
    ("Odeća", "Ormar za odjeću", "ormar za odeću"): ("Ormar", "orman"),
    ("Odeća", "Ogledalo za oblačenje", "ogledalo za oblačenje"): ("Ogledalo za odjeću", "ogledalo za odeću"),
    ("Odeća", "Maska za lice", "maska za lice"): ("Zaštitna maska", "zaštitna maska"),
    ("Odeća", "Svečana kravata", "svečana kravata"): ("Kravata svečana", "svečana kravata"),
    ("Škola", "Stolica u učionici", "stolica u učionici"): ("Školska stolica", "školska stolica"),
    ("Škola", "Spužva za tablu", "sunđer za tablu"): ("Spužva za tablu", "sunđer za tablu"),
    ("Škola", "Torba za školu", "školska torba"): ("Školska torba", "školska torba"),
    ("Škola", "Ruksak za školu", "školski ranac"): ("Školski ruksak", "školski ranac"),
    ("Škola", "Zvono za školu", "školsko zvono"): ("Školsko zvono", "školsko zvono"),
    ("Škola", "Dvorana za tjelesni", "sala za fizičko"): ("Sportska dvorana", "sala za fizičko"),
    ("Škola", "Hodnik škole", "školski hodnik"): ("Školski hodnik", "školski hodnik"),
}

CATEGORY_EXACT_HINT_POOLS.update({
    # Batch 2C: reviewed Zabava, Balkan, Odeća, Škola, Hrana and Životinje.
    ("zabava", "film"): ["kokice", "mrak", "kauč", "večer"],
    ("zabava", "serija"): ["epizoda", "kauč", "Netflix", "vikend"],
    ("zabava", "kino"): ["kokice", "film", "mrak", "platno"],
    ("zabava", "kazaliste"): ["scena", "publika", "glumci", "aplauz"],
    ("zabava", "koncert"): ["publika", "svjetla", "muzika", "večer"],
    ("zabava", "glazba"): ["radio", "slušalice", "ples", "društvo"],
    ("zabava", "pjesma"): ["radio", "glas", "refren", "društvo"],
    ("zabava", "vokal"): ["mikrofon", "scena", "pjesma", "publika"],
    ("zabava", "bend"): ["proba", "gitara", "bubanj", "koncert"],
    ("zabava", "gitara"): ["pjesma", "žica", "koncert", "društvo"],
    ("zabava", "klavir"): ["tipke", "sala", "melodija", "koncert"],
    ("zabava", "bubanj"): ["ritam", "palice", "bend", "buka"],
    ("zabava", "ples"): ["muzika", "svadba", "pokret", "noć"],
    ("zabava", "zabava"): ["društvo", "muzika", "smijeh", "večer"],
    ("zabava", "rodendan"): ["torta", "poklon", "svijeće", "slavlje"],
    ("zabava", "poklon"): ["rođendan", "iznenađenje", "slavlje", "kutija"],
    ("zabava", "balon"): ["rođendan", "helij", "boje", "djeca"],
    ("zabava", "torta"): ["svijeće", "rođendan", "slatko", "rezanje"],
    ("zabava", "svijeca"): ["rođendan", "plamen", "torta", "večer"],
    ("zabava", "drustvena igra"): ["smijeh", "ekipa", "večer", "izazov"],
    ("zabava", "karte za igru"): ["stol", "društvo", "blef", "večer"],
    ("zabava", "kockica"): ["stol", "bacanje", "igra", "brojevi"],
    ("zabava", "puzzle"): ["stol", "komadići", "strpljenje", "slika"],
    ("zabava", "kviz"): ["pitanje", "ekipa", "znanje", "bodovi"],
    ("zabava", "karaoke"): ["mikrofon", "pjesma", "društvo", "smijeh"],
    ("zabava", "mikrofon za karaoke"): ["pjesma", "ruka", "scena", "glas"],
    ("zabava", "scena"): ["svjetla", "publika", "zastor", "nastup"],
    ("zabava", "publika"): ["aplauz", "sjedala", "scena", "čekanje"],
    ("zabava", "aplauz"): ["publika", "kraj", "scena", "dlanovi"],
    ("zabava", "ulaznica"): ["red", "koncert", "džep", "kontrola"],
    ("zabava", "maskenbal"): ["kostim", "maska", "muzika", "noć"],
    ("zabava", "karnevalska maska"): ["kostim", "lice", "karneval", "noć"],
    ("zabava", "strip"): ["crtež", "junak", "stranice", "oblačići"],
    ("zabava", "roman za odmor"): ["kauč", "stranice", "tišina", "vikend"],
    ("zabava", "roman"): ["priča", "stranice", "kauč", "večer"],
    ("zabava", "casopis"): ["naslovnica", "kafić", "slike", "vikend"],
    ("zabava", "hobi"): ["vikend", "radost", "slobodno vrijeme", "ekipa"],
    ("zabava", "crtanje"): ["papir", "olovka", "boje", "mir"],
    ("zabava", "likovna radionica"): ["boje", "stol", "četkice", "društvo"],
    ("zabava", "fotografiranje"): ["kamera", "uspomena", "poza", "svjetlo"],
    ("zabava", "video igra"): ["kontroler", "ekran", "noć", "ekipa"],
    ("zabava", "igraca konzola"): ["kauč", "kontroler", "televizor", "igrica"],
    ("zabava", "gamepad"): ["dugmad", "ruke", "igrica", "kauč"],
    ("zabava", "igraonica"): ["djeca", "aparati", "žetoni", "buka"],
    ("zabava", "zabavni park"): ["vrtiljak", "red", "ulaznica", "vikend"],
    ("zabava", "vrtuljak"): ["krug", "djeca", "muzika", "lampice"],
    ("zabava", "klovn"): ["cirkus", "smijeh", "kostim", "djeca"],
    ("zabava", "madionicar"): ["scena", "šešir", "publika", "trik"],
    ("zabava", "cirkus"): ["šator", "publika", "akrobati", "svjetla"],
    ("zabava", "izlozba"): ["galerija", "slike", "tišina", "posjetioci"],
    ("zabava", "muzej"): ["izložba", "tišina", "vitrine", "ulaznica"],
    ("zabava", "festival"): ["muzika", "gužva", "štandovi", "ljeto"],
    ("zabava", "sajam"): ["štand", "gužva", "ulaznica", "vikend"],
    ("zabava", "piknik"): ["deka", "trava", "sendvič", "društvo"],
    ("zabava", "izlazak"): ["društvo", "noć", "kafić", "muzika"],
    ("zabava", "kafic"): ["kafa", "stol", "razgovor", "večer"],
    ("zabava", "diskoteka"): ["muzika", "svjetla", "ples", "noć"],
    ("zabava", "dj"): ["muzika", "pult", "svjetla", "ples"],
    ("zabava", "titlovi"): ["bioskop", "epizoda", "Netflix", "ekran"],
    ("zabava", "epizoda"): ["serija", "kauč", "vikend", "nastavak"],
    ("zabava", "netflix"): ["serija", "kauč", "daljinski", "večer"],
    ("zabava", "kokice za kino"): ["mrak", "sala", "film", "škripanje"],
    ("zabava", "kino sjedalo"): ["sala", "red", "platno", "kokice"],
    ("zabava", "humor"): ["smijeh", "društvo", "šala", "večer"],
    ("zabava", "sala"): ["smijeh", "društvo", "vic", "reakcija"],
    ("zabava", "meme"): ["internet", "smijeh", "slika", "poruka"],
    ("zabava", "audio emisija"): ["slušalice", "epizoda", "glas", "šetnja"],
    ("zabava", "stream"): ["ekran", "chat", "uživo", "publika"],
    ("zabava", "publika online"): ["chat", "ekran", "uživo", "reakcije"],
    ("zabava", "navijanje"): ["stadion", "ekipa", "glas", "uzbuđenje"],

    ("balkan", "kafana"): ["muzika", "društvo", "čaša", "noć"],
    ("balkan", "pekara"): ["jutro", "burek", "miris", "red"],
    ("balkan", "trznica"): ["tezga", "voće", "subota", "gužva"],
    ("balkan", "susjed"): ["zgrada", "dvorište", "pozdrav", "vrata"],
    ("balkan", "susjedstvo"): ["zgrada", "dvorište", "priča", "ulaz"],
    ("balkan", "dzezva"): ["kafa", "šporet", "miris", "jutro"],
    ("balkan", "fildzan"): ["kafa", "tacna", "razgovor", "sećija"],
    ("balkan", "kafa u kafani"): ["čaša vode", "sto", "konobar", "razgovor"],
    ("balkan", "rakija"): ["čašica", "slavlje", "gost", "zima"],
    ("balkan", "dvorisni rostilj"): ["dvorište", "dim", "meso", "nedjelja"],
    ("balkan", "cevabdzinica"): ["lepinja", "luk", "miris", "red"],
    ("balkan", "buregdzinica"): ["jutro", "jogurt", "tepsija", "red"],
    ("balkan", "sarma"): ["porodica", "lonac", "zima", "praznik"],
    ("balkan", "domaci ajvar"): ["zimnica", "paprika", "tegla", "roštilj"],
    ("balkan", "zimnica"): ["tegla", "podrum", "jesen", "paprika"],
    ("balkan", "slava"): ["gosti", "svijeća", "sto", "porodica"],
    ("balkan", "svadba"): ["muzika", "kolo", "kolona", "veselje"],
    ("balkan", "kolo"): ["svadba", "muzika", "krug", "veselje"],
    ("balkan", "tamburica"): ["pjesma", "žica", "ravnica", "društvo"],
    ("balkan", "harmonika"): ["kafana", "svadba", "muzika", "veselje"],
    ("balkan", "truba"): ["svadba", "orkestar", "glasno", "veselje"],
    ("balkan", "narodna pjesma"): ["kafana", "radio", "društvo", "refren"],
    ("balkan", "sevdah"): ["kafana", "noć", "glas", "emocija"],
    ("balkan", "klapa"): ["more", "glasovi", "riva", "večer"],
    ("balkan", "riva"): ["more", "šetnja", "kafić", "zalazak"],
    ("balkan", "carsija"): ["dućani", "kaldrma", "kafa", "gužva"],
    ("balkan", "mahala"): ["sokak", "komšije", "avlija", "priča"],
    ("balkan", "avlija"): ["dvorište", "kapija", "cvijeće", "komšije"],
    ("balkan", "sokak"): ["kaldrma", "kuće", "djeca", "večer"],
    ("balkan", "kaldrma"): ["stari grad", "cipele", "ulica", "kamen"],
    ("balkan", "cilim"): ["soba", "šara", "pod", "tradicija"],
    ("balkan", "sporet na drva"): ["zima", "kuhinja", "lonac", "toplina"],
    ("balkan", "drva"): ["zima", "šupa", "cijepanje", "peć"],
    ("balkan", "supa"): ["alat", "drva", "dvorište", "prašina"],
    ("balkan", "bunar"): ["dvorište", "voda", "kanta", "selo"],
    ("balkan", "seoski vrt"): ["povrće", "zemlja", "ljeto", "dvorište"],
    ("balkan", "sljivik"): ["voće", "berba", "selo", "jesen"],
    ("balkan", "vinograd"): ["grožđe", "redovi", "berba", "sunce"],
    ("balkan", "berba"): ["voće", "jesen", "korpa", "društvo"],
    ("balkan", "seoski put"): ["prašina", "njiva", "traktor", "tišina"],
    ("balkan", "seoski autobus"): ["stanica", "karta", "gužva", "jutro"],
    ("balkan", "autobusna stanica"): ["klupa", "red vožnje", "torba", "čekanje"],
    ("balkan", "tetka"): ["porodica", "ručak", "savjet", "posjeta"],
    ("balkan", "ujak"): ["porodica", "priča", "posjeta", "smijeh"],
    ("balkan", "stric"): ["porodica", "dvorište", "priča", "praznik"],
    ("balkan", "baka"): ["kuhinja", "savjet", "ručak", "porodica"],
    ("balkan", "djed"): ["priča", "dvorište", "novine", "porodica"],
    ("balkan", "kum"): ["svadba", "čaša", "porodica", "zdravica"],
    ("balkan", "kuma"): ["svadba", "porodica", "poklon", "veselje"],
    ("balkan", "gosti"): ["sto", "kafa", "priča", "večer"],
    ("balkan", "meze"): ["tanjir", "kafana", "društvo", "čaša"],
    ("balkan", "sok od bazge"): ["ljeto", "dvorište", "čaša", "domaće"],
    ("balkan", "kiseli kupus"): ["zima", "sarma", "burence", "ručak"],
    ("balkan", "domaca juha"): ["porodica", "lonac", "nedjelja", "toplo"],
    ("balkan", "pogaca"): ["sto", "porodica", "praznik", "miris"],
    ("balkan", "lepinja"): ["ćevapi", "pekara", "toplo", "luk"],
    ("balkan", "kajmak"): ["lepinja", "doručak", "trpeza", "selo"],
    ("balkan", "paprikas"): ["lonac", "paprika", "ručak", "porodica"],
    ("balkan", "gulas"): ["lonac", "meso", "zima", "toplo"],
    ("balkan", "baklava"): ["slatko", "praznik", "sirup", "tanjir"],
    ("balkan", "tulumbe"): ["sirup", "poslastičarnica", "slatko", "tanjir"],
    ("balkan", "ustipci"): ["jutro", "tijesto", "ulje", "porodica"],
    ("balkan", "priganice"): ["tijesto", "ulje", "doručak", "porodica"],
    ("balkan", "domaca serija"): ["epizoda", "kauč", "porodica", "večer"],
    ("balkan", "tv dnevnik"): ["televizor", "večer", "porodica", "voditelj"],
    ("balkan", "daljinski"): ["kauč", "televizor", "dugmad", "večer"],
    ("balkan", "terasa kafica"): ["kafa", "sunce", "stol", "razgovor"],
    ("balkan", "promaja"): ["prozor", "vrata", "rasprava", "propuh"],
    ("balkan", "papirnati rucnik"): ["kuhinja", "mrlja", "ruke", "rolna"],
    ("balkan", "vikendica"): ["selo", "roštilj", "dvorište", "odmor"],
    ("balkan", "jadran"): ["more", "ljeto", "riva", "plaža"],
})

CATEGORY_EXACT_HINT_POOLS.update({
    ("odeca", "majica"): ["ormar", "ljeto", "rukav", "pranje"],
    ("odeca", "kosulja"): ["dugmad", "ormar", "posao", "pegla"],
    ("odeca", "hlace"): ["kaiš", "džep", "posao", "ormar"],
    ("odeca", "traperice"): ["džep", "kaiš", "ulica", "vikend"],
    ("odeca", "suknja"): ["ormar", "izlazak", "koljena", "ljeto"],
    ("odeca", "haljina"): ["svadba", "ormar", "večer", "stil"],
    ("odeca", "jakna"): ["zima", "vješalica", "rukav", "izlazak"],
    ("odeca", "kaput"): ["zima", "izlazak", "vješalica", "hladnoća"],
    ("odeca", "dzemper"): ["pletivo", "toplina", "zima", "kauč"],
    ("odeca", "duks"): ["kapuljača", "trening", "kauč", "vikend"],
    ("odeca", "trenerka"): ["sport", "kauč", "trening", "patike"],
    ("odeca", "kratke hlace"): ["ljeto", "plaža", "koljena", "odmor"],
    ("odeca", "donje rublje"): ["ladica", "pranje", "jutro", "privatno"],
    ("odeca", "carapa"): ["stopala", "ladica", "pranje", "par"],
    ("odeca", "cipela"): ["ulica", "pertle", "hodanje", "ormar"],
    ("odeca", "tenisica"): ["trening", "šetnja", "pertle", "park"],
    ("odeca", "cizma"): ["zima", "blato", "hodanje", "kiša"],
    ("odeca", "sandala"): ["ljeto", "plaža", "stopala", "šetnja"],
    ("odeca", "papuca"): ["kuća", "hodnik", "jutro", "udobnost"],
    ("odeca", "kapa"): ["glava", "sunce", "zima", "stil"],
    ("odeca", "sesir"): ["glava", "ljeto", "stil", "sjena"],
    ("odeca", "sal"): ["vrat", "zima", "kaput", "vjetar"],
    ("odeca", "rukavica"): ["zima", "prsti", "snijeg", "džep"],
    ("odeca", "remen"): ["hlače", "struk", "kopča", "ormar"],
    ("odeca", "torba"): ["rame", "novčanik", "izlazak", "ključevi"],
    ("odeca", "ruksak"): ["leđa", "škola", "putovanje", "patent"],
    ("odeca", "novcanik"): ["džep", "novac", "kartica", "torba"],
    ("odeca", "rucni sat"): ["zglob", "vrijeme", "kazaljke", "stil"],
    ("odeca", "nausnica"): ["uho", "nakit", "ogledalo", "kutija"],
    ("odeca", "ogrlica"): ["vrat", "nakit", "svečanost", "poklon"],
    ("odeca", "narukvica"): ["zglob", "nakit", "poklon", "kutija"],
    ("odeca", "prsten"): ["ruka", "nakit", "svadba", "kutija"],
    ("odeca", "naocale"): ["lice", "okvir", "sunce", "torbica"],
    ("odeca", "naocale za sunce"): ["sunce", "plaža", "lice", "torba"],
    ("odeca", "kravata"): ["košulja", "posao", "čvor", "sastanak"],
    ("odeca", "leptir masna"): ["svečanost", "košulja", "vrat", "večer"],
    ("odeca", "odijelo"): ["sastanak", "svadba", "košulja", "pegla"],
    ("odeca", "sako"): ["košulja", "posao", "vješalica", "sastanak"],
    ("odeca", "radna uniforma"): ["smjena", "ormar", "pravila", "identitet"],
    ("odeca", "pregaca"): ["kuhinja", "brašno", "kuhanje", "mrlje"],
    ("odeca", "pidzama"): ["krevet", "noć", "jutro", "meko"],
    ("odeca", "kupaci kostim"): ["plaža", "more", "torba", "ljeto"],
    ("odeca", "rucnik"): ["plaža", "tuš", "voda", "torba"],
    ("odeca", "kabanica"): ["kiša", "ulica", "kapuljača", "jesen"],
    ("odeca", "kisobran"): ["jesen", "ulica", "oblaci", "torba"],
    ("odeca", "gumb"): ["košulja", "rupa", "prsti", "šivanje"],
    ("odeca", "patentni zatvarac"): ["jakna", "torba", "povlačenje", "zubci"],
    ("odeca", "vezica"): ["cipela", "čvor", "hodanje", "jutro"],
    ("odeca", "dzep"): ["ključevi", "novčanik", "hlače", "ruka"],
    ("odeca", "kapuljaca"): ["duks", "kiša", "glava", "vjetar"],
    ("odeca", "vjesalica"): ["ormar", "jakna", "košulja", "hodnik"],
    ("odeca", "ormar"): ["odjeća", "vješalice", "ladice", "spavaća soba"],
    ("odeca", "ogledalo"): ["izlazak", "lice", "hodnik", "svjetlo"],
    ("odeca", "peglanje"): ["košulja", "para", "daska", "rukav"],
    ("odeca", "pranje rublja"): ["mašina", "deterdžent", "korpa", "čarape"],
    ("odeca", "susenje rublja"): ["žica", "balkon", "štipaljke", "vjetar"],
    ("odeca", "moda"): ["izlog", "stil", "boje", "časopis"],
    ("odeca", "stil"): ["ogledalo", "izlazak", "boje", "detalj"],
    ("odeca", "velicina"): ["etiketa", "kabina", "probavanje", "kupovina"],
    ("odeca", "boja"): ["izlog", "kombinacija", "ormar", "stil"],
    ("odeca", "materijal"): ["dodir", "etiketa", "tkanina", "kupovina"],
    ("odeca", "pamuk"): ["majica", "meko", "ljeto", "pranje"],
    ("odeca", "vuna"): ["džemper", "zima", "pletivo", "toplina"],
    ("odeca", "kozna jakna"): ["motor", "izlazak", "crno", "vješalica"],
    ("odeca", "svila"): ["haljina", "glatko", "svečanost", "marama"],
    ("odeca", "jeans"): ["traperice", "džep", "kaiš", "vikend"],
    ("odeca", "dzepna maramica"): ["sako", "džep", "svečanost", "detalj"],
    ("odeca", "kostim"): ["maskenbal", "scena", "uloga", "zabava"],
    ("odeca", "zastitna maska"): ["lice", "torba", "apoteka", "autobus"],
    ("odeca", "kravata svecana"): ["košulja", "čvor", "svadba", "sako"],
    ("odeca", "bros"): ["sako", "nakit", "igla", "detalj"],
    ("odeca", "torbica"): ["rame", "novčanik", "izlazak", "ključevi"],

    ("skola", "skola"): ["zvono", "tabla", "učionica", "torba"],
    ("skola", "ucionica"): ["klupe", "tabla", "razred", "tišina"],
    ("skola", "klupa"): ["učenik", "bilježnica", "olovka", "učionica"],
    ("skola", "skolska stolica"): ["sjedenje", "učionica", "klupa", "naslon"],
    ("skola", "tabla"): ["kreda", "razred", "učitelj", "zadatak"],
    ("skola", "kreda"): ["tabla", "prašina", "prsti", "razred"],
    ("skola", "spuzva"): ["tabla", "voda", "kreda", "učionica"],
    ("skola", "profesor"): ["škola", "ispit", "učionica", "tabla"],
    ("skola", "ucitelj"): ["razred", "dnevnik", "tabla", "ocjena"],
    ("skola", "ucenik"): ["torba", "klupa", "odmor", "zadatak"],
    ("skola", "ucenica"): ["torba", "klupa", "odmor", "bilježnica"],
    ("skola", "razred"): ["učionica", "klupe", "dnevnik", "zvono"],
    ("skola", "dnevnik"): ["ocjena", "učitelj", "razred", "roditelji"],
    ("skola", "biljeznica"): ["torba", "zadatak", "olovka", "stranice"],
    ("skola", "knjiga"): ["stranice", "lektira", "polica", "čitanje"],
    ("skola", "udzbenik"): ["torba", "lekcija", "stranice", "škola"],
    ("skola", "olovka"): ["pisanje", "pernica", "papir", "zadatak"],
    ("skola", "kemijska olovka"): ["ispit", "bilježnica", "klupa", "sat"],
    ("skola", "gumica"): ["olovka", "greška", "pernica", "papir"],
    ("skola", "siljilo"): ["olovka", "pernica", "piljevina", "klupa"],
    ("skola", "ravnalo"): ["crta", "geometrija", "pernica", "škola"],
    ("skola", "sestar"): ["krug", "geometrija", "pernica", "zadatak"],
    ("skola", "kalkulator"): ["brojevi", "matematika", "tipke", "ispit"],
    ("skola", "mapa"): ["papiri", "torba", "prezentacija", "red"],
    ("skola", "skolska torba"): ["knjige", "rame", "hodnik", "jutro"],
    ("skola", "skolski ruksak"): ["knjige", "rame", "patent", "hodnik"],
    ("skola", "zadaca"): ["kuća", "bilježnica", "večer", "zadatak"],
    ("skola", "ispit"): ["stres", "papir", "ocjena", "tišina"],
    ("skola", "test"): ["ispit", "olovka", "klupa", "sat"],
    ("skola", "ocjena"): ["dnevnik", "test", "roditelji", "škola"],
    ("skola", "svjedodzba"): ["kraj godine", "ocjene", "papir", "roditelji"],
    ("skola", "odmor"): ["zvono", "hodnik", "užina", "razgovor"],
    ("skola", "skolsko zvono"): ["odmor", "hodnik", "početak", "glasno"],
    ("skola", "knjiznica"): ["police", "tišina", "lektira", "knjige"],
    ("skola", "laboratorij"): ["epruveta", "miris", "zaštita", "eksperiment"],
    ("skola", "sportska dvorana"): ["lopta", "patike", "zviždaljka", "trening"],
    ("skola", "likovni"): ["boje", "papir", "kist", "crtež"],
    ("skola", "glazbeni"): ["pjesma", "nota", "instrument", "učionica"],
    ("skola", "matematika"): ["brojevi", "zadatak", "ispit", "bilježnica"],
    ("skola", "povijest"): ["datumi", "karta", "knjiga", "priča"],
    ("skola", "zemljopis"): ["karta", "države", "planina", "učionica"],
    ("skola", "priroda i drustvo"): ["biljke", "životinje", "učionica", "sveska"],
    ("skola", "biologija"): ["biljke", "mikroskop", "ćelije", "laboratorij"],
    ("skola", "kemija"): ["laboratorij", "epruveta", "miris", "zaštitne naočale"],
    ("skola", "fizika"): ["eksperiment", "formula", "laboratorij", "tabla"],
    ("skola", "informatika"): ["računar", "tastatura", "program", "učionica"],
    ("skola", "engleski"): ["riječi", "izgovor", "knjiga", "čas"],
    ("skola", "njemacki"): ["riječi", "gramatika", "knjiga", "čas"],
    ("skola", "hrvatski"): ["lektira", "gramatika", "učionica", "sveska"],
    ("skola", "lektira"): ["knjiga", "čitanje", "rok", "bilježnica"],
    ("skola", "esej"): ["papir", "tema", "olovka", "rok"],
    ("skola", "prezentacija"): ["plakat", "grupa", "tabla", "trema"],
    ("skola", "projekt"): ["grupa", "plakat", "rok", "prezentacija"],
    ("skola", "grupa"): ["dogovor", "projekt", "klupa", "zadatak"],
    ("skola", "skolski hodnik"): ["ormarići", "odmor", "gužva", "zvono"],
    ("skola", "zbornica"): ["dnevnik", "kafa", "profesori", "odmor"],
    ("skola", "ravnatelj"): ["ured", "hodnik", "pravila", "sastanak"],
    ("skola", "izlet"): ["autobus", "sendvič", "ruksak", "smijeh"],
    ("skola", "matura"): ["odijelo", "slikanje", "ispit", "uzbuđenje"],
    ("skola", "svjedocanstvo"): ["ocjene", "papir", "kraj godine", "roditelji"],
    ("skola", "prvasic"): ["torba", "prvi dan", "olovka", "uzbuđenje"],
    ("skola", "abeceda"): ["prvi razred", "tabla", "sveska", "čitanje"],
    ("skola", "slovo"): ["abeceda", "papir", "čitanje", "učenje"],
    ("skola", "broj"): ["matematika", "tabla", "zadatak", "računanje"],
    ("skola", "geometrija"): ["ravnalo", "šestar", "crta", "zadatak"],
    ("skola", "atlas"): ["karte", "države", "geografija", "polica"],
    ("skola", "globus"): ["svijet", "učionica", "karta", "okretanje"],
    ("skola", "mikroskop"): ["laboratorij", "stakalce", "biologija", "oko"],
    ("skola", "eksperiment"): ["laboratorij", "miris", "zaštita", "radoznalost"],
    ("skola", "flomaster"): ["boje", "plakat", "pernica", "crtež"],
    ("skola", "markeri"): ["boje", "tabla", "plakat", "prezentacija"],
    ("skola", "plakat"): ["prezentacija", "boje", "grupa", "zid"],
})

CATEGORY_EXACT_HINT_POOLS.update({
    ("hrana", "kruh"): ["doručak", "pekara", "namaz", "sendvič"],
    ("hrana", "sir"): ["sendvič", "frižider", "pijaca", "doručak"],
    ("hrana", "mlijeko"): ["doručak", "čaša", "frižider", "kafa"],
    ("hrana", "jaje"): ["doručak", "tava", "ljuska", "kuhinja"],
    ("hrana", "maslac"): ["namaz", "doručak", "frižider", "kruh"],
    ("hrana", "jabuka"): ["voće", "škola", "torba", "užina"],
    ("hrana", "banana"): ["voće", "užina", "pijaca", "žuto"],
    ("hrana", "naranca"): ["zima", "sok", "miris", "vitamin"],
    ("hrana", "rajcica"): ["salata", "ljeto", "pijaca", "sendvič"],
    ("hrana", "krumpir"): ["ručak", "pećnica", "prilog", "selo"],
    ("hrana", "mrkva"): ["supa", "zec", "pijaca", "narandžasto"],
    ("hrana", "luk"): ["suze", "kuhinja", "tava", "ručak"],
    ("hrana", "riza"): ["tanjir", "ručak", "prilog", "lonac"],
    ("hrana", "tjestenina"): ["lonac", "umak", "vilica", "večera"],
    ("hrana", "juha"): ["žlica", "tanjur", "ručak", "toplo"],
    ("hrana", "corba"): ["kašika", "lonac", "toplo", "ručak"],
    ("hrana", "salata"): ["zdjela", "povrće", "ljeto", "ručak"],
    ("hrana", "piletina"): ["tava", "ručak", "pećnica", "miris"],
    ("hrana", "riba"): ["more", "tanjir", "limun", "restoran"],
    ("hrana", "kolac"): ["slatko", "rođendan", "tanjir", "kafa"],
    ("hrana", "sladoled"): ["ljeto", "kornet", "hladno", "šetnja"],
    ("hrana", "palacinka"): ["tava", "džem", "doručak", "slatko"],
    ("hrana", "cokolada"): ["slatko", "poklon", "film", "poslastica"],
    ("hrana", "med"): ["tegla", "čaj", "kašika", "pčela"],
    ("hrana", "jogurt"): ["doručak", "frižider", "kašika", "voće"],
    ("hrana", "lubenica"): ["ljeto", "plaža", "nož", "sok"],
    ("hrana", "grozde"): ["vinograd", "grozd", "ljeto", "zdjela"],
    ("hrana", "jagoda"): ["proljeće", "slatko", "šlag", "pijaca"],
    ("hrana", "kruska"): ["voće", "užina", "jesen", "sok"],
    ("hrana", "breskva"): ["ljeto", "sok", "pijaca", "koštica"],
    ("hrana", "limun"): ["čaj", "kiselina", "žuto", "limunada"],
    ("hrana", "krastavac"): ["salata", "ljeto", "pijaca", "svježe"],
    ("hrana", "paprika"): ["pijaca", "boje", "salata", "ajvar"],
    ("hrana", "grah"): ["lonac", "ručak", "zima", "porodica"],
    ("hrana", "grasak"): ["zeleno", "prilog", "ručak", "kašika"],
    ("hrana", "kupus"): ["sarma", "salata", "pijaca", "zima"],
    ("hrana", "gljiva"): ["šuma", "tava", "pica", "miris"],
    ("hrana", "kukuruz"): ["klip", "roštilj", "ljeto", "putar"],
    ("hrana", "kobasica"): ["roštilj", "tava", "senf", "doručak"],
    ("hrana", "sunka"): ["sendvič", "frižider", "doručak", "narezano"],
    ("hrana", "tost"): ["doručak", "toplo", "sir", "aparat"],
    ("hrana", "sendvic"): ["pauza", "torba", "škola", "doručak"],
    ("hrana", "pizza"): ["restoran", "sir", "kutija", "večer"],
    ("hrana", "pljeskavica"): ["roštilj", "lepinja", "luk", "društvo"],
    ("hrana", "cevapi"): ["roštilj", "lepinja", "luk", "društvo"],
    ("hrana", "sarma"): ["praznik", "porodica", "lonac", "zima"],
    ("hrana", "burek"): ["pekara", "jutro", "miris", "jogurt"],
    ("hrana", "gibanica"): ["sir", "tepsija", "doručak", "porodica"],
    ("hrana", "pita"): ["tepsija", "sir", "jabuka", "kuhinja"],
    ("hrana", "ajvar"): ["zimnica", "paprika", "tegla", "roštilj"],
    ("hrana", "kajmak"): ["lepinja", "doručak", "selo", "tanjir"],
    ("hrana", "kiselo vrhnje"): ["žlica", "zdjela", "ručak", "frižider"],
    ("hrana", "kava"): ["jutro", "šoljica", "razgovor", "pauza"],
    ("hrana", "caj"): ["šolja", "zima", "med", "mir"],
    ("hrana", "sok"): ["čaša", "ljeto", "frižider", "voće"],
    ("hrana", "voda"): ["čaša", "žeđ", "ljeto", "trening"],
    ("hrana", "mineralna voda"): ["mjehurići", "čaša", "ručak", "frižider"],
    ("hrana", "limunada"): ["limun", "čaša", "led", "ljeto"],
    ("hrana", "rostilj"): ["dvorište", "dim", "meso", "društvo"],
    ("hrana", "omlet"): ["jaje", "tava", "doručak", "sir"],
    ("hrana", "musaka"): ["pećnica", "krompir", "ručak", "tepsija"],
    ("hrana", "krofna"): ["šećer", "pekara", "slatko", "jutro"],
    ("hrana", "keks"): ["mlijeko", "kutija", "užina", "djeca"],
    ("hrana", "cips"): ["film", "kesica", "društvo", "grickanje"],
    ("hrana", "kokice"): ["film", "lonac", "kino", "grickanje"],
    ("hrana", "orasi"): ["ljuska", "kolač", "zima", "zdjela"],
    ("hrana", "bademi"): ["zdjela", "užina", "zdravo", "grickanje"],
    ("hrana", "ljesnjak"): ["čokolada", "ljuska", "kolač", "jesen"],
    ("hrana", "slanina"): ["tava", "doručak", "miris", "jaje"],
    ("hrana", "maslina"): ["more", "salata", "tanjir", "ulje"],
    ("hrana", "spinat"): ["zeleno", "ručak", "tava", "pita"],

    ("zivotinje", "pas"): ["šetnja", "povodac", "dvorište", "lavež"],
    ("zivotinje", "macka"): ["kauč", "prozor", "noć", "šapa"],
    ("zivotinje", "konj"): ["selo", "sedlo", "trka", "štala"],
    ("zivotinje", "krava"): ["selo", "štala", "mlijeko", "livada"],
    ("zivotinje", "koza"): ["selo", "brdo", "mlijeko", "stado"],
    ("zivotinje", "ovca"): ["vuna", "stado", "livada", "selo"],
    ("zivotinje", "svinja"): ["blato", "farma", "korito", "selo"],
    ("zivotinje", "kokos"): ["dvorište", "jaje", "perje", "selo"],
    ("zivotinje", "pijetao"): ["jutro", "kokošinjac", "selo", "kukurikanje"],
    ("zivotinje", "patka"): ["jezero", "voda", "perje", "kvakanje"],
    ("zivotinje", "guska"): ["dvorište", "voda", "perje", "glasno"],
    ("zivotinje", "zec"): ["mrkva", "livada", "uši", "tišina"],
    ("zivotinje", "hrcak"): ["kavez", "točak", "sjeme", "kućni ljubimac"],
    ("zivotinje", "papiga"): ["kavez", "perje", "glas", "boje"],
    ("zivotinje", "riba"): ["voda", "udica", "more", "akvarij"],
    ("zivotinje", "kornjaca"): ["oklop", "sporo", "voda", "kamen"],
    ("zivotinje", "zmija"): ["trava", "tišina", "koža", "oprez"],
    ("zivotinje", "guster"): ["kamen", "sunce", "rep", "zid"],
    ("zivotinje", "zaba"): ["bara", "skakanje", "kiša", "kreket"],
    ("zivotinje", "mis"): ["rupa", "sir", "noć", "malo"],
    ("zivotinje", "stakor"): ["podrum", "noć", "rep", "grad"],
    ("zivotinje", "vjeverica"): ["orah", "drvo", "rep", "park"],
    ("zivotinje", "jez"): ["lišće", "bodlje", "vrt", "noć"],
    ("zivotinje", "lisica"): ["šuma", "rep", "lukavost", "selo"],
    ("zivotinje", "vuk"): ["šuma", "čopor", "noć", "zavijanje"],
    ("zivotinje", "medvjed"): ["šuma", "zima", "planina", "tragovi"],
    ("zivotinje", "lav"): ["savana", "griva", "zoološki vrt", "rik"],
    ("zivotinje", "tigar"): ["pruge", "džungla", "zoološki vrt", "tišina"],
    ("zivotinje", "slon"): ["surla", "veličina", "zoološki vrt", "uši"],
    ("zivotinje", "zirafa"): ["dug vrat", "savana", "lišće", "zoološki vrt"],
    ("zivotinje", "majmun"): ["banana", "drvo", "zoološki vrt", "skakanje"],
    ("zivotinje", "zebra"): ["pruge", "savana", "stado", "trčanje"],
    ("zivotinje", "klokan"): ["skok", "torba", "Australija", "zoološki vrt"],
    ("zivotinje", "panda"): ["bambus", "crno-bijelo", "zoološki vrt", "mir"],
    ("zivotinje", "pingvin"): ["led", "more", "kolonija", "hodanje"],
    ("zivotinje", "dupin"): ["more", "skok", "talasi", "akvarij"],
    ("zivotinje", "kit"): ["more", "veličina", "dubina", "rep"],
    ("zivotinje", "morski pas"): ["more", "peraja", "dubina", "oprez"],
    ("zivotinje", "hobotnica"): ["more", "pipci", "akvarij", "dubina"],
    ("zivotinje", "rak"): ["more", "kliješta", "kamen", "plaža"],
    ("zivotinje", "skoljka"): ["plaža", "pijesak", "talasi", "more"],
    ("zivotinje", "puz"): ["kiša", "vrt", "sporo", "kućica"],
    ("zivotinje", "pcela"): ["cvijet", "med", "košnica", "ljeto"],
    ("zivotinje", "mrav"): ["kolona", "mrvice", "zemlja", "rad"],
    ("zivotinje", "leptir"): ["cvijet", "krila", "ljeto", "boje"],
    ("zivotinje", "muha"): ["kuhinja", "zujanje", "ljeto", "prozor"],
    ("zivotinje", "komarac"): ["noć", "ubod", "ljeto", "zujanje"],
    ("zivotinje", "pauk"): ["mreža", "ugao", "tišina", "podrum"],
    ("zivotinje", "bubamara"): ["crveno", "tačkice", "list", "vrt"],
    ("zivotinje", "orao"): ["nebo", "krila", "planina", "visina"],
    ("zivotinje", "sova"): ["noć", "drvo", "tišina", "oči"],
    ("zivotinje", "golub"): ["trg", "mrvice", "grad", "krila"],
    ("zivotinje", "vrana"): ["drvo", "crno", "glas", "grad"],
    ("zivotinje", "labud"): ["jezero", "bijelo", "vrat", "mir"],
    ("zivotinje", "roda"): ["krov", "gnijezdo", "duge noge", "selo"],
    ("zivotinje", "flamingo"): ["ružičasto", "voda", "duge noge", "jato"],
    ("zivotinje", "deva"): ["pustinja", "teret", "vrućina", "karavan"],
    ("zivotinje", "magarac"): ["selo", "teret", "uši", "staja"],
    ("zivotinje", "jelen"): ["šuma", "rogovi", "jutro", "tragovi"],
    ("zivotinje", "srna"): ["šuma", "livada", "tišina", "jutro"],
    ("zivotinje", "divlja svinja"): ["šuma", "blato", "kljove", "tragovi"],
    ("zivotinje", "ris"): ["šuma", "tišina", "šape", "planina"],
    ("zivotinje", "tuljan"): ["more", "led", "peraje", "obala"],
    ("zivotinje", "vidra"): ["rijeka", "kamen", "voda", "igra"],
    ("zivotinje", "jazavac"): ["rupa", "šuma", "noć", "pruge"],
    ("zivotinje", "dabar"): ["rijeka", "brana", "drvo", "zubi"],
    ("zivotinje", "noj"): ["duge noge", "pustinja", "brzina", "jaje"],
    ("zivotinje", "paun"): ["perje", "boje", "dvorište", "rep"],
    ("zivotinje", "kengur"): ["skok", "torba", "Australija", "zoološki vrt"],
    ("zivotinje", "koala"): ["eukaliptus", "drvo", "spavanje", "Australija"],
    ("zivotinje", "aligator"): ["močvara", "zubi", "voda", "oprez"],
    ("zivotinje", "krokodil"): ["rijeka", "zubi", "voda", "oprez"],
})

CATEGORY_HINT_BANKS = {
    "Kuća": [
        ["jutro", "kuhinja", "miris", "stol"], ["večer", "kauč", "svjetlo", "tišina"],
        ["čišćenje", "vreća", "pod", "vikend"], ["spavaća soba", "noć", "ladice", "ormar"],
        ["kupatilo", "pločice", "para", "ručnik"], ["hodnik", "ključevi", "cipele", "žurba"],
        ["dnevna soba", "gosti", "televizor", "grickalice"], ["balkon", "biljke", "sunce", "kafa"],
        ["popravka", "alat", "vijak", "strpljenje"], ["porodični ručak", "tanjir", "stol", "razgovor"],
        ["zima", "deka", "čaj", "prozor"], ["selidba", "kutije", "namještaj", "prašina"],
    ],
    "Hrana": [
        ["doručak", "tanjir", "miris", "jutro"], ["ručak", "lonac", "kuhinja", "porodica"],
        ["večera", "stol", "gosti", "razgovor"], ["pijaca", "tezga", "boje", "subota"],
        ["frižider", "čaša", "hladno", "užina"], ["slatko", "film", "poklon", "poslastica"],
        ["roštilj", "dim", "dvorište", "društvo"], ["pekara", "red", "miris", "jutro"],
        ["ljeto", "voće", "sok", "plaža"], ["zima", "lonac", "toplo", "porodica"],
        ["sendvič", "pauza", "torba", "škola"], ["restoran", "konobar", "meni", "večer"],
    ],
    "Životinje": [
        ["selo", "dvorište", "jutro", "stado"], ["šuma", "tragovi", "tišina", "staza"],
        ["zoološki vrt", "djeca", "ograda", "vikend"], ["kućni ljubimac", "kauč", "igra", "zdjelica"],
        ["more", "talasi", "dubina", "brod"], ["livada", "trava", "sunce", "mir"],
        ["noć", "zvuk", "sjena", "prozor"], ["farma", "štala", "hrana", "blato"],
        ["park", "šetnja", "povodac", "djeca"], ["planina", "kamen", "vjetar", "sloboda"],
        ["vrt", "cvijet", "ljeto", "zuji"], ["rijeka", "obala", "voda", "kamen"],
    ],
    "Sport": [
        ["stadion", "navijanje", "lopta", "večer"], ["dvorana", "patike", "znoj", "trening"],
        ["teren", "ekipa", "sudija", "utakmica"], ["bazen", "voda", "ljeto", "trka"],
        ["parket", "semafor", "publika", "pauza"], ["reket", "mreža", "servis", "tišina"],
        ["planina", "staza", "ranac", "umor"], ["teretana", "tegovi", "ogledalo", "znoj"],
        ["medalja", "postolje", "ponos", "aplauz"], ["svlačionica", "dres", "voda", "nervoza"],
    ],
    "Škola": [
        ["učionica", "tabla", "dnevnik", "odmor"], ["pernica", "bilježnica", "zadatak", "tišina"],
        ["ispit", "nervoza", "klupa", "sat"], ["laboratorij", "eksperiment", "miris", "zaštita"],
        ["biblioteka", "police", "tišina", "lektira"], ["hodnik", "zvono", "gužva", "torba"],
        ["geometrija", "crta", "papir", "olovka"], ["matura", "odijelo", "slikanje", "uzbuđenje"],
        ["prezentacija", "plakat", "grupa", "projekt"], ["školski izlet", "autobus", "sendvič", "smijeh"],
    ],
    "Posao": [
        ["kancelarija", "sastanak", "kafa", "rok"], ["uniforma", "smjena", "jutro", "umor"],
        ["radionica", "alat", "prašina", "popravka"], ["restoran", "narudžba", "miris", "večer"],
        ["sud", "dokumenti", "odijelo", "ozbiljnost"], ["gradilište", "kaciga", "buka", "pauza"],
        ["recepcija", "telefon", "osmijeh", "gosti"], ["tim", "plan", "laptop", "poruka"],
        ["prodavnica", "račun", "red", "kasa"], ["salon", "ogledalo", "termin", "makaze"],
    ],
    "Tehnologija": [
        ["telefon", "poruka", "džep", "notifikacija"], ["kabl", "utičnica", "noćni ormarić", "struja"],
        ["laptop", "tastatura", "sastanak", "torba"], ["Wi-Fi", "lozinka", "signal", "stan"],
        ["kamera", "slika", "uspomena", "putovanje"], ["igrica", "kontroler", "kauč", "večer"],
        ["aplikacija", "ikonica", "ekran", "poruka"], ["server", "mreža", "tišina", "lampice"],
        ["slušalice", "muzika", "autobus", "šetnja"], ["projektor", "prezentacija", "zid", "mrak"],
    ],
    "Putovanja": [
        ["kofer", "recepcija", "ključ", "doručak"], ["aerodrom", "kontrola", "torba", "red"],
        ["plaža", "peškir", "sunce", "odmor"], ["mapa", "grad", "šetnja", "telefon"],
        ["granica", "dokument", "auto", "čekanje"], ["peron", "karta", "putovanje", "prozor"],
        ["kamp", "šator", "vatra", "noć"], ["suvenir", "razglednica", "fotografija", "poklon"],
        ["hotel", "lift", "hodnik", "tišina"], ["planina", "ranac", "staza", "umor"],
    ],
    "Priroda": [
        ["nebo", "svjetlost", "toplina", "ljeto"], ["oblaci", "ulica", "jesen", "kapljice"],
        ["šuma", "drveće", "hlad", "staza"], ["rijeka", "most", "obala", "šetnja"],
        ["planina", "vjetar", "pogled", "tišina"], ["livada", "trava", "cvijet", "pčele"],
        ["more", "valovi", "obala", "sol"], ["zima", "snijeg", "rukavice", "mir"],
        ["vrt", "zemlja", "zalijevanje", "jutro"], ["noć", "mjesec", "zvijezde", "hladno"],
    ],
    "Prevoz": [
        ["stanica", "karta", "gužva", "jutro"], ["parking", "volan", "put", "gorivo"],
        ["peron", "pruga", "prozor", "putovanje"], ["pedale", "park", "lanac", "vožnja"],
        ["semafor", "raskrsnica", "žurba", "sirena"], ["aerodrom", "terminal", "kofer", "let"],
        ["luka", "talasi", "brod", "vjetar"], ["autocesta", "odmor", "radio", "brzina"],
        ["taksi", "aplikacija", "adresa", "noć"], ["tramvaj", "šine", "centar", "stanica"],
    ],
    "Odeća": [
        ["ormar", "vješalica", "izlazak", "ogledalo"], ["zima", "rukav", "kaput", "hladno"],
        ["ulica", "pertle", "hodanje", "kiša"], ["ladica", "pranje", "par", "stopala"],
        ["svečanost", "odijelo", "fotografija", "večer"], ["plaža", "sunce", "torba", "ljeto"],
        ["sport", "patike", "trening", "znoj"], ["moda", "boja", "stil", "izlog"],
        ["kiša", "kapuljača", "autobus", "jesen"], ["nakit", "poklon", "kutija", "svjetlo"],
    ],
    "Zdravlje": [
        ["čekaonica", "pregled", "termin", "mantil"], ["apoteka", "recept", "red", "savjet"],
        ["jutro", "voda", "šetnja", "navika"], ["zub", "osmijeh", "četkica", "pasta"],
        ["odmor", "san", "tišina", "jastuk"], ["trening", "disanje", "znoj", "energija"],
        ["ekran", "vid", "okvir", "knjiga"], ["čaj", "med", "toplo", "grlo"],
        ["higijena", "sapun", "ručnik", "kupatilo"], ["masaža", "leđa", "opuštanje", "mir"],
    ],
    "Zabava": [
        ["bioskop", "kokice", "mrak", "platno"], ["koncert", "publika", "svjetla", "večer"],
        ["ekipa", "smijeh", "izazov", "stol"], ["rođendan", "poklon", "balon", "slavlje"],
        ["scena", "aplauz", "kostim", "ulaznica"], ["kauč", "serija", "epizoda", "grickalice"],
        ["festival", "gužva", "muzika", "ljeto"], ["hobi", "boje", "mir", "vikend"],
        ["igrica", "kontroler", "ekran", "noć"], ["karaoke", "mikrofon", "društvo", "pjesma"],
    ],
    "Balkan": [
        ["muzika", "društvo", "čaša", "noć"], ["jutro", "burek", "miris", "red"],
        ["tezga", "voće", "subota", "gužva"], ["zgrada", "dvorište", "pozdrav", "vrata"],
        ["praznik", "porodica", "sto", "gosti"], ["selo", "bašta", "hlad", "priča"],
        ["kafana", "dim", "harmonika", "smijeh"], ["ljeto", "riva", "šetnja", "more"],
        ["zimnica", "tegla", "paprika", "podrum"], ["svadba", "kolo", "muzika", "kolona"],
    ],
}

RAW_CATEGORY_WORDS = {
    "Kuća": [
        [
            "Kuća",
            "kuća"
        ],
        [
            "Stan",
            "stan"
        ],
        [
            "Soba",
            "soba"
        ],
        [
            "Kuhinja",
            "kuhinja"
        ],
        [
            "Kupatilo",
            "kupatilo"
        ],
        [
            "Dnevni boravak",
            "dnevna soba"
        ],
        [
            "Spavaća soba",
            "spavaća soba"
        ],
        [
            "Hodnik",
            "hodnik"
        ],
        [
            "Balkon",
            "balkon"
        ],
        [
            "Terasa",
            "terasa"
        ],
        [
            "Vrata",
            "vrata"
        ],
        [
            "Prozor",
            "prozor"
        ],
        [
            "Zid",
            "zid"
        ],
        [
            "Pod",
            "pod"
        ],
        [
            "Strop",
            "plafon"
        ],
        [
            "Krov",
            "krov"
        ],
        [
            "Stol",
            "sto"
        ],
        [
            "Stolica",
            "stolica"
        ],
        [
            "Krevet",
            "krevet"
        ],
        [
            "Jastuk",
            "jastuk"
        ],
        [
            "Pokrivač",
            "pokrivač"
        ],
        [
            "Deka",
            "ćebe"
        ],
        [
            "Ormar",
            "ormar"
        ],
        [
            "Ladica",
            "fioka"
        ],
        [
            "Polica",
            "polica"
        ],
        [
            "Kauč",
            "kauč"
        ],
        [
            "Fotelja",
            "fotelja"
        ],
        [
            "Tepih",
            "tepih"
        ],
        [
            "Zavjesa",
            "zavesa"
        ],
        [
            "Lampa",
            "lampa"
        ],
        [
            "Svjetiljka",
            "svetiljka"
        ],
        [
            "Ogledalo",
            "ogledalo"
        ],
        [
            "Slika",
            "slika"
        ],
        [
            "Sat",
            "sat"
        ],
        [
            "Vaza",
            "vaza"
        ],
        [
            "Tanjur",
            "tanjir"
        ],
        [
            "Čaša",
            "čaša"
        ],
        [
            "Šalica",
            "šolja"
        ],
        [
            "Žlica",
            "kašika"
        ],
        [
            "Vilica",
            "viljuška"
        ],
        [
            "Nož",
            "nož"
        ],
        [
            "Lonac",
            "lonac"
        ],
        [
            "Tava",
            "tiganj"
        ],
        [
            "Pećnica",
            "rerna"
        ],
        [
            "Hladnjak",
            "frižider"
        ],
        [
            "Zamrzivač",
            "zamrzivač"
        ],
        [
            "Sudoper",
            "sudopera"
        ],
        [
            "Spužva",
            "sunđer"
        ],
        [
            "Metla",
            "metla"
        ],
        [
            "Krpa",
            "krpa"
        ],
        [
            "Usisavač",
            "usisivač"
        ],
        [
            "Perilica rublja",
            "veš mašina"
        ],
        [
            "Sušilica",
            "sušilica"
        ],
        [
            "Pegla",
            "pegla"
        ],
        [
            "Daska za peglanje",
            "daska za peglanje"
        ],
        [
            "Ključ",
            "ključ"
        ],
        [
            "Brava",
            "brava"
        ],
        [
            "Zvono",
            "zvono"
        ],
        [
            "Kanta",
            "kanta"
        ],
        [
            "Kanta za smeće",
            "kanta za đubre"
        ],
        [
            "Daljinski upravljač",
            "daljinski"
        ],
        [
            "Televizor",
            "televizor"
        ],
        [
            "Radio",
            "radio"
        ],
        [
            "Punjač",
            "punjač"
        ],
        [
            "Utičnica",
            "utičnica"
        ],
        [
            "Prekidač",
            "prekidač"
        ],
        [
            "Stepenice",
            "stepenice"
        ],
        [
            "Dvorište",
            "dvorište"
        ],
        [
            "Garaža",
            "garaža"
        ],
        [
            "Podrum",
            "podrum"
        ],
        [
            "Tavan",
            "tavan"
        ],
        [
            "Komoda",
            "komoda"
        ]
    ],
    "Hrana": [
        [
            "Kruh",
            "hleb"
        ],
        [
            "Sir",
            "sir"
        ],
        [
            "Mlijeko",
            "mleko"
        ],
        [
            "Jaje",
            "jaje"
        ],
        [
            "Maslac",
            "puter"
        ],
        [
            "Jabuka",
            "jabuka"
        ],
        [
            "Banana",
            "banana"
        ],
        [
            "Naranča",
            "pomorandža"
        ],
        [
            "Rajčica",
            "paradajz"
        ],
        [
            "Krumpir",
            "krompir"
        ],
        [
            "Mrkva",
            "šargarepa"
        ],
        [
            "Luk",
            "luk"
        ],
        [
            "Riža",
            "pirinač"
        ],
        [
            "Tjestenina",
            "testenina"
        ],
        [
            "Juha",
            "supa"
        ],
        [
            "Čorba",
            "čorba"
        ],
        [
            "Salata",
            "salata"
        ],
        [
            "Piletina",
            "piletina"
        ],
        [
            "Riba",
            "riba"
        ],
        [
            "Kolač",
            "kolač"
        ],
        [
            "Sladoled",
            "sladoled"
        ],
        [
            "Palačinka",
            "palačinka"
        ],
        [
            "Čokolada",
            "čokolada"
        ],
        [
            "Med",
            "med"
        ],
        [
            "Jogurt",
            "jogurt"
        ],
        [
            "Lubenica",
            "lubenica"
        ],
        [
            "Grožđe",
            "grožđe"
        ],
        [
            "Jagoda",
            "jagoda"
        ],
        [
            "Kruška",
            "kruška"
        ],
        [
            "Breskva",
            "breskva"
        ],
        [
            "Limun",
            "limun"
        ],
        [
            "Krastavac",
            "krastavac"
        ],
        [
            "Paprika",
            "paprika"
        ],
        [
            "Grah",
            "pasulj"
        ],
        [
            "Grašak",
            "grašak"
        ],
        [
            "Kupus",
            "kupus"
        ],
        [
            "Gljiva",
            "pečurka"
        ],
        [
            "Kukuruz",
            "kukuruz"
        ],
        [
            "Kobasica",
            "kobasica"
        ],
        [
            "Šunka",
            "šunka"
        ],
        [
            "Tost",
            "tost"
        ],
        [
            "Sendvič",
            "sendvič"
        ],
        [
            "Pizza",
            "pica"
        ],
        [
            "Pljeskavica",
            "pljeskavica"
        ],
        [
            "Ćevapi",
            "ćevapi"
        ],
        [
            "Sarma",
            "sarma"
        ],
        [
            "Burek",
            "burek"
        ],
        [
            "Gibanica",
            "gibanica"
        ],
        [
            "Pita",
            "pita"
        ],
        [
            "Ajvar",
            "ajvar"
        ],
        [
            "Kajmak",
            "kajmak"
        ],
        [
            "Kiselo vrhnje",
            "kisela pavlaka"
        ],
        [
            "Kava",
            "kafa"
        ],
        [
            "Čaj",
            "čaj"
        ],
        [
            "Sok",
            "sok"
        ],
        [
            "Voda",
            "voda"
        ],
        [
            "Mineralna voda",
            "kisela voda"
        ],
        [
            "Limunada",
            "limunada"
        ],
        [
            "Roštilj",
            "roštilj"
        ],
        [
            "Omlet",
            "omlet"
        ],
        [
            "Musaka",
            "musaka"
        ],
        [
            "Krofna",
            "krofna"
        ],
        [
            "Keks",
            "keks"
        ],
        [
            "Čips",
            "čips"
        ],
        [
            "Kokice",
            "kokice"
        ],
        [
            "Orasi",
            "orasi"
        ],
        [
            "Bademi",
            "bademi"
        ],
        [
            "Lješnjak",
            "lešnik"
        ],
        [
            "Slanina",
            "slanina"
        ],
        [
            "Maslina",
            "maslina"
        ],
        [
            "Špinat",
            "spanać"
        ]
    ],
    "Životinje": [
        [
            "Pas",
            "pas"
        ],
        [
            "Mačka",
            "mačka"
        ],
        [
            "Konj",
            "konj"
        ],
        [
            "Krava",
            "krava"
        ],
        [
            "Koza",
            "koza"
        ],
        [
            "Ovca",
            "ovca"
        ],
        [
            "Svinja",
            "svinja"
        ],
        [
            "Kokoš",
            "kokoška"
        ],
        [
            "Pijetao",
            "petao"
        ],
        [
            "Patka",
            "patka"
        ],
        [
            "Guska",
            "guska"
        ],
        [
            "Zec",
            "zec"
        ],
        [
            "Hrčak",
            "hrčak"
        ],
        [
            "Papiga",
            "papagaj"
        ],
        [
            "Riba",
            "ribica"
        ],
        [
            "Kornjača",
            "kornjača"
        ],
        [
            "Zmija",
            "zmija"
        ],
        [
            "Gušter",
            "gušter"
        ],
        [
            "Žaba",
            "žaba"
        ],
        [
            "Miš",
            "miš"
        ],
        [
            "Štakor",
            "pacov"
        ],
        [
            "Vjeverica",
            "veverica"
        ],
        [
            "Jež",
            "jež"
        ],
        [
            "Lisica",
            "lisica"
        ],
        [
            "Vuk",
            "vuk"
        ],
        [
            "Medvjed",
            "medved"
        ],
        [
            "Lav",
            "lav"
        ],
        [
            "Tigar",
            "tigar"
        ],
        [
            "Slon",
            "slon"
        ],
        [
            "Žirafa",
            "žirafa"
        ],
        [
            "Majmun",
            "majmun"
        ],
        [
            "Zebra",
            "zebra"
        ],
        [
            "Klokan",
            "kengur"
        ],
        [
            "Panda",
            "panda"
        ],
        [
            "Pingvin",
            "pingvin"
        ],
        [
            "Dupin",
            "delfin"
        ],
        [
            "Kit",
            "kit"
        ],
        [
            "Morski pas",
            "ajkula"
        ],
        [
            "Hobotnica",
            "hobotnica"
        ],
        [
            "Rak",
            "rak"
        ],
        [
            "Školjka",
            "školjka"
        ],
        [
            "Puž",
            "puž"
        ],
        [
            "Pčela",
            "pčela"
        ],
        [
            "Mrav",
            "mrav"
        ],
        [
            "Leptir",
            "leptir"
        ],
        [
            "Muha",
            "muva"
        ],
        [
            "Komarac",
            "komarac"
        ],
        [
            "Pauk",
            "pauk"
        ],
        [
            "Bubamara",
            "bubamara"
        ],
        [
            "Orao",
            "orao"
        ],
        [
            "Sova",
            "sova"
        ],
        [
            "Golub",
            "golub"
        ],
        [
            "Vrana",
            "vrana"
        ],
        [
            "Labud",
            "labud"
        ],
        [
            "Roda",
            "roda"
        ],
        [
            "Flamingo",
            "flamingo"
        ],
        [
            "Deva",
            "kamila"
        ],
        [
            "Magarac",
            "magarac"
        ],
        [
            "Jelen",
            "jelen"
        ],
        [
            "Srna",
            "srna"
        ],
        [
            "Divlja svinja",
            "divlja svinja"
        ],
        [
            "Ris",
            "ris"
        ],
        [
            "Tuljan",
            "foka"
        ],
        [
            "Vidra",
            "vidra"
        ],
        [
            "Jazavac",
            "jazavac"
        ],
        [
            "Dabar",
            "dabar"
        ],
        [
            "Noj",
            "noj"
        ],
        [
            "Paun",
            "paun"
        ],
        [
            "Kengur",
            "kengur"
        ],
        [
            "Koala",
            "koala"
        ],
        [
            "Aligator",
            "aligator"
        ],
        [
            "Krokodil",
            "krokodil"
        ]
    ],
    "Sport": [
        [
            "Nogomet",
            "fudbal"
        ],
        [
            "Košarka",
            "košarka"
        ],
        [
            "Rukomet",
            "rukomet"
        ],
        [
            "Odbojka",
            "odbojka"
        ],
        [
            "Tenis",
            "tenis"
        ],
        [
            "Stolni tenis",
            "stoni tenis"
        ],
        [
            "Plivanje",
            "plivanje"
        ],
        [
            "Trčanje",
            "trčanje"
        ],
        [
            "Biciklizam",
            "biciklizam"
        ],
        [
            "Skijanje",
            "skijanje"
        ],
        [
            "Klizanje",
            "klizanje"
        ],
        [
            "Boks",
            "boks"
        ],
        [
            "Karate",
            "karate"
        ],
        [
            "Judo",
            "džudo"
        ],
        [
            "Gimnastika",
            "gimnastika"
        ],
        [
            "Atletika",
            "atletika"
        ],
        [
            "Golf",
            "golf"
        ],
        [
            "Šah",
            "šah"
        ],
        [
            "Biljar",
            "bilijar"
        ],
        [
            "Pikado",
            "pikado"
        ],
        [
            "Lopta",
            "lopta"
        ],
        [
            "Gol",
            "gol"
        ],
        [
            "Koš",
            "koš"
        ],
        [
            "Mreža",
            "mreža"
        ],
        [
            "Reket",
            "reket"
        ],
        [
            "Palica",
            "palica"
        ],
        [
            "Kopačke",
            "kopačke"
        ],
        [
            "Tenisice",
            "patike"
        ],
        [
            "Dres",
            "dres"
        ],
        [
            "Trener",
            "trener"
        ],
        [
            "Sudac",
            "sudija"
        ],
        [
            "Navijač",
            "navijač"
        ],
        [
            "Stadion",
            "stadion"
        ],
        [
            "Dvorana",
            "hala"
        ],
        [
            "Teren",
            "teren"
        ],
        [
            "Utakmica",
            "utakmica"
        ],
        [
            "Trening",
            "trening"
        ],
        [
            "Medalja",
            "medalja"
        ],
        [
            "Pečat pobjede",
            "pečat pobede"
        ],
        [
            "Semafor",
            "semafor"
        ],
        [
            "Zviždaljka",
            "pištaljka"
        ],
        [
            "Kaciga za sport",
            "sportska kaciga"
        ],
        [
            "Štitnici",
            "štitnici"
        ],
        [
            "Rukavice",
            "rukavice"
        ],
        [
            "Skateboard",
            "skejtbord"
        ],
        [
            "Surfanje",
            "surfovanje"
        ],
        [
            "Vaterpolo",
            "vaterpolo"
        ],
        [
            "Kuglanje",
            "kuglanje"
        ],
        [
            "Planinarenje",
            "planinarenje"
        ],
        [
            "Ronjenje",
            "ronjenje"
        ],
        [
            "Jedrenje",
            "jedrenje"
        ],
        [
            "Maraton",
            "maraton"
        ],
        [
            "Sprint",
            "sprint"
        ],
        [
            "Skok u dalj",
            "skok udalj"
        ],
        [
            "Skok u vis",
            "skok uvis"
        ],
        [
            "Bacanje kugle",
            "bacanje kugle"
        ],
        [
            "Kladivo",
            "kladivo"
        ],
        [
            "Disk",
            "disk"
        ],
        [
            "Bazen",
            "bazen"
        ],
        [
            "Svlačionica",
            "svlačionica"
        ],
        [
            "Tabela",
            "tabela"
        ],
        [
            "Liga",
            "liga"
        ],
        [
            "Kup",
            "kup"
        ],
        [
            "Kapetan",
            "kapiten"
        ],
        [
            "Rezerva",
            "rezerva"
        ],
        [
            "Napad",
            "napad"
        ],
        [
            "Obrana",
            "odbrana"
        ],
        [
            "Pobjeda",
            "pobeda"
        ],
        [
            "Poraz",
            "poraz"
        ],
        [
            "Neriješeno",
            "nerešeno"
        ],
        [
            "Penal",
            "penal"
        ],
        [
            "Aut",
            "aut"
        ]
    ],
    "Škola": [
        [
            "Škola",
            "škola"
        ],
        [
            "Učionica",
            "učionica"
        ],
        [
            "Klupa",
            "klupa"
        ],
        [
            "Stolica u učionici",
            "stolica u učionici"
        ],
        [
            "Tabla",
            "tabla"
        ],
        [
            "Kreda",
            "kreda"
        ],
        [
            "Spužva za tablu",
            "sunđer za tablu"
        ],
        [
            "Profesor",
            "profesor"
        ],
        [
            "Učitelj",
            "učitelj"
        ],
        [
            "Učenik",
            "učenik"
        ],
        [
            "Učenica",
            "učenica"
        ],
        [
            "Razred",
            "odeljenje"
        ],
        [
            "Dnevnik",
            "dnevnik"
        ],
        [
            "Bilježnica",
            "sveska"
        ],
        [
            "Knjiga",
            "knjiga"
        ],
        [
            "Udžbenik",
            "udžbenik"
        ],
        [
            "Olovka",
            "olovka"
        ],
        [
            "Kemijska olovka",
            "hemijska olovka"
        ],
        [
            "Gumica",
            "gumica"
        ],
        [
            "Šiljilo",
            "rezač"
        ],
        [
            "Ravnalo",
            "lenjir"
        ],
        [
            "Šestar",
            "šestar"
        ],
        [
            "Kalkulator",
            "kalkulator"
        ],
        [
            "Mapa",
            "fascikla"
        ],
        [
            "Torba za školu",
            "školska torba"
        ],
        [
            "Ruksak za školu",
            "školski ranac"
        ],
        [
            "Zadaća",
            "domaći zadatak"
        ],
        [
            "Ispit",
            "ispit"
        ],
        [
            "Test",
            "test"
        ],
        [
            "Ocjena",
            "ocena"
        ],
        [
            "Svjedodžba",
            "svedočanstvo"
        ],
        [
            "Odmor",
            "odmor"
        ],
        [
            "Zvono za školu",
            "školsko zvono"
        ],
        [
            "Knjižnica",
            "biblioteka"
        ],
        [
            "Laboratorij",
            "laboratorija"
        ],
        [
            "Dvorana za tjelesni",
            "sala za fizičko"
        ],
        [
            "Likovni",
            "likovno"
        ],
        [
            "Glazbeni",
            "muzičko"
        ],
        [
            "Matematika",
            "matematika"
        ],
        [
            "Povijest",
            "istorija"
        ],
        [
            "Zemljopis",
            "geografija"
        ],
        [
            "Priroda i društvo",
            "priroda i društvo"
        ],
        [
            "Biologija",
            "biologija"
        ],
        [
            "Kemija",
            "hemija"
        ],
        [
            "Fizika",
            "fizika"
        ],
        [
            "Informatika",
            "informatika"
        ],
        [
            "Engleski",
            "engleski"
        ],
        [
            "Njemački",
            "nemački"
        ],
        [
            "Hrvatski",
            "srpski"
        ],
        [
            "Lektira",
            "lektira"
        ],
        [
            "Esej",
            "esej"
        ],
        [
            "Prezentacija",
            "prezentacija"
        ],
        [
            "Projekt",
            "projekat"
        ],
        [
            "Grupa",
            "grupa"
        ],
        [
            "Hodnik škole",
            "školski hodnik"
        ],
        [
            "Zbornica",
            "zbornica"
        ],
        [
            "Ravnatelj",
            "direktor"
        ],
        [
            "Izlet",
            "ekskurzija"
        ],
        [
            "Matura",
            "matura"
        ],
        [
            "Svjedočanstvo",
            "svedočanstvo"
        ],
        [
            "Prvašić",
            "prvak"
        ],
        [
            "Abeceda",
            "azbuka"
        ],
        [
            "Slovo",
            "slovo"
        ],
        [
            "Broj",
            "broj"
        ],
        [
            "Geometrija",
            "geometrija"
        ],
        [
            "Atlas",
            "atlas"
        ],
        [
            "Globus",
            "globus"
        ],
        [
            "Mikroskop",
            "mikroskop"
        ],
        [
            "Eksperiment",
            "eksperiment"
        ],
        [
            "Flomaster",
            "flomaster"
        ],
        [
            "Markeri",
            "markeri"
        ],
        [
            "Plakat",
            "plakat"
        ]
    ],
    "Posao": [
        [
            "Posao",
            "posao"
        ],
        [
            "Ured",
            "kancelarija"
        ],
        [
            "Radni stol",
            "radni sto"
        ],
        [
            "Sastanak",
            "sastanak"
        ],
        [
            "Pauza",
            "pauza"
        ],
        [
            "Kolega",
            "kolega"
        ],
        [
            "Kolegica",
            "koleginica"
        ],
        [
            "Šef",
            "šef"
        ],
        [
            "Direktor",
            "direktor"
        ],
        [
            "Radnik",
            "radnik"
        ],
        [
            "Radnica",
            "radnica"
        ],
        [
            "Liječnik",
            "lekar"
        ],
        [
            "Medicinska sestra",
            "medicinska sestra"
        ],
        [
            "Učiteljica",
            "učiteljica"
        ],
        [
            "Profesorica",
            "profesorka"
        ],
        [
            "Inženjer",
            "inženjer"
        ],
        [
            "Programer",
            "programer"
        ],
        [
            "Dizajner",
            "dizajner"
        ],
        [
            "Konobar",
            "konobar"
        ],
        [
            "Kuhar",
            "kuvar"
        ],
        [
            "Pekar",
            "pekar"
        ],
        [
            "Vozač",
            "vozač"
        ],
        [
            "Policajac",
            "policajac"
        ],
        [
            "Vatrogasac",
            "vatrogasac"
        ],
        [
            "Poštar",
            "poštar"
        ],
        [
            "Frizer",
            "frizer"
        ],
        [
            "Krojač",
            "krojač"
        ],
        [
            "Stolar",
            "stolar"
        ],
        [
            "Vodoinstalater",
            "vodoinstalater"
        ],
        [
            "Električar",
            "električar"
        ],
        [
            "Mehaničar",
            "mehaničar"
        ],
        [
            "Prodavač",
            "prodavac"
        ],
        [
            "Blagajnik",
            "kasir"
        ],
        [
            "Čistač",
            "čistač"
        ],
        [
            "Zaštitar",
            "obezbeđenje"
        ],
        [
            "Novinar",
            "novinar"
        ],
        [
            "Fotograf",
            "fotograf"
        ],
        [
            "Glumac",
            "glumac"
        ],
        [
            "Pjevač",
            "pevač"
        ],
        [
            "Slikar",
            "slikar"
        ],
        [
            "Vrtlar",
            "baštovan"
        ],
        [
            "Poljoprivrednik",
            "poljoprivrednik"
        ],
        [
            "Ribar",
            "ribar"
        ],
        [
            "Pilot",
            "pilot"
        ],
        [
            "Stjuardesa",
            "stjuardesa"
        ],
        [
            "Odvjetnik",
            "advokat"
        ],
        [
            "Sudac na poslu",
            "sudija na poslu"
        ],
        [
            "Računovođa",
            "računovođa"
        ],
        [
            "Tajnica",
            "sekretarica"
        ],
        [
            "Recepcija",
            "recepcija"
        ],
        [
            "Vizitka",
            "vizitkarta"
        ],
        [
            "Ugovor",
            "ugovor"
        ],
        [
            "Plaća",
            "plata"
        ],
        [
            "Radno vrijeme",
            "radno vreme"
        ],
        [
            "Smjena",
            "smena"
        ],
        [
            "Uniforma",
            "uniforma"
        ],
        [
            "Kaciga na gradilištu",
            "šlem na gradilištu"
        ],
        [
            "Alat",
            "alat"
        ],
        [
            "Kutija za alat",
            "kutija za alat"
        ],
        [
            "Laptop za posao",
            "poslovni laptop"
        ],
        [
            "Službeni mobitel",
            "službeni telefon"
        ],
        [
            "E-mail",
            "imejl"
        ],
        [
            "Dokument",
            "dokument"
        ],
        [
            "Pečat",
            "pečat"
        ],
        [
            "Potpis",
            "potpis"
        ],
        [
            "Kalendar",
            "kalendar"
        ],
        [
            "Rok",
            "rok"
        ],
        [
            "Plan",
            "plan"
        ],
        [
            "Zadatak",
            "zadatak"
        ],
        [
            "Tim",
            "tim"
        ],
        [
            "Kava na poslu",
            "kafa na poslu"
        ],
        [
            "Kopirni uređaj",
            "kopir aparat"
        ]
    ],
    "Tehnologija": [
        [
            "Računalo",
            "računar"
        ],
        [
            "Laptop",
            "laptop"
        ],
        [
            "Tablet",
            "tablet"
        ],
        [
            "Mobitel",
            "mobilni telefon"
        ],
        [
            "Telefon",
            "telefon"
        ],
        [
            "Ekran",
            "ekran"
        ],
        [
            "Tipkovnica",
            "tastatura"
        ],
        [
            "Miš za računar",
            "miš za računar"
        ],
        [
            "Kamera",
            "kamera"
        ],
        [
            "Slušalice",
            "slušalice"
        ],
        [
            "Zvučnik",
            "zvučnik"
        ],
        [
            "Mikrofon",
            "mikrofon"
        ],
        [
            "Punjač za uređaj",
            "punjač za uređaj"
        ],
        [
            "Baterija",
            "baterija"
        ],
        [
            "Kabel",
            "kabl"
        ],
        [
            "USB",
            "USB"
        ],
        [
            "Internet",
            "internet"
        ],
        [
            "Wi-Fi",
            "vaj-faj"
        ],
        [
            "Lozinka",
            "lozinka"
        ],
        [
            "Aplikacija",
            "aplikacija"
        ],
        [
            "Poruka",
            "poruka"
        ],
        [
            "Poziv",
            "poziv"
        ],
        [
            "Video poziv",
            "video poziv"
        ],
        [
            "Fotografija",
            "fotografija"
        ],
        [
            "Snimka",
            "snimak"
        ],
        [
            "Datoteka",
            "fajl"
        ],
        [
            "Mapa na računaru",
            "folder na računaru"
        ],
        [
            "Printer",
            "štampač"
        ],
        [
            "Skener",
            "skener"
        ],
        [
            "Router",
            "ruter"
        ],
        [
            "Server",
            "server"
        ],
        [
            "Cloud servis",
            "cloud servis"
        ],
        [
            "Preglednik",
            "pregledač"
        ],
        [
            "Web stranica",
            "veb stranica"
        ],
        [
            "Link",
            "link"
        ],
        [
            "Profil",
            "profil"
        ],
        [
            "Avatar",
            "avatar"
        ],
        [
            "Emoji",
            "emodži"
        ],
        [
            "Igrica",
            "igrica"
        ],
        [
            "Konzola",
            "konzola"
        ],
        [
            "Kontroler",
            "kontroler"
        ],
        [
            "Pametni televizor",
            "pametni televizor"
        ],
        [
            "Daljinski za TV",
            "daljinski za TV"
        ],
        [
            "Pametni sat",
            "pametni sat"
        ],
        [
            "Dron",
            "dron"
        ],
        [
            "Robot",
            "robot"
        ],
        [
            "Čip",
            "čip"
        ],
        [
            "Ažuriranje",
            "ažuriranje"
        ],
        [
            "Signal",
            "signal"
        ],
        [
            "Računalna mreža",
            "računarska mreža"
        ],
        [
            "Bluetooth",
            "blutut"
        ],
        [
            "Navigacija digitalna",
            "digitalna navigacija"
        ],
        [
            "GPS",
            "GPS"
        ],
        [
            "Mapa u telefonu",
            "mapa u telefonu"
        ],
        [
            "Ekran osjetljiv na dodir",
            "ekran na dodir"
        ],
        [
            "Notifikacija",
            "obaveštenje"
        ],
        [
            "Alarm",
            "alarm"
        ],
        [
            "Kalendar u telefonu",
            "kalendar u telefonu"
        ],
        [
            "Bilješka",
            "beleška"
        ],
        [
            "Pretraga",
            "pretraga"
        ],
        [
            "Kôd",
            "kod"
        ],
        [
            "Lozinka za Wi-Fi",
            "lozinka za Wi-Fi"
        ],
        [
            "Snimanje",
            "snimanje"
        ],
        [
            "Streaming",
            "striming"
        ],
        [
            "Podcast",
            "podkast"
        ],
        [
            "Selfie",
            "selfi"
        ],
        [
            "Filter za sliku",
            "filter za sliku"
        ],
        [
            "Memorija",
            "memorija"
        ],
        [
            "Procesor",
            "procesor"
        ],
        [
            "Tvrdi disk",
            "hard disk"
        ],
        [
            "Monitor",
            "monitor"
        ],
        [
            "Projektor",
            "projektor"
        ]
    ],
    "Putovanja": [
        [
            "Putovanje",
            "putovanje"
        ],
        [
            "Kofer",
            "kofer"
        ],
        [
            "Putna torba",
            "putna torba"
        ],
        [
            "Putovnica",
            "pasoš"
        ],
        [
            "Osobna iskaznica",
            "lična karta"
        ],
        [
            "Avionska karta",
            "avionska karta"
        ],
        [
            "Vozna karta za put",
            "vozna karta za put"
        ],
        [
            "Autobusna karta za put",
            "autobuska karta za put"
        ],
        [
            "Hotel",
            "hotel"
        ],
        [
            "Apartman",
            "apartman"
        ],
        [
            "Recepcija hotela",
            "recepcija hotela"
        ],
        [
            "Soba u hotelu",
            "hotelska soba"
        ],
        [
            "Ključ od sobe",
            "ključ od sobe"
        ],
        [
            "Plaža",
            "plaža"
        ],
        [
            "More na odmoru",
            "more na odmoru"
        ],
        [
            "Planina na odmoru",
            "planina na odmoru"
        ],
        [
            "Grad za vikend",
            "grad za vikend"
        ],
        [
            "Selo za odmor",
            "selo za odmor"
        ],
        [
            "Granica",
            "granica"
        ],
        [
            "Carina",
            "carina"
        ],
        [
            "Aerodrom",
            "aerodrom"
        ],
        [
            "Kolodvor",
            "stanica"
        ],
        [
            "Peron",
            "peron"
        ],
        [
            "Putnički vlak",
            "putnički voz"
        ],
        [
            "Putnički autobus",
            "putnički autobus"
        ],
        [
            "Taksi",
            "taksi"
        ],
        [
            "Rent-a-car",
            "rent-a-car"
        ],
        [
            "Karta grada",
            "mapa grada"
        ],
        [
            "Vodič",
            "vodič"
        ],
        [
            "Turist",
            "turista"
        ],
        [
            "Suvenir",
            "suvenir"
        ],
        [
            "Razglednica",
            "razglednica"
        ],
        [
            "Fotografija s puta",
            "fotografija s puta"
        ],
        [
            "Kamp",
            "kamp"
        ],
        [
            "Šator",
            "šator"
        ],
        [
            "Kampiranje",
            "kampovanje"
        ],
        [
            "Izlet za vikend",
            "izlet za vikend"
        ],
        [
            "Godišnji odmor",
            "godišnji odmor"
        ],
        [
            "Ljetovanje",
            "letovanje"
        ],
        [
            "Zimovanje",
            "zimovanje"
        ],
        [
            "Krstarenje",
            "krstarenje"
        ],
        [
            "Trajekt",
            "trajekt"
        ],
        [
            "Luka",
            "luka"
        ],
        [
            "Most",
            "most"
        ],
        [
            "Tunel",
            "tunel"
        ],
        [
            "Autocesta",
            "auto-put"
        ],
        [
            "Putokaz",
            "putokaz"
        ],
        [
            "Raspored",
            "raspored"
        ],
        [
            "Rezervacija",
            "rezervacija"
        ],
        [
            "Krevet u hotelu",
            "krevet u hotelu"
        ],
        [
            "Doručak u hotelu",
            "doručak u hotelu"
        ],
        [
            "Bazen u hotelu",
            "bazen u hotelu"
        ],
        [
            "Ručnik za plažu",
            "peškir za plažu"
        ],
        [
            "Krema za sunce",
            "krema za sunce"
        ],
        [
            "Sunčane naočale",
            "naočare za sunce"
        ],
        [
            "Fotoaparat",
            "fotoaparat"
        ],
        [
            "Viza",
            "viza"
        ],
        [
            "Valuta",
            "valuta"
        ],
        [
            "Mjenjačnica",
            "menjačnica"
        ],
        [
            "Ručna prtljaga",
            "ručni prtljag"
        ],
        [
            "Prtljaga",
            "prtljag"
        ],
        [
            "Ukrcaj",
            "ukrcavanje"
        ],
        [
            "Let",
            "let"
        ],
        [
            "Kašnjenje",
            "kašnjenje"
        ],
        [
            "Smještaj",
            "smeštaj"
        ],
        [
            "Plan puta",
            "plan puta"
        ],
        [
            "Adresa",
            "adresa"
        ],
        [
            "Navigacija za put",
            "navigacija za put"
        ],
        [
            "Turistički ured",
            "turistička agencija"
        ],
        [
            "Slikanje",
            "slikanje"
        ],
        [
            "Šetnja gradom",
            "šetnja gradom"
        ],
        [
            "Noćenje",
            "noćenje"
        ]
    ],
    "Priroda": [
        [
            "Sunce",
            "sunce"
        ],
        [
            "Mjesec",
            "mesec"
        ],
        [
            "Zvijezda",
            "zvezda"
        ],
        [
            "Nebo",
            "nebo"
        ],
        [
            "Oblak",
            "oblak"
        ],
        [
            "Kiša",
            "kiša"
        ],
        [
            "Snijeg",
            "sneg"
        ],
        [
            "Vjetar",
            "vetar"
        ],
        [
            "Magla",
            "magla"
        ],
        [
            "Duga",
            "duga"
        ],
        [
            "Grom",
            "grom"
        ],
        [
            "Munja",
            "munja"
        ],
        [
            "More",
            "more"
        ],
        [
            "Rijeka",
            "reka"
        ],
        [
            "Jezero",
            "jezero"
        ],
        [
            "Potok",
            "potok"
        ],
        [
            "Vodopad",
            "vodopad"
        ],
        [
            "Planina",
            "planina"
        ],
        [
            "Brdo",
            "brdo"
        ],
        [
            "Dolina",
            "dolina"
        ],
        [
            "Šuma",
            "šuma"
        ],
        [
            "Livada",
            "livada"
        ],
        [
            "Polje",
            "polje"
        ],
        [
            "Plaža prirodna",
            "prirodna plaža"
        ],
        [
            "Pijesak",
            "pesak"
        ],
        [
            "Kamen",
            "kamen"
        ],
        [
            "Stijena",
            "stena"
        ],
        [
            "Zemlja",
            "zemlja"
        ],
        [
            "Blato",
            "blato"
        ],
        [
            "Trava",
            "trava"
        ],
        [
            "Cvijet",
            "cvet"
        ],
        [
            "Drvo",
            "drvo"
        ],
        [
            "List",
            "list"
        ],
        [
            "Grana",
            "grana"
        ],
        [
            "Korijen",
            "koren"
        ],
        [
            "Šišarka",
            "šišarka"
        ],
        [
            "Žir",
            "žir"
        ],
        [
            "Gljiva u šumi",
            "pečurka u šumi"
        ],
        [
            "Mahovina",
            "mahovina"
        ],
        [
            "Pšenica",
            "pšenica"
        ],
        [
            "Kukuruzno polje",
            "kukuruzno polje"
        ],
        [
            "Vinograd",
            "vinograd"
        ],
        [
            "Maslina u prirodi",
            "maslina u prirodi"
        ],
        [
            "Vrt",
            "bašta"
        ],
        [
            "Park",
            "park"
        ],
        [
            "Staza",
            "staza"
        ],
        [
            "Izvor",
            "izvor"
        ],
        [
            "Pećina",
            "pećina"
        ],
        [
            "Otok",
            "ostrvo"
        ],
        [
            "Poluotok",
            "poluostrvo"
        ],
        [
            "Obala",
            "obala"
        ],
        [
            "Zaljev",
            "zaliv"
        ],
        [
            "Luka u prirodi",
            "prirodna luka"
        ],
        [
            "Pustinja",
            "pustinja"
        ],
        [
            "Led",
            "led"
        ],
        [
            "Mraz",
            "mraz"
        ],
        [
            "Rosa",
            "rosa"
        ],
        [
            "Vrućina",
            "vrućina"
        ],
        [
            "Hladnoća",
            "hladnoća"
        ],
        [
            "Proljeće",
            "proleće"
        ],
        [
            "Ljeto",
            "leto"
        ],
        [
            "Jesen",
            "jesen"
        ],
        [
            "Zima",
            "zima"
        ],
        [
            "Zrak",
            "vazduh"
        ],
        [
            "Sjena",
            "senka"
        ],
        [
            "Svjetlost",
            "svetlost"
        ],
        [
            "Miris prirode",
            "miris prirode"
        ],
        [
            "Tišina",
            "tišina"
        ],
        [
            "Pčelinjak",
            "pčelinjak"
        ],
        [
            "Gnijezdo",
            "gnezdo"
        ],
        [
            "Horizont",
            "horizont"
        ]
    ],
    "Prevoz": [
        [
            "Automobil",
            "automobil"
        ],
        [
            "Auto",
            "auto"
        ],
        [
            "Autobus",
            "autobus"
        ],
        [
            "Vlak",
            "voz"
        ],
        [
            "Tramvaj",
            "tramvaj"
        ],
        [
            "Trolejbus",
            "trolejbus"
        ],
        [
            "Taksi vozilo",
            "taksi vozilo"
        ],
        [
            "Motocikl",
            "motor"
        ],
        [
            "Skuter",
            "skuter"
        ],
        [
            "Bicikl za prevoz",
            "bicikl za prevoz"
        ],
        [
            "Kamion",
            "kamion"
        ],
        [
            "Kombi",
            "kombi"
        ],
        [
            "Traktor",
            "traktor"
        ],
        [
            "Avion",
            "avion"
        ],
        [
            "Helikopter",
            "helikopter"
        ],
        [
            "Brod",
            "brod"
        ],
        [
            "Čamac",
            "čamac"
        ],
        [
            "Trajektna linija",
            "trajektna linija"
        ],
        [
            "Metro",
            "metro"
        ],
        [
            "Stanica",
            "stanica"
        ],
        [
            "Autobusno stajalište",
            "autobusko stajalište"
        ],
        [
            "Kolodvor za prevoz",
            "železnička stanica"
        ],
        [
            "Terminal",
            "terminal"
        ],
        [
            "Cesta",
            "put"
        ],
        [
            "Ulica",
            "ulica"
        ],
        [
            "Izlaz s autoceste",
            "izlaz sa auto-puta"
        ],
        [
            "Prometni semafor",
            "saobraćajni semafor"
        ],
        [
            "Pješački prijelaz",
            "pešački prelaz"
        ],
        [
            "Kružni tok",
            "kružni tok"
        ],
        [
            "Most na cesti",
            "most na putu"
        ],
        [
            "Cestovni tunel",
            "putni tunel"
        ],
        [
            "Parkiralište",
            "parking"
        ],
        [
            "Garaža za auto",
            "garaža za auto"
        ],
        [
            "Volan",
            "volan"
        ],
        [
            "Kočnica",
            "kočnica"
        ],
        [
            "Gas",
            "gas"
        ],
        [
            "Mjenjač",
            "menjač"
        ],
        [
            "Guma",
            "guma"
        ],
        [
            "Rezervna guma",
            "rezervna guma"
        ],
        [
            "Motor vozila",
            "motor vozila"
        ],
        [
            "Prtljažnik",
            "gepek"
        ],
        [
            "Sjedište",
            "sedište"
        ],
        [
            "Pojas",
            "pojas"
        ],
        [
            "Kaciga za motor",
            "kaciga za motor"
        ],
        [
            "Mjesečna karta",
            "mesečna karta"
        ],
        [
            "Vozni red",
            "red vožnje"
        ],
        [
            "Putnik",
            "putnik"
        ],
        [
            "Vozač autobusa",
            "vozač autobusa"
        ],
        [
            "Kontrolor",
            "kontrolor"
        ],
        [
            "Kondukter",
            "kondukter"
        ],
        [
            "Gužva u prometu",
            "gužva u saobraćaju"
        ],
        [
            "Kolona",
            "kolona"
        ],
        [
            "Skretanje",
            "skretanje"
        ],
        [
            "Raskrižje",
            "raskrsnica"
        ],
        [
            "Benzinska postaja",
            "benzinska pumpa"
        ],
        [
            "Gorivo",
            "gorivo"
        ],
        [
            "Benzin",
            "benzin"
        ],
        [
            "Dizel",
            "dizel"
        ],
        [
            "Električni auto",
            "električni auto"
        ],
        [
            "Punjač za auto",
            "punjač za auto"
        ],
        [
            "Navigacija u autu",
            "navigacija u autu"
        ],
        [
            "Retrovizor",
            "retrovizor"
        ],
        [
            "Brisači",
            "brisači"
        ],
        [
            "Far",
            "far"
        ],
        [
            "Sirena",
            "sirena"
        ],
        [
            "Tablica",
            "registracija"
        ],
        [
            "Taxi aplikacija",
            "taksi aplikacija"
        ],
        [
            "Pruga",
            "pruga"
        ],
        [
            "Tračnice",
            "šine"
        ],
        [
            "Peron za voz",
            "peron za voz"
        ],
        [
            "Brodska luka",
            "brodska luka"
        ]
    ],
    "Odeća": [
        [
            "Majica",
            "majica"
        ],
        [
            "Košulja",
            "košulja"
        ],
        [
            "Hlače",
            "pantalone"
        ],
        [
            "Traperice",
            "farmerke"
        ],
        [
            "Suknja",
            "suknja"
        ],
        [
            "Haljina",
            "haljina"
        ],
        [
            "Jakna",
            "jakna"
        ],
        [
            "Kaput",
            "kaput"
        ],
        [
            "Džemper",
            "džemper"
        ],
        [
            "Duks",
            "duks"
        ],
        [
            "Trenerka",
            "trenerka"
        ],
        [
            "Kratke hlače",
            "šorts"
        ],
        [
            "Donje rublje",
            "donji veš"
        ],
        [
            "Čarapa",
            "čarapa"
        ],
        [
            "Cipela",
            "cipela"
        ],
        [
            "Tenisica",
            "patika"
        ],
        [
            "Čizma",
            "čizma"
        ],
        [
            "Sandala",
            "sandala"
        ],
        [
            "Papuča",
            "papuča"
        ],
        [
            "Kapa",
            "kapa"
        ],
        [
            "Šešir",
            "šešir"
        ],
        [
            "Šal",
            "šal"
        ],
        [
            "Rukavica",
            "rukavica"
        ],
        [
            "Remen",
            "kaiš"
        ],
        [
            "Torba",
            "torba"
        ],
        [
            "Ruksak",
            "ranac"
        ],
        [
            "Novčanik",
            "novčanik"
        ],
        [
            "Sat na ruci",
            "ručni sat"
        ],
        [
            "Naušnica",
            "minđuša"
        ],
        [
            "Ogrlica",
            "ogrlica"
        ],
        [
            "Narukvica",
            "narukvica"
        ],
        [
            "Prsten",
            "prsten"
        ],
        [
            "Naočale",
            "naočare"
        ],
        [
            "Naočale za sunce",
            "naočare za sunce"
        ],
        [
            "Kravata",
            "kravata"
        ],
        [
            "Leptir mašna",
            "leptir mašna"
        ],
        [
            "Odijelo",
            "odelo"
        ],
        [
            "Sako",
            "sako"
        ],
        [
            "Radna uniforma",
            "radna uniforma"
        ],
        [
            "Pregača",
            "kecelja"
        ],
        [
            "Pidžama",
            "pidžama"
        ],
        [
            "Kupaći kostim",
            "kupaći kostim"
        ],
        [
            "Ručnik",
            "peškir"
        ],
        [
            "Kabanica",
            "kišna kabanica"
        ],
        [
            "Kišobran",
            "kišobran"
        ],
        [
            "Gumb",
            "dugme"
        ],
        [
            "Patentni zatvarač",
            "rajsferšlus"
        ],
        [
            "Vezica",
            "pertla"
        ],
        [
            "Džep",
            "džep"
        ],
        [
            "Kapuljača",
            "kapuljača"
        ],
        [
            "Vješalica",
            "vešalica"
        ],
        [
            "Ormar za odjeću",
            "ormar za odeću"
        ],
        [
            "Ogledalo za oblačenje",
            "ogledalo za oblačenje"
        ],
        [
            "Peglanje",
            "peglanje"
        ],
        [
            "Pranje rublja",
            "pranje veša"
        ],
        [
            "Sušenje rublja",
            "sušenje veša"
        ],
        [
            "Moda",
            "moda"
        ],
        [
            "Stil",
            "stil"
        ],
        [
            "Veličina",
            "veličina"
        ],
        [
            "Boja",
            "boja"
        ],
        [
            "Materijal",
            "materijal"
        ],
        [
            "Pamuk",
            "pamuk"
        ],
        [
            "Vuna",
            "vuna"
        ],
        [
            "Kožna jakna",
            "kožna jakna"
        ],
        [
            "Svila",
            "svila"
        ],
        [
            "Jeans",
            "džins"
        ],
        [
            "Džepna maramica",
            "džepna maramica"
        ],
        [
            "Kostim",
            "kostim"
        ],
        [
            "Maska za lice",
            "maska za lice"
        ],
        [
            "Svečana kravata",
            "svečana kravata"
        ],
        [
            "Broš",
            "broš"
        ],
        [
            "Torbica",
            "tašnica"
        ]
    ],
    "Zdravlje": [
        [
            "Zdravlje",
            "zdravlje"
        ],
        [
            "Liječnik opće prakse",
            "lekar opšte prakse"
        ],
        [
            "Doktorica",
            "doktorka"
        ],
        [
            "Ambulanta",
            "ambulanta"
        ],
        [
            "Ordinacija",
            "ordinacija"
        ],
        [
            "Bolnica",
            "bolnica"
        ],
        [
            "Ljekarna",
            "apoteka"
        ],
        [
            "Lijek",
            "lek"
        ],
        [
            "Tableta",
            "tableta"
        ],
        [
            "Sirup",
            "sirup"
        ],
        [
            "Vitamin",
            "vitamin"
        ],
        [
            "Toplomjer",
            "toplomer"
        ],
        [
            "Zavoj",
            "zavoj"
        ],
        [
            "Flaster",
            "flaster"
        ],
        [
            "Maska",
            "maska"
        ],
        [
            "Rukavice medicinske",
            "medicinske rukavice"
        ],
        [
            "Pregled",
            "pregled"
        ],
        [
            "Recept",
            "recept"
        ],
        [
            "Kontrola",
            "kontrola"
        ],
        [
            "Čekaonica",
            "čekaonica"
        ],
        [
            "Zubar",
            "zubar"
        ],
        [
            "Četkica za zube",
            "četkica za zube"
        ],
        [
            "Pasta za zube",
            "pasta za zube"
        ],
        [
            "Zub",
            "zub"
        ],
        [
            "Oko",
            "oko"
        ],
        [
            "Uho",
            "uho"
        ],
        [
            "Nos",
            "nos"
        ],
        [
            "Grlo",
            "grlo"
        ],
        [
            "Ruka",
            "ruka"
        ],
        [
            "Noga",
            "noga"
        ],
        [
            "Leđa",
            "leđa"
        ],
        [
            "Glava",
            "glava"
        ],
        [
            "Srce",
            "srce"
        ],
        [
            "Stomak",
            "stomak"
        ],
        [
            "Koža",
            "koža"
        ],
        [
            "Kosa",
            "kosa"
        ],
        [
            "San",
            "san"
        ],
        [
            "Kratak odmor",
            "kratak odmor"
        ],
        [
            "Čaša vode",
            "čaša vode"
        ],
        [
            "Šetnja",
            "šetnja"
        ],
        [
            "Lagano trčanje",
            "lagano trčanje"
        ],
        [
            "Vježba",
            "vežba"
        ],
        [
            "Teretana",
            "teretana"
        ],
        [
            "Joga",
            "joga"
        ],
        [
            "Disanje",
            "disanje"
        ],
        [
            "Temperatura",
            "temperatura"
        ],
        [
            "Kašalj",
            "kašalj"
        ],
        [
            "Prehlada",
            "prehlada"
        ],
        [
            "Alergija",
            "alergija"
        ],
        [
            "Kapi za nos",
            "kapi za nos"
        ],
        [
            "Krema",
            "krema"
        ],
        [
            "Masaža",
            "masaža"
        ],
        [
            "Fizioterapija",
            "fizioterapija"
        ],
        [
            "Naočale za vid",
            "naočare za vid"
        ],
        [
            "Leća",
            "sočivo"
        ],
        [
            "Sluh",
            "sluh"
        ],
        [
            "Puls",
            "puls"
        ],
        [
            "Tlak",
            "pritisak"
        ],
        [
            "Prehrana",
            "ishrana"
        ],
        [
            "Svježe voće",
            "sveže voće"
        ],
        [
            "Svježe povrće",
            "sveže povrće"
        ],
        [
            "Zdrav doručak",
            "zdrav doručak"
        ],
        [
            "Čaj za grlo",
            "čaj za grlo"
        ],
        [
            "Med za grlo",
            "med za grlo"
        ],
        [
            "Sapunjanje",
            "pranje sapunom"
        ],
        [
            "Higijena",
            "higijena"
        ],
        [
            "Tuširanje",
            "tuširanje"
        ],
        [
            "Ručnik za zdravlje",
            "peškir za zdravlje"
        ],
        [
            "Dezinfekcija",
            "dezinfekcija"
        ],
        [
            "Prva pomoć",
            "prva pomoć"
        ]
    ],
    "Zabava": [
        [
            "Film",
            "film"
        ],
        [
            "Serija",
            "serija"
        ],
        [
            "Kino",
            "bioskop"
        ],
        [
            "Kazalište",
            "pozorište"
        ],
        [
            "Koncert",
            "koncert"
        ],
        [
            "Glazba",
            "muzika"
        ],
        [
            "Pjesma",
            "pesma"
        ],
        [
            "Glavni vokal",
            "glavni vokal"
        ],
        [
            "Bend",
            "bend"
        ],
        [
            "Gitara",
            "gitara"
        ],
        [
            "Klavir",
            "klavir"
        ],
        [
            "Bubanj",
            "bubanj"
        ],
        [
            "Ples",
            "ples"
        ],
        [
            "Zabava",
            "žurka"
        ],
        [
            "Rođendan",
            "rođendan"
        ],
        [
            "Poklon",
            "poklon"
        ],
        [
            "Balon",
            "balon"
        ],
        [
            "Torta",
            "torta"
        ],
        [
            "Svijeća",
            "sveća"
        ],
        [
            "Društvena igra",
            "društvena igra"
        ],
        [
            "Karte za igru",
            "karte za igru"
        ],
        [
            "Kockica",
            "kockica"
        ],
        [
            "Puzzle",
            "slagalica"
        ],
        [
            "Kviz",
            "kviz"
        ],
        [
            "Karaoke",
            "karaoke"
        ],
        [
            "Karaoke mikrofon",
            "karaoke mikrofon"
        ],
        [
            "Scena",
            "scena"
        ],
        [
            "Publika",
            "publika"
        ],
        [
            "Aplauz",
            "aplauz"
        ],
        [
            "Ulaznica",
            "ulaznica"
        ],
        [
            "Maskenbal",
            "maskenbal"
        ],
        [
            "Maska za maskenbal",
            "maska za maskenbal"
        ],
        [
            "Strip",
            "strip"
        ],
        [
            "Knjiga za odmor",
            "knjiga za odmor"
        ],
        [
            "Roman",
            "roman"
        ],
        [
            "Časopis",
            "časopis"
        ],
        [
            "Hobi",
            "hobi"
        ],
        [
            "Crtanje",
            "crtanje"
        ],
        [
            "Likovna radionica",
            "likovna radionica"
        ],
        [
            "Fotografiranje",
            "fotografisanje"
        ],
        [
            "Video igra",
            "video igra"
        ],
        [
            "Igraća konzola",
            "igraća konzola"
        ],
        [
            "Gamepad",
            "gejmped"
        ],
        [
            "Igraonica",
            "igraonica"
        ],
        [
            "Park za zabavu",
            "zabavni park"
        ],
        [
            "Vrtuljak",
            "ringišpil"
        ],
        [
            "Klovn",
            "klovn"
        ],
        [
            "Mađioničar",
            "mađioničar"
        ],
        [
            "Cirkus",
            "cirkus"
        ],
        [
            "Izložba",
            "izložba"
        ],
        [
            "Muzej",
            "muzej"
        ],
        [
            "Festival",
            "festival"
        ],
        [
            "Sajam",
            "sajam"
        ],
        [
            "Piknik",
            "piknik"
        ],
        [
            "Izlazak",
            "izlazak"
        ],
        [
            "Kafić",
            "kafić"
        ],
        [
            "Diskoteka",
            "diskoteka"
        ],
        [
            "DJ",
            "di-džej"
        ],
        [
            "Titlovi",
            "titlovi"
        ],
        [
            "Epizoda",
            "epizoda"
        ],
        [
            "Netflix",
            "Netflix"
        ],
        [
            "Kokice u kinu",
            "kokice u bioskopu"
        ],
        [
            "Sjedalo u kinu",
            "sedište u bioskopu"
        ],
        [
            "Humor",
            "humor"
        ],
        [
            "Šala",
            "šala"
        ],
        [
            "Meme",
            "mim"
        ],
        [
            "Audio emisija",
            "audio emisija"
        ],
        [
            "Stream",
            "strim"
        ],
        [
            "Publika online",
            "online publika"
        ],
        [
            "Navijanje",
            "navijanje"
        ]
    ],
    "Balkan": [
        [
            "Kafana",
            "kafana"
        ],
        [
            "Pekara",
            "pekara"
        ],
        [
            "Tržnica",
            "pijaca"
        ],
        [
            "Susjed",
            "komšija"
        ],
        [
            "Susjedstvo",
            "komšiluk"
        ],
        [
            "Džezva",
            "džezva"
        ],
        [
            "Fildžan",
            "fildžan"
        ],
        [
            "Kava u kafani",
            "kafa u kafani"
        ],
        [
            "Rakija",
            "rakija"
        ],
        [
            "Roštilj u dvorištu",
            "roštilj u dvorištu"
        ],
        [
            "Ćevabdžinica",
            "ćevabdžinica"
        ],
        [
            "Buregdžinica",
            "buregdžinica"
        ],
        [
            "Sarma za praznik",
            "sarma za praznik"
        ],
        [
            "Ajvar iz zimnice",
            "ajvar iz zimnice"
        ],
        [
            "Zimnica",
            "zimnica"
        ],
        [
            "Slava",
            "slava"
        ],
        [
            "Svadba",
            "svadba"
        ],
        [
            "Kolo",
            "kolo"
        ],
        [
            "Tamburica",
            "tamburica"
        ],
        [
            "Harmonika",
            "harmonika"
        ],
        [
            "Truba",
            "truba"
        ],
        [
            "Narodna pjesma",
            "narodna pesma"
        ],
        [
            "Sevdah",
            "sevdah"
        ],
        [
            "Klapa",
            "klapa"
        ],
        [
            "Riva",
            "riva"
        ],
        [
            "Čaršija",
            "čaršija"
        ],
        [
            "Mahala",
            "mahala"
        ],
        [
            "Avlija",
            "avlija"
        ],
        [
            "Sokak",
            "sokak"
        ],
        [
            "Kaldrma",
            "kaldrma"
        ],
        [
            "Ćilim",
            "ćilim"
        ],
        [
            "Šporet na drva",
            "šporet na drva"
        ],
        [
            "Drva",
            "drva"
        ],
        [
            "Šupa",
            "šupa"
        ],
        [
            "Bunar",
            "bunar"
        ],
        [
            "Seoski vrt",
            "seoska bašta"
        ],
        [
            "Šljivik",
            "šljivik"
        ],
        [
            "Vinograd za berbu",
            "vinograd za berbu"
        ],
        [
            "Berba",
            "berba"
        ],
        [
            "Seoski put",
            "seoski put"
        ],
        [
            "Seoski autobus",
            "seoski autobus"
        ],
        [
            "Autobusna stanica",
            "autobuska stanica"
        ],
        [
            "Tetka",
            "tetka"
        ],
        [
            "Ujak",
            "ujak"
        ],
        [
            "Stric",
            "stric"
        ],
        [
            "Baka",
            "baka"
        ],
        [
            "Djed",
            "deda"
        ],
        [
            "Kum",
            "kum"
        ],
        [
            "Kuma",
            "kuma"
        ],
        [
            "Gosti",
            "gosti"
        ],
        [
            "Meze",
            "meze"
        ],
        [
            "Sok od bazge",
            "sok od zove"
        ],
        [
            "Kiseli kupus",
            "kiseli kupus"
        ],
        [
            "Domaća juha",
            "domaća supa"
        ],
        [
            "Pogača",
            "pogača"
        ],
        [
            "Lepinja",
            "lepinja"
        ],
        [
            "Kajmak na stolu",
            "kajmak na stolu"
        ],
        [
            "Paprikaš",
            "paprikaš"
        ],
        [
            "Gulaš",
            "gulaš"
        ],
        [
            "Baklava",
            "baklava"
        ],
        [
            "Tulumbe",
            "tulumbe"
        ],
        [
            "Uštipci",
            "uštipci"
        ],
        [
            "Priganice",
            "priganice"
        ],
        [
            "Domaća serija",
            "domaća serija"
        ],
        [
            "Dnevnik na TV-u",
            "dnevnik na TV-u"
        ],
        [
            "Daljinski kod kuće",
            "daljinski kod kuće"
        ],
        [
            "Terasa kafića",
            "terasa kafića"
        ],
        [
            "Promaja",
            "promaja"
        ],
        [
            "Papirnati ručnik",
            "papirni ubrus"
        ],
        [
            "Vikendica",
            "vikendica"
        ],
        [
            "Jadransko more",
            "Jadransko more"
        ]
    ]
}

@dataclass
class WordIssue:
    word_id: str
    field: str
    message: str

@dataclass
class WordValidationResult:
    quality_warnings: list[WordIssue] = field(default_factory=list)

    def add(self, word_id: str, field: str, message: str) -> None:
        self.quality_warnings.append(WordIssue(word_id, field, message))


def ascii_fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def token_set(value: str) -> set[str]:
    return {token for token in re.split(r"[^\w]+", ascii_fold(value)) if token}


def stable_index(value: str, modulo: int) -> int:
    return sum((index + 1) * ord(ch) for index, ch in enumerate(value)) % modulo


def remove_direct_hints(hr: str, sr: str, hints: list[str]) -> list[str]:
    blocked_tokens = token_set(hr) | token_set(sr)
    exact_words = {ascii_fold(hr), ascii_fold(sr)}
    clean: list[str] = []
    for hint in hints:
        hint_text = str(hint).strip()
        if not hint_text:
            continue
        hint_fold = ascii_fold(hint_text)
        if hint_fold in exact_words:
            continue
        if token_set(hint_text) & blocked_tokens:
            continue
        if hint_fold in BANNED_DIRECT_HINTS:
            continue
        if hint_text not in clean:
            clean.append(hint_text)
    return clean


def semantic_hint_pool(hr: str, sr: str, category: str, index: int) -> list[str]:
    category_pool = category_exact_hint_pool(category, hr, sr)
    if category_pool:
        return category_pool[:4]
    hr_fold = ascii_fold(hr)
    sr_fold = ascii_fold(sr)
    hints: list[str] = []
    has_exact_match = False
    for key, pool in EXACT_HINT_POOLS.items():
        key_fold = ascii_fold(key)
        if key_fold in {hr_fold, sr_fold}:
            hints.extend(pool)
            has_exact_match = True
            break
    if not hints:
        for key, pool in EXACT_HINT_POOLS.items():
            key_fold = ascii_fold(key)
            if len(key_fold) >= 5 and (key_fold in token_set(hr) or key_fold in token_set(sr)):
                hints.extend(pool)
                has_exact_match = True
                break
    bank = CATEGORY_HINT_BANKS[category]
    scene = bank[stable_index(f"{category}:{hr}:{sr}:{index}", len(bank))]
    hints.extend(scene)
    offset_scene = bank[(stable_index(f"extra:{sr}:{hr}", len(bank)) + index) % len(bank)]
    hints.extend(offset_scene)
    variant_pool = [hint for bank_scene in bank for hint in bank_scene]
    variant = variant_pool[stable_index(f"variant:{category}:{hr}:{sr}:{index}", len(variant_pool))]
    if has_exact_match:
        blended_hints = hints[:4]
    else:
        blended_hints = [scene[0], variant, scene[2], scene[3], scene[1], offset_scene[0], offset_scene[2], offset_scene[3]]
    hints = remove_direct_hints(hr, sr, blended_hints)
    if len(hints) < 4:
        for scene in bank:
            hints.extend(remove_direct_hints(hr, sr, scene))
            unique = []
            for hint in hints:
                if hint not in unique:
                    unique.append(hint)
            hints = unique
            if len(hints) >= 4:
                break
    return hints[:4]


def difficulty_for(index: int) -> str:
    if index % 5 == 0:
        return "hard"
    if index % 3 == 0:
        return "easy"
    return "normal"


def build_words() -> list[dict]:
    words: list[dict] = []
    for category, pairs in RAW_CATEGORY_WORDS.items():
        prefix = ascii_fold(category).replace(" ", "_")
        for index, pair in enumerate(pairs, start=1):
            hr, sr = pair
            hr, sr = WORD_RENAMES.get((category, hr, sr), (hr, sr))
            words.append({
                "id": f"{prefix}_{index:03d}",
                "hr": hr,
                "sr": sr,
                "category": category,
                "difficulty": difficulty_for(index),
                "hint_pool": semantic_hint_pool(hr, sr, category, index),
            })
    return words


def validate_words(words: list[dict], *, strict: bool = False) -> WordValidationResult:
    result = WordValidationResult()
    if len(words) != 1000:
        result.add("database", "count", f"Expected exactly 1000 words, found {len(words)}")
    ids: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    for word in words:
        word_id = str(word.get("id", "<missing>"))
        for field_name in ("id", "hr", "sr", "category", "difficulty", "hint_pool"):
            if field_name not in word:
                result.add(word_id, field_name, "Missing required field")
                continue
            if field_name != "hint_pool" and not str(word[field_name]).strip():
                result.add(word_id, field_name, "Empty field")
        if word_id in ids:
            result.add(word_id, "id", "Duplicate id")
        ids.add(word_id)
        hr = str(word.get("hr", "")).strip()
        sr = str(word.get("sr", "")).strip()
        pair = (hr.casefold(), sr.casefold())
        if pair in pairs:
            result.add(word_id, "word", f"Duplicate word pair: {hr} / {sr}")
        pairs.add(pair)
        category = str(word.get("category", ""))
        if category not in WORD_CATEGORIES:
            result.add(word_id, "category", f"Invalid category: {category}")
        difficulty = str(word.get("difficulty", ""))
        if difficulty not in ALLOWED_DIFFICULTIES:
            result.add(word_id, "difficulty", f"Invalid difficulty: {difficulty}")
        hints = word.get("hint_pool", [])
        if not isinstance(hints, list) or not 3 <= len(hints) <= 4:
            result.add(word_id, "hint_pool", "hint_pool must contain 3-4 hints")
            hints = []
        blocked_tokens = token_set(hr) | token_set(sr)
        for hint in hints:
            hint_text = str(hint).strip()
            if not hint_text:
                result.add(word_id, "hint_pool", "Empty hint")
                continue
            hint_fold = ascii_fold(hint_text)
            if hint_fold in {ascii_fold(hr), ascii_fold(sr)}:
                result.add(word_id, "hint_pool", f"Hint reveals exact word: {hint_text}")
            if hint_fold in BANNED_DIRECT_HINTS:
                result.add(word_id, "hint_pool", f"Direct banned hint: {hint_text}")
        for field_name in ("hr", "sr"):
            text = str(word.get(field_name, "")).strip()
            lower = text.casefold()
            if lower.startswith(SUSPICIOUS_PREFIXES):
                result.add(word_id, field_name, f"Suspicious generated phrase: {text}")
            folded = ascii_fold(text)
            if folded in ASCII_DIACRITIC_EXPECTATIONS and not any(ch in text for ch in "čćšđžČĆŠĐŽ"):
                result.add(word_id, field_name, f"Suspicious missing diacritics: {text}")
    if strict and result.quality_warnings:
        details = "\n".join(f"- {issue.word_id} [{issue.field}]: {issue.message}" for issue in result.quality_warnings[:30])
        raise ValueError(f"Word validation failed with {len(result.quality_warnings)} issue(s):\n{details}")
    return result


def hint_repetition_warnings(words: list[dict]) -> list[str]:
    exact: defaultdict[tuple[str, ...], list[str]] = defaultdict(list)
    first_three: defaultdict[tuple[str, ...], list[str]] = defaultdict(list)
    for word in words:
        hints = tuple(word.get("hint_pool", []))
        exact[hints].append(word["id"])
        first_three[hints[:3]].append(word["id"])
    warnings: list[str] = []
    for hints, ids in sorted(exact.items(), key=lambda item: len(item[1]), reverse=True):
        if len(ids) > 3:
            warnings.append(f"Exact hint_pool repeated {len(ids)} times: {hints} -> {', '.join(ids[:8])}")
    for hints, ids in sorted(first_three.items(), key=lambda item: len(item[1]), reverse=True):
        if len(ids) > 4:
            warnings.append(f"First 3 hints repeated {len(ids)} times: {hints} -> {', '.join(ids[:8])}")
    return warnings


def random_hint(word: dict) -> str:
    hints = word.get("hint_pool") or []
    if hints:
        return random.choice(hints)
    return word.get("hint", "Slušaj asocijacije i uklopi se.")

STARTER_WORDS = build_words()
validate_words(STARTER_WORDS, strict=True)


def normalize_category(category: str | None) -> str:
    if category in WORD_CATEGORIES:
        return category
    return DEFAULT_CATEGORY


def words_for_category(category: str | None) -> list[dict]:
    selected_category = normalize_category(category)
    if selected_category == DEFAULT_CATEGORY:
        return STARTER_WORDS
    filtered_words = [word for word in STARTER_WORDS if word["category"] == selected_category]
    return filtered_words or STARTER_WORDS
