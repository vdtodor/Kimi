import sys
from bisect import bisect_left

# ------------------------------------------------------------
# Funkcija: procitaj_ulaz
# Čita standardni ulaz (par gradova u formatu CITY1->CITY2)
# Ako je ulaz prazan, vraća None (program se tiho završava)
# Ako je format pogrešan, baca grešku
# ------------------------------------------------------------
def procitaj_ulaz():
    s = sys.stdin.read().strip()

    # Ako je ulaz prazan niz znakova – program se korektno završava
    if s == "":
        return None

    # Ulaz mora da sadrži strelicu
    if "->" not in s:
        raise ValueError("Neispravan format ulaza")

    # Razdvajamo polazni i dolazni grad
    dep, lan = [x.strip() for x in s.split("->", 1)]

    # Gradovi ne smeju biti prazni
    if dep == "" or lan == "":
        raise ValueError("Neispravan format ulaza")

    return dep, lan


# ------------------------------------------------------------
# Funkcija: time_to_min
# Pretvara vreme u formatu "hh:mm" u ukupan broj minuta
# Ovo olakšava poređenje vremena
# ------------------------------------------------------------
def time_to_min(t):
    hh, mm = t.split(":")
    return int(hh) * 60 + int(mm)


# ------------------------------------------------------------
# Funkcija: flight_sort_key
# Ključ za sortiranje letova prema zahtevu zadatka:
# 1) vreme polaska
# 2) trajanje leta
# 3) ime aviokompanije
# ------------------------------------------------------------
def flight_sort_key(flight):
    airline, _, _, dep_min, lan_min, _, _, _ = flight
    duration = lan_min - dep_min
    return (dep_min, duration, airline)


# ------------------------------------------------------------
# Funkcija: procitaj_flights_file
# Čita datoteku flights.txt i formira dve strukture podataka:
#
# route_map:
#   (dep, lan) -> { airline -> [letovi...] }
#
# seg_map:
#   (dep, lan) -> [letovi...]
#
# Let je običan tuple (bez klasa!)
# ------------------------------------------------------------
def procitaj_flights_file(path):
    route_map = {}
    seg_map = {}

    # Otvaranje datoteke
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()

            # Preskačemo prazne redove
            if line == "":
                continue

            # Očekujemo tačno tri dela razdvojena znakom |
            parts = line.split("|")
            if len(parts) != 3:
                raise ValueError("Pogrešan format linije")

            airline = parts[0].strip()
            route = parts[1].strip()
            flights_part = parts[2].strip()

            # Provera rute
            if "->" not in route:
                raise ValueError("Pogrešan format rute")

            dep_city, lan_city = [x.strip() for x in route.split("->", 1)]

            if airline == "" or dep_city == "" or lan_city == "":
                raise ValueError("Prazno polje u liniji")

            # Svaki let je razdvojen znakom ;
            tokens = flights_part.split(";")

            for tok in tokens:
                tok = tok.strip()
                if tok == "":
                    continue

                # Format: hh:mm-hh:mm,price
                if "," not in tok:
                    raise ValueError("Pogrešan format leta")

                time_range, price_str = tok.split(",", 1)

                if "-" not in time_range:
                    raise ValueError("Pogrešan format vremena")

                dep_str, lan_str = [x.strip() for x in time_range.split("-", 1)]

                # Pretvaranje vremena u minute
                dep_min = time_to_min(dep_str)
                lan_min = time_to_min(lan_str)

                # Cena mora biti realan broj
                price = float(price_str.strip())

                # Jedan let kao tuple
                flight = (
                    airline,
                    dep_city,
                    lan_city,
                    dep_min,
                    lan_min,
                    dep_str,
                    lan_str,
                    price
                )

                key = (dep_city, lan_city)

                # Popunjavanje route_map
                if key not in route_map:
                    route_map[key] = {}
                if airline not in route_map[key]:
                    route_map[key][airline] = []
                route_map[key][airline].append(flight)

                # Popunjavanje seg_map
                if key not in seg_map:
                    seg_map[key] = []
                seg_map[key].append(flight)

    # Sortiranje letova
    for key in route_map:
        for airline in route_map[key]:
            route_map[key][airline].sort(key=flight_sort_key)

    for key in seg_map:
        seg_map[key].sort(key=flight_sort_key)

    return route_map, seg_map


# ------------------------------------------------------------
# Funkcija: upisi_direct
# Formira datoteku flights_direct.txt
# ------------------------------------------------------------
def upisi_direct(route_map, out_path):
    with open(out_path, "w", encoding="utf-8") as out:
        for dep, lan in sorted(route_map.keys()):
            out.write(f"{dep}->{lan}\n")

            for airline in sorted(route_map[(dep, lan)].keys()):
                flights = route_map[(dep, lan)][airline]

                flights_str = ";".join(
                    f"{f[5]}-{f[6]},{f[7]:.2f}" for f in flights
                )

                out.write(f"{airline}|{flights_str}\n")


# ------------------------------------------------------------
# Funkcija: upisi_indirect
# Formira datoteku flights_indirect.txt
# Sa jednim presedanjem
# ------------------------------------------------------------
def upisi_indirect(seg_map, dep, lan, out_path):
    # Pronalazimo sve gradove preko kojih je moguće presedanje
    dep_to = {to for (fr, to) in seg_map if fr == dep}
    to_lan = {fr for (fr, to) in seg_map if to == lan}
    meds = sorted(dep_to & to_lan)

    with open(out_path, "w", encoding="utf-8") as out:
        for med in meds:
            A = seg_map.get((dep, med), [])
            B = seg_map.get((med, lan), [])

            if not A or not B:
                continue

            out.write(f"{dep}->{med}->{lan}\n")

            # Lista vremena polaska za drugi segment
            b_dep_times = [f[3] for f in B]

            for a in A:
                out.write(
                    f"{dep}->{med}|{a[0]}|{a[5]}-{a[6]},{a[7]:.2f}\n"
                )

                # Tražimo letove koji mogu da se stignu
                idx = bisect_left(b_dep_times, a[4])

                for b in B[idx:]:
                    out.write(
                        f"{med}->{lan}|{b[0]}|{b[5]}-{b[6]},{b[7]:.2f}\n"
                    )


# ------------------------------------------------------------
# Glavna funkcija
# ------------------------------------------------------------
def main():
    try:
        ulaz = procitaj_ulaz()

        # Ako je ulaz prazan – ništa se ne ispisuje
        if ulaz is None:
            return

        dep, lan = ulaz

        try:
            route_map, seg_map = procitaj_flights_file("flights.txt")
        except FileNotFoundError:
            print("DAT_GRESKA")
            return

        upisi_direct(route_map, "flights_direct.txt")
        upisi_indirect(seg_map, dep, lan, "flights_indirect.txt")

    except Exception:
        print("GRESKA")


# Pokretanje programa
if __name__ == "__main__":
    main()
