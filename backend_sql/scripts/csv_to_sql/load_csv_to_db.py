from math import nan
import datetime
from ressource_csv_download import GouvDataFetcher
import mysql.connector
from data_handler import (
    DataHandler,
    Usagers,
    Vehicules,
    Lieux,
    Caracteristique,
)


# ----- small helpers for safe conversion ----- #

NULL_MARKERS = {"", "N/A", "#VALEURMULTI"}

def to_int(value: str | None, field: str, default: int | None = None) -> int | None:
    if value is None:
        return None

    v = str(value).strip()
    if v in NULL_MARKERS:
        # treat as missing
        return None

    try:
        return int(v)
    except ValueError:
        # this really is unexpected garbage now
        print(f"Warning: field {field}: cannot convert {value!r} to int, using default {default}")
        return default




def to_float_fr(value: str | None) -> float:
    """
    Convert French-style float string '48,86638600' -> 48.866386.
    Returns NaN for empty / invalid.
    """
    if value is None:
        return nan

    v = str(value).strip()
    if v in ("", "N/A"):
        return nan

    try:
        return float(v.replace(",", "."))
    except ValueError:
        print(f"Warning: cannot convert {value!r} to float, using NaN")
        return nan


# ----- main builder ----- #

def build_data_handler(year: int = 2023) -> DataHandler:
    # 1. fetch raw CSVs
    fetcher = GouvDataFetcher(year=year)
    all_files = fetcher.fetch_all()  # list[{"name": str, "rows": list[dict]}]

    # 2. create handler, store raw files structure if you want
    handler = DataHandler(all_files)

    # 3. dispatch each file into the right dataclass list
    for file in all_files:
        name: str = file["name"]
        rows: list[dict] = file["rows"]

        lower_name = name.lower()

        # ---- USAGERS ---- #
        if "usagers" in lower_name:
            for r in rows:
                handler.usagers_data.append(
                    Usagers(
                        Num_Acc=r.get("Num_Acc"),
                        id_usager=r.get("id_usager"),
                        id_vehicule=r.get("id_vehicule"),
                        num_veh=r.get("num_veh"),
                        place=to_int(r.get("place"), "place"),
                        catu=to_int(r.get("catu"), "catu"),
                        grav=to_int(r.get("grav"), "grav"),
                        sexe=to_int(r.get("sexe"), "sexe"),
                        an_nais=to_int(r.get("an_nais"), "an_nais"),
                        trajet=to_int(r.get("trajet"), "trajet"),
                        secu1=to_int(r.get("secu1"), "secu1"),
                        secu2=to_int(r.get("secu2"), "secu2"),
                        secu3=to_int(r.get("secu3"), "secu3"),
                        locp=to_int(r.get("locp"), "locp"),
                        actp=r.get("actp"),
                        etatp=to_int(r.get("etatp"), "etatp"),
                    )
                )

        # ---- VEHICULES ---- #
        elif "vehicules" in lower_name:
            for r in rows:
                handler.vehicules_data.append(
                    Vehicules(
                        Num_Acc=r.get("Num_Acc"),
                        id_vehicule=r.get("id_vehicule"),
                        num_veh=r.get("num_veh"),
                        senc=to_int(r.get("senc"), "senc"),
                        catv=to_int(r.get("catv"), "catv"),
                        obs=to_int(r.get("obs"), "obs"),
                        obsm=to_int(r.get("obsm"), "obsm"),
                        choc=to_int(r.get("choc"), "choc"),
                        manv=to_int(r.get("manv"), "manv"),
                        motor=to_int(r.get("motor"), "motor"),
                        occutc=r.get("occutc") or None,
                    )
                )


        # ---- LIEUX ---- #
        elif "lieux" in lower_name:
            for r in rows:
                handler.lieux_data.append(
                    Lieux(
                        Num_Acc=r.get("Num_Acc"),
                        catr=to_int(r.get("catr"), "catr"),
                        voie=r.get("voie") or None,
                        v1=r.get("v1") or None,
                        v2=r.get("v2") or None,
                        circ=to_int(r.get("circ"), "circ"),
                        nbv=to_int(r.get("nbv"), "nbv"),
                        vosp=to_int(r.get("vosp"), "vosp"),
                        prof=to_int(r.get("prof"), "prof"),
                        pr=r.get("pr") or None,
                        pr1=r.get("pr1") or None,
                        plan=to_int(r.get("plan"), "plan"),
                        lartpc=r.get("lartpc") or None,
                        larrout=r.get("larrout") or None,
                        surf=to_int(r.get("surf"), "surf"),
                        infra=to_int(r.get("infra"), "infra"),
                        situ=to_int(r.get("situ"), "situ"),
                        vma=to_int(r.get("vma"), "vma"),
                    )
                )


        # ---- CARACTERISTIQUES ---- #
        elif "caract" in lower_name:
            for r in rows:
                handler.caracteristiques_data.append(
                Caracteristique(
                    Num_Acc=r.get("Num_Acc"),
                    jour=to_int(r.get("jour"), "jour"),
                    mois=to_int(r.get("mois"), "mois"),
                    an=to_int(r.get("an"), "an"),
                    hrmn=r.get("hrmn"),
                    lum=to_int(r.get("lum"), "lum"),
                    dep=r.get("dep"),
                    com=r.get("com"),
                    agg=to_int(r.get("agg"), "agg"),
                    inter=to_int(r.get("int"), "int"),
                    atm=to_int(r.get("atm"), "atm"),
                    col=to_int(r.get("col"), "col"),
                    adr=r.get("adr"),
                    lat=to_float_fr(r.get("lat")),
                    long=to_float_fr(r.get("long")),
                )
            )



    return handler


def get_existing_years(conn) -> set[int]:
    """Return the set of years already present in raw_rows.year."""
    cur = conn.cursor()
    try:
        cur.execute("SELECT DISTINCT year FROM raw_rows;")
        years = {row[0] for row in cur.fetchall() if row[0] is not None}
    except mysql.connector.errors.ProgrammingError:
        # raw_rows table doesn’t exist yet → no years loaded
        years = set()
    finally:
        cur.close()
    return years

    
if __name__ == "__main__":
    latest_year = datetime.date.today().year
    target_years = [latest_year - i for i in range(5)]

    conn = mysql.connector.connect(
        host="postgresql",
        user="db",
        password="db",
        database="db",
        port=5432,
    )

    existing_years = get_existing_years(conn)
    missing_years = [y for y in target_years if y not in existing_years]

    print("Existing years in DB:", sorted(existing_years))
    print("Target years        :", sorted(target_years))
    print("Missing years       :", sorted(missing_years))

    for year in sorted(missing_years):
        print(f"\n=== Loading year {year} ===")
        handler = build_data_handler(year=year)

        print("Usagers:", len(handler.usagers_data))
        print("Vehicules:", len(handler.vehicules_data))
        print("Lieux:", len(handler.lieux_data))
        print("Caract:", len(handler.caracteristiques_data))
        handler.save_all(conn)
        print(f"Year {year} data saved to DB.")

    conn.close()