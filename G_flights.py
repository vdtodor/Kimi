import sys
import os

def parsiraj_vreme(vreme_str):
    """
    Konvertuje string oblika "HH:MM" u minute od pocetka dana.
    Vraca integer ili podize ValueError.
    """
    if ':' not in vreme_str:
        raise ValueError
    hh, mm = map(int, vreme_str.split(':'))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise ValueError
    return hh * 60 + mm

def formatiraj_cenu(cena):
    """
    Formatira realan broj na dve decimale.
    """
    return "{:.2f}".format(cena)

def ucitaj_letove(putanja):
    """
    Ucitava i parsira podatke o letovima iz datoteke.
    Vraca recnik direktnih letova ili podize izuzetak.
    """
    if not os.path.exists(putanja):
        raise FileNotFoundError
    
    letovi = {}
    
    with open(putanja, 'r', encoding='utf-8') as f:
        for linija in f:
            linija = linija.strip()
            if not linija:
                continue
            
            # Validacija formata linije: tekst|tekst->tekst|...
            delovi = linija.split('|')
            if len(delovi) != 3:
                raise Exception("Neispravan format linije")
            
            aviokompanija = delovi[0]
            ruta = delovi[1]
            letovi_info = delovi[2]
            
            if '->' not in ruta:
                raise Exception("Neispravan format rute")
                
            gradovi = ruta.split('->')
            if len(gradovi) != 2:
                raise Exception("Neispravan format gradova")
                
            grad_polaska, grad_dolaska = gradovi[0], gradovi[1]
            
            # Parsiranje letova
            # Format: hh:mm-hh:mm,price;...
            niz_letova = letovi_info.split(';')
            for info in niz_letova:
                if ',' not in info or '-' not in info:
                    raise Exception("Neispravan format leta")
                
                vremena_deo, cena_str = info.split(',')
                vremena = vremena_deo.split('-')
                if len(vremena) != 2:
                    raise Exception("Neispravan format vremena")
                    
                vreme_pol_str, vreme_dol_str = vremena
                
                try:
                    vreme_pol_min = parsiraj_vreme(vreme_pol_str)
                    vreme_dol_min = parsiraj_vreme(vreme_dol_str)
                    cena = float(cena_str)
                except ValueError:
                    raise Exception("Neispravna vrednost vremena ili cene")
                
                let = {
                    'aviokompanija': aviokompanija,
                    'grad_polaska': grad_polaska,
                    'grad_dolaska': grad_dolaska,
                    'vreme_pol_str': vreme_pol_str,
                    'vreme_dol_str': vreme_dol_str,
                    'vreme_pol_min': vreme_pol_min,
                    'vreme_dol_min': vreme_dol_min,
                    'trajanje': vreme_dol_min - vreme_pol_min,
                    'cena': cena
                }
                
                kljuc = (grad_polaska, grad_dolaska)
                if kljuc not in letovi:
                    letovi[kljuc] = []
                letovi[kljuc].append(let)
                
    return letovi

def obradi_direktne_letove(letovi):
    """
    Formira datoteku flights_direct.txt.
    """
    izlazno_ime = "flights_direct.txt"
    with open(izlazno_ime, 'w', encoding='utf-8') as f:
        # Sortiranje parova gradova leksikografski
        parovi_gradova = sorted(letovi.keys())
        
        for par in parovi_gradova:
            grad_pol, grad_dol = par
            f.write(f"{grad_pol}->{grad_dol}\n")
            
            # Grupisanj letova po aviokompaniji
            letovi_na_ruti = letovi[par]
            po_kompanijama = {}
            for let in letovi_na_ruti:
                kompanija = let['aviokompanija']
                if kompanija not in po_kompanijama:
                    po_kompanijama[kompanija] = []
                po_kompanijama[kompanija].append(let)
            
            # Sortiranje aviokompanija leksikografski
            kompanije_sorted = sorted(po_kompanijama.keys())
            
            for komp in kompanije_sorted:
                f.write(f"{komp}\n")
                
                # Sortiranje letova hronoloski rastuce
                letovi_kompanije = po_kompanijama[komp]
                letovi_kompanije.sort(key=lambda x: x['vreme_pol_min'])
                
                for l in letovi_kompanije:
                    cena_txt = formatiraj_cenu(l['cena'])
                    f.write(f"  {l['vreme_pol_str']}-{l['vreme_dol_str']},{cena_txt}\n")

def obradi_indirektne_letove(letovi, trazeni_polazak, trazeni_dolazak):
    """
    Formira datoteku flights_indirect.txt za zadati par gradova.
    """
    izlazno_ime = "flights_indirect.txt"
    
    # Pronalazenje mogucih medjugradova
    # Grad X je medjugrad ako postoji let trazeni_polazak -> X i X -> trazeni_dolazak
    medjugradovi = []
    
    # Prvi korak: naci sve rute koje krecu iz trazeni_polazak
    for (pol, dol) in letovi.keys():
        if pol == trazeni_polazak:
            # Provera da li postoji ruta od dol do trazeni_dolazak
            if (dol, trazeni_dolazak) in letovi:
                medjugradovi.append(dol)
    
    # Sortiranje medjugradova leksikografski
    medjugradovi.sort()
    
    with open(izlazno_ime, 'w', encoding='utf-8') as f:
        for medju in medjugradovi:
            # Dohvatanje letova
            prvi_letovi = letovi[(trazeni_polazak, medju)]
            drugi_letovi_kandidati = letovi[(medju, trazeni_dolazak)]
            
            # Filtriranje i sparivanje
            # Potrebno je prvo sortirati letove prvog segmenta
            # Kriterijum: vreme polaska, trajanje, aviokompanija
            prvi_letovi_sortirani = sorted(
                prvi_letovi, 
                key=lambda x: (x['vreme_pol_min'], x['trajanje'], x['aviokompanija'])
            )
            
            ima_ispisa_za_medjugrad = False
            buffer_ispisa = [] 
            # Koristimo buffer da ne bismo ispisali zaglavlje ako nema validnih konekcija?
            # Tekst kaze "Za svaki identifikovani grad ... ispisati ... u formatu ... u jednom redu, a zatim..."
            # Ako nema validnih letova sa presedanjem preko tog grada (zbog vremena), da li ispisujemo grad?
            # "pronadju svi letovi koji zahtevaju jedno presedanje. Za svaki identifikovani grad ... ispisati"
            # Ako nema letova, grad nije identifikovan kao tacka presedanja u validnom smislu?
            # Pretpostavicemo da ispisujemo samo ako postoji bar jedna validna konekcija.
            
            validne_konekcije = []
            
            for l1 in prvi_letovi_sortirani:
                # Za svaki let l1, nadji validne l2
                validni_l2 = []
                for l2 in drugi_letovi_kandidati:
                    if l2['vreme_pol_min'] > l1['vreme_dol_min']:
                        validni_l2.append(l2)
                
                if validni_l2:
                    # Sortiranje l2: vreme polaska, trajanje, aviokompanija
                    validni_l2.sort(key=lambda x: (x['vreme_pol_min'], x['trajanje'], x['aviokompanija']))
                    validne_konekcije.append((l1, validni_l2))
            
            if validne_konekcije:
                f.write(f"{trazeni_polazak}->{medju}->{trazeni_dolazak}\n")
                for l1, lista_l2 in validne_konekcije:
                    cena1 = formatiraj_cenu(l1['cena'])
                    f.write(f"  {l1['aviokompanija']}|{l1['vreme_pol_str']}-{l1['vreme_dol_str']},{cena1}\n")
                    for l2 in lista_l2:
                        cena2 = formatiraj_cenu(l2['cena'])
                        f.write(f"    {l2['aviokompanija']}|{l2['vreme_pol_str']}-{l2['vreme_dol_str']},{cena2}\n")

def main():
    try:
        # 1. Ucitavanje sa standardnog ulaza (par gradova)
        # S obzirom na potencijalni prazan ulaz, citamo odmah.
        # "Ucitava sve potrebne podatke sa standardnog ulaza" - to je samo par gradova za 2. deo.
        ulaz = sys.stdin.readline().strip()
        if not ulaz:
            return
            
        if '->' in ulaz:
            trazeni_gradovi = ulaz.split('->')
            if len(trazeni_gradovi) == 2:
                trazeni_polazak, trazeni_dolazak = trazeni_gradovi[0].strip(), trazeni_gradovi[1].strip()
            else:
                # Tehnicki bi ovo bio format error, ali zadatak kaze da pretpostavimo ispravan ulaz
                # osim ako nije drugacije receno.
                trazeni_polazak, trazeni_dolazak = None, None
        else:
            trazeni_polazak, trazeni_dolazak = None, None

        # 2. Ucitavanje datoteke
        try:
            letovi = ucitaj_letove("flights.txt")
        except FileNotFoundError:
            print("DAT_GRESKA")
            return
        except Exception:
            # Bilo koja druga greska pri parsiranju
            print("GRESKA")
            return
            
        # 3. Obrada direktnih letova
        try:
            obradi_direktne_letove(letovi)
        except Exception:
            print("GRESKA")
            return
            
        # 4. Obrada indirektnih letova
        if trazeni_polazak and trazeni_dolazak:
            try:
                obradi_indirektne_letove(letovi, trazeni_polazak, trazeni_dolazak)
            except Exception:
                print("GRESKA")
                return

    except Exception:
        print("GRESKA")

if __name__ == "__main__":
    main()
