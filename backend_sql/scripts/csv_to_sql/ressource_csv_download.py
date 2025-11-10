import requests
import csv
from typing import Dict, List


class GouvDataFetcher:
    DATASET_SLUG = (
        "bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-"
        "routiere-annees-de-2005-a-2024"
    )
    BASE_URL = "https://www.data.gouv.fr/api/1/datasets/"

    # known filename patterns per logical type
    # everything is case-insensitive; {year} will be formatted
    FILENAME_PATTERNS: Dict[str, List[str]] = {
        "caract": [
            "caract-{year}.csv",
            "caract_{year}.csv",
            "caracteristiques-{year}.csv",
            "caracteristiques_{year}.csv",
        ],
        "lieux": [
            "lieux-{year}.csv",
            "lieux_{year}.csv",
        ],
        "usagers": [
            "usagers-{year}.csv",
            "usagers_{year}.csv",
        ],
        "vehicules": [
            "vehicules-{year}.csv",
            "vehicules_{year}.csv",
        ],
    }

    def __init__(self, year: int):
        self.year = year
        self.dataset_url = f"{self.BASE_URL}{self.DATASET_SLUG}/"
        self.resources: List[dict] = []
        # result: [{"type": "caract", "name": "...", "rows": [...]}, ...]
        self.data: List[dict] = []

    # ---------- low-level helpers ---------- #

    def _get_resources(self) -> List[dict]:
        resp = requests.get(self.dataset_url)
        resp.raise_for_status()
        return resp.json().get("resources", [])

    @staticmethod
    def _fetch_csv(csv_url: str) -> List[dict]:
        resp = requests.get(csv_url, stream=True)
        resp.raise_for_status()
        lines = (line.decode("utf-8") for line in resp.iter_lines())
        reader = csv.DictReader(lines, delimiter=";")
        return list(reader)

    # ---------- matching logic ---------- #

    def _expected_names_for_year(self) -> Dict[str, set[str]]:
        """
        Build the concrete filenames we expect for this year, lowercased.
        Example for 2023, 'vehicules' ->
            {'vehicules-2023.csv', 'vehicules_2023.csv'}
        """
        year = self.year
        expected: Dict[str, set[str]] = {}
        for kind, patterns in self.FILENAME_PATTERNS.items():
            expected[kind] = {p.format(year=year).lower() for p in patterns}
            
        return expected

    def _match_targets_for_year(self, resources: List[dict]) -> Dict[str, dict]:
        """
        Return a map: {"caract": resource_dict, "lieux": ..., ...}
        based on exact (case-insensitive) filename matches against known patterns.
        """
        expected = self._expected_names_for_year()
        result: Dict[str, dict] = {}

        for r in resources:
            fmt = (r.get("format") or "").lower()
            if fmt != "csv":
                continue  # ignore non-CSV resources

            title = (r.get("title") or "").lower()
            url = (r.get("url") or "").lower()
            filename = url.rsplit("/", 1)[-1]

            for kind, names in expected.items():
                # exact match on filename or on title-as-filename
                if filename in names or title in names:
                    # extra guard to avoid 'vehicules-immatricule-baac-YYYY.csv'
                    if kind == "vehicules" and "immatricule" in filename:
                        continue
                    result[kind] = r

        # optional: warn if some expected types are missing
        missing = [k for k in expected.keys() if k not in result]
        if missing:
            print(f"WARNING year {self.year}: missing CSV types:", missing)

        return result

    # ---------- public API ---------- #

    def fetch_all(self) -> List[dict]:
        """
        Download all 4 accident CSVs for this year and return:
        [
          {"type": "caract", "name": ..., "rows": [...]},
          {"type": "lieux", ...},
          {"type": "usagers", ...},
          {"type": "vehicules", ...},
        ]
        """
        self.resources = self._get_resources()
        target_map = self._match_targets_for_year(self.resources)

        self.data = []
        for kind in ["caract", "lieux", "usagers", "vehicules"]:
            res = target_map.get(kind)
            if not res:
                continue

            name = res.get("title") or res.get("url") or f"{kind}-{self.year}"
            csv_url = res["url"]

            print(f"Downloading {name} (type={kind}) ...")
            rows = self._fetch_csv(csv_url)
            print(f"{name}: {len(rows)} rows downloaded")

            self.data.append({"type": kind, "name": name, "rows": rows})

        return self.data
