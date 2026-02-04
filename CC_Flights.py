def ucitaj_letove(naziv_datoteke):
    """Učitava letove iz datoteke i vraća strukturu podataka sa letovima."""
    letovi = []
    
    with open(naziv_datoteke, 'r', encoding='utf-8') as f:
        for linija in f:
            linija = linija.strip()
            if not linija:
                continue
            
            # Provera formata tekst|tekst->tekst
            if '|' not in linija:
                raise ValueError("Neispravan format")
            
            delovi = linija.split('|')
            if len(delovi) < 3:
                raise ValueError("Neispravan format")
            
            aviokompanija = delovi[0]
            ruta = delovi[1]
            
            if '->' not in ruta:
                raise ValueError("Neispravan format")
            
            gradovi = ruta.split('->')
            if len(gradovi) != 2:
                raise ValueError("Neispravan format")
            
            grad_polaska = gradovi[0]
            grad_dolaska = gradovi[1]
            
            # Parsiranje letova
            letovi_str = delovi[2]
            letovi_na_liniji = []
            
            for let_str in letovi_str.split(';'):
                let_str = let_str.strip()
                if not let_str:
                    continue
                
                # Format: hhDep:minDep-hhLan:minLan,price
                delovi_leta = let_str.split(',')
                if len(delovi_leta) != 2:
                    raise ValueError("Neispravan format")
                
                cena = float(delovi_leta[1])
                vremena = delovi_leta[0].split('-')
                
                if len(vremena) != 2:
                    raise ValueError("Neispravan format")
                
                vreme_polaska = vremena[0]
                vreme_dolaska = vremena[1]
                
                letovi_na_liniji.append({
                    'vreme_polaska': vreme_polaska,
                    'vreme_dolaska': vreme_dolaska,
                    'cena': cena
                })
            
            letovi.append({
                'aviokompanija': aviokompanija,
                'grad_polaska': grad_polaska,
                'grad_dolaska': grad_dolaska,
                'letovi': letovi_na_liniji
            })
    
    return letovi


def formiraj_direktne_letove(letovi, naziv_datoteke):
    """Formira datoteku sa direktnim letovima."""
    # Grupisanje po parovima gradova
    parovi = {}
    
    for linija in letovi:
        kljuc = f"{linija['grad_polaska']}->{linija['grad_dolaska']}"
        
        if kljuc not in parovi:
            parovi[kljuc] = []
        
        parovi[kljuc].append({
            'aviokompanija': linija['aviokompanija'],
            'letovi': linija['letovi']
        })
    
    # Sortiranje parova leksikografski
    sortirani_parovi = sorted(parovi.keys())
    
    with open(naziv_datoteke, 'w', encoding='utf-8') as f:
        for par in sortirani_parovi:
            f.write(f"{par}\n")
            
            # Sortiranje aviokompanija leksikografski
            sortirane_kompanije = sorted(parovi[par], key=lambda x: x['aviokompanija'])
            
            for kompanija in sortirane_kompanije:
                # Sortiranje letova hronološki
                sortirani_letovi = sorted(kompanija['letovi'], key=lambda x: x['vreme_polaska'])
                
                for let in sortirani_letovi:
                    f.write(f"{kompanija['aviokompanija']}|{let['vreme_polaska']}-{let['vreme_dolaska']},{let['cena']:.2f}\n")


def vreme_u_minute(vreme_str):
    """Konvertuje vreme iz formata hh:mm u minute."""
    delovi = vreme_str.split(':')
    return int(delovi[0]) * 60 + int(delovi[1])


def trajanje_leta(vreme_polaska, vreme_dolaska):
    """Računa trajanje leta u minutima."""
    return vreme_u_minute(vreme_dolaska) - vreme_u_minute(vreme_polaska)


def formiraj_indirektne_letove(letovi, par_gradova, naziv_datoteke):
    """Formira datoteku sa letovima sa jednim presedalim."""
    delovi = par_gradova.split('->')
    if len(delovi) != 2:
        raise ValueError("Neispravan format para gradova")
    
    polazni_grad = delovi[0]
    odredisni_grad = delovi[1]
    
    # Pronalaženje svih letova
    letovi_iz = {}  # grad_polaska -> grad_dolaska -> lista letova
    
    for linija in letovi:
        grad_p = linija['grad_polaska']
        grad_d = linija['grad_dolaska']
        
        if grad_p not in letovi_iz:
            letovi_iz[grad_p] = {}
        
        if grad_d not in letovi_iz[grad_p]:
            letovi_iz[grad_p][grad_d] = []
        
        for let in linija['letovi']:
            letovi_iz[grad_p][grad_d].append({
                'aviokompanija': linija['aviokompanija'],
                'vreme_polaska': let['vreme_polaska'],
                'vreme_dolaska': let['vreme_dolaska'],
                'cena': let['cena']
            })
    
    # Pronalaženje svih presedanja
    presedanja = {}
    
    if polazni_grad in letovi_iz:
        for medjugrad in letovi_iz[polazni_grad]:
            if medjugrad != odredisni_grad and medjugrad in letovi_iz:
                if odredisni_grad in letovi_iz[medjugrad]:
                    presedanja[medjugrad] = []
                    
                    # Kombinacije letova
                    for let1 in letovi_iz[polazni_grad][medjugrad]:
                        for let2 in letovi_iz[medjugrad][odredisni_grad]:
                            # Provera da li je vreme presedanja moguće
                            if vreme_u_minute(let2['vreme_polaska']) > vreme_u_minute(let1['vreme_dolaska']):
                                presedanja[medjugrad].append((let1, let2))
    
    # Sortiranje gradova presedanja leksikografski
    sortirani_gradovi = sorted(presedanja.keys())
    
    with open(naziv_datoteke, 'w', encoding='utf-8') as f:
        for medjugrad in sortirani_gradovi:
            f.write(f"{polazni_grad}->{medjugrad}->{odredisni_grad}\n")
            
            # Sortiranje kombinacija
            kombinacije = presedanja[medjugrad]
            kombinacije_sortirane = sorted(kombinacije, key=lambda x: (
                x[0]['vreme_polaska'],
                trajanje_leta(x[0]['vreme_polaska'], x[0]['vreme_dolaska']),
                x[0]['aviokompanija']
            ))
            
            for let1, let2 in kombinacije_sortirane:
                f.write(f"{polazni_grad}->{medjugrad}\n")
                f.write(f"{let1['aviokompanija']}|{let1['vreme_polaska']}-{let1['vreme_dolaska']},{let1['cena']:.2f}\n")
                
                # Sortiranje drugog dela
                f.write(f"{medjugrad}->{odredisni_grad}\n")
                f.write(f"{let2['aviokompanija']}|{let2['vreme_polaska']}-{let2['vreme_dolaska']},{let2['cena']:.2f}\n")


def main():
    try:
        # Učitavanje para gradova sa standardnog ulaza
        par_gradova = input().strip()
        
        if not par_gradova:
            return
        
        # Učitavanje letova iz datoteke
        letovi = ucitaj_letove('flights.txt')
        
        # Formiranje datoteke sa direktnim letovima
        formiraj_direktne_letove(letovi, 'flights_direct.txt')
        
        # Formiranje datoteke sa indirektnim letovima
        formiraj_indirektne_letove(letovi, par_gradova, 'flights_indirect.txt')
        
    except FileNotFoundError:
        print("DAT_GRESKA")
    except Exception:
        print("GRESKA")


if __name__ == "__main__":
    main()
