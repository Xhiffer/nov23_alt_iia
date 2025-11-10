from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
import json
import math
import re


@dataclass
class Usagers:
    Num_Acc: str | None
    id_usager: str | None
    id_vehicule: str | None
    num_veh: str | None
    place: int | None
    catu: int | None
    grav: int | None
    sexe: int | None
    an_nais: int | None
    trajet: int | None
    secu1: int | None
    secu2: int | None
    secu3: int | None
    locp: int | None
    actp: str | None
    etatp: int | None


@dataclass
class Vehicules:
    Num_Acc: str | None
    id_vehicule: str | None
    num_veh: str | None
    senc: int | None
    catv: int | None
    obs: int | None
    obsm: int | None
    choc: int | None
    manv: int | None
    motor: int | None
    occutc: str | None


@dataclass
class Lieux:
    Num_Acc: str | None
    catr: int | None
    voie: str | None
    v1: str | None
    v2: str | None
    circ: int | None
    nbv: int | None
    vosp: int | None
    prof: int | None
    pr: str | None
    pr1: str | None
    plan: int | None
    lartpc: str | None
    larrout: str | None
    surf: int | None
    infra: int | None
    situ: int | None
    vma: int | None


@dataclass
class Caracteristique:
    Num_Acc: str | None
    jour: int | None
    mois: int | None
    an: int | None
    hrmn: str | None
    lum: int | None
    dep: str | None
    com: str | None
    agg: int | None
    inter: int | None
    atm: int | None
    col: int | None
    adr: str | None
    lat: float | None
    long: float | None





class DataHandler:

    def __init__(self, data: List[Dict[str, Any]]):
        """
        data is expected to be the list coming from GouvDataFetcher.fetch_all():
        [
            {"name": "caract-2023.csv", "rows": [...]},
            {"name": "lieux-2023.csv", "rows": [...]},
            ...
        ]
        """
        self.raw_data: List[Dict[str, Any]] = data
        self.usagers_data: List[Usagers] = []
        self.vehicules_data: List[Vehicules] = []
        self.lieux_data: List[Lieux] = []
        self.caracteristiques_data: List[Caracteristique] = []

    def _nan_to_none(self, value: Any) -> Any:
        if isinstance(value, float) and math.isnan(value):
            return None
        return value


    def _extract_year_from_filename(self, file_name: str) -> int | None:
        m = re.search(r"(\d{4})", file_name)
        return int(m.group(1)) if m else None
    
    # ---------- DB insert methods ---------- #

    def save_raw_rows(self, conn) -> None:
        """
        Insert raw rows into table raw_rows(file_name, year, Num_Acc, row_json).
        """
        sql = """
            INSERT INTO raw_rows (file_name, year, Num_Acc, row_json)
            VALUES (%s, %s, %s, %s)
        """
        cur = conn.cursor()

        for file_block in self.raw_data:
            file_name = file_block["name"]
            year = self._extract_year_from_filename(file_name)
            for row in file_block["rows"]:
                num_acc = row.get("Num_Acc")
                cur.execute(sql, (file_name, year, num_acc, json.dumps(row)))

        conn.commit()
        cur.close()

    def save_caracteristiques(self, conn) -> None:
        """
        Insert Caracteristique objects into caracteristiques table.
        """
        sql = """
            INSERT INTO caracteristiques (
                Num_Acc, jour, mois, an, hrmn, lum,
                dep, com, agg, `inter`, atm, col, adr, lat, `long`
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        cur = conn.cursor()

        for c in self.caracteristiques_data:
            cur.execute(
                sql,
                (
                    c.Num_Acc,
                    c.jour,
                    c.mois,
                    c.an,
                    c.hrmn,
                    c.lum,
                    c.dep,
                    c.com,
                    c.agg,
                    c.inter,
                    c.atm,
                    c.col,
                    c.adr,
                    self._nan_to_none(c.lat),
                    self._nan_to_none(c.long),
                ),
            )

        conn.commit()
        cur.close()

    def save_lieux(self, conn) -> None:
        """
        Insert Lieux objects into lieux table.
        """
        sql = """
            INSERT INTO lieux (
                Num_Acc, catr, voie, v1, v2, circ, nbv, vosp,
                prof, pr, pr1, plan, lartpc, larrout, surf, infra, situ, vma
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        cur = conn.cursor()

        for l in self.lieux_data:
            cur.execute(
                sql,
                (
                    l.Num_Acc,
                    l.catr,
                    l.voie,
                    l.v1,
                    l.v2,
                    l.circ,
                    l.nbv,
                    l.vosp,
                    l.prof,
                    l.pr,
                    l.pr1,
                    l.plan,
                    l.lartpc,
                    l.larrout,
                    l.surf,
                    l.infra,
                    l.situ,
                    l.vma,
                ),
            )

        conn.commit()
        cur.close()

    def save_vehicules(self, conn) -> None:
        """
        Insert Vehicules objects into vehicules table.
        """
        sql = """
            INSERT INTO vehicules (
                Num_Acc, id_vehicule, num_veh,
                senc, catv, obs, obsm, choc, manv, motor, occutc
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        cur = conn.cursor()

        for v in self.vehicules_data:
            cur.execute(
                sql,
                (
                    v.Num_Acc,
                    v.id_vehicule,
                    v.num_veh,
                    v.senc,
                    v.catv,
                    v.obs,
                    v.obsm,
                    v.choc,
                    v.manv,
                    v.motor,
                    v.occutc,
                ),
            )

        conn.commit()
        cur.close()

    def save_usagers(self, conn) -> None:
        """
        Insert Usagers objects into usagers table.
        """
        sql = """
            INSERT INTO usagers (
                Num_Acc, id_usager, id_vehicule, num_veh,
                place, catu, grav, sexe, an_nais, trajet,
                secu1, secu2, secu3, locp, actp, etatp
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """
        cur = conn.cursor()

        for u in self.usagers_data:
            cur.execute(
                sql,
                (
                    u.Num_Acc,
                    u.id_usager,
                    u.id_vehicule,
                    u.num_veh,
                    u.place,
                    u.catu,
                    u.grav,
                    u.sexe,
                    u.an_nais,
                    u.trajet,
                    u.secu1,
                    u.secu2,
                    u.secu3,
                    u.locp,
                    u.actp,
                    u.etatp,
                ),
            )

        conn.commit()
        cur.close()

    def save_all(self, conn) -> None:
        """
        Convenience wrapper:
        - save raw rows
        - then caracteristiques
        - then lieux, vehicules, usagers
        Order matters because of foreign keys.
        """
        self.save_raw_rows(conn)
        self.save_caracteristiques(conn)
        self.save_lieux(conn)
        self.save_vehicules(conn)
        self.save_usagers(conn)
        
