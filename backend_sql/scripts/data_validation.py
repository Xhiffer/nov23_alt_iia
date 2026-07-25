"""
Validation de données **bloquante** pour l'entraînement (Pandera).

`validate_training_data(df)` lève une exception si le jeu de features ne respecte
pas le contrat (colonnes manquantes, cible hors {0,1}, mois/jour hors plage...),
afin de **stopper** le pipeline avant l'entraînement plutôt que d'entraîner sur
des données corrompues.
"""
import pandera as pa

# Features attendues en entrée d'entraînement (hors cible `grav`).
REQUIRED_FEATURES = [
    "manv", "plan", "mois", "age", "n_passager", "motor", "larrout", "an",
    "cos_time", "n_pieton", "catr", "surf", "lum", "sin_time", "senc", "circ",
    "infra", "dep", "catv", "vosp", "situ", "agg", "day_of_week", "obs",
    "prof", "int_", "sexe", "obsm", "pr", "jour", "atm", "is_holiday",
    "choc", "pr1", "col", "vma_cat",
]


def build_training_schema() -> pa.DataFrameSchema:
    """Schéma conservateur : présence des features + contraintes sûres sur la cible
    et quelques colonnes clés (ne casse pas sur des données BAAC valides)."""
    columns = {
        # Cible binaire (après group_grav_values) : 0 = indemne/léger, 1 = tué/hospitalisé
        "grav": pa.Column(int, pa.Check.isin([0, 1]), nullable=False, coerce=True),
        "mois": pa.Column(int, pa.Check.in_range(1, 12), nullable=False, coerce=True),
        "jour": pa.Column(int, pa.Check.in_range(1, 31), nullable=False, coerce=True),
    }
    # Présence obligatoire des autres features (type/null non contraints ici).
    for col in REQUIRED_FEATURES:
        columns.setdefault(col, pa.Column(nullable=True, required=True))
    return pa.DataFrameSchema(columns, strict=False)


def validate_training_data(df):
    """Valide le DataFrame d'entraînement. Lève `pandera.errors.SchemaErrors`
    (mode lazy : toutes les violations agrégées) en cas de non-conformité.
    Retourne le DataFrame validé si tout est conforme."""
    schema = build_training_schema()
    return schema.validate(df, lazy=True)
