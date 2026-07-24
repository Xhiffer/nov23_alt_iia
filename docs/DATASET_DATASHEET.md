# Datasheet — Jeu de données BAAC (accidents corporels)

> Fiche descriptive du jeu de données, format inspiré des *Datasheets for Datasets* (Gebru et al., 2018).
> Les champs `<!-- À COMPLÉTER -->` doivent être renseignés avec les valeurs réelles.

## 1. Motivation

- **But.** Entraîner un modèle de classification de la **gravité corporelle** des accidents de la route
  à partir des caractéristiques de l'accident, du lieu, des véhicules et des usagers.
- **Créateur du dataset original.** Base **BAAC** (Bulletin d'Analyse des Accidents Corporels), produite
  par les forces de l'ordre et publiée par l'ONISR / l'État français.
- **Constitué / traité par.** Équipe projet `nov23_alt_iia`.

## 2. Composition

- **Tables sources** (importées en PostgreSQL via le DAG `import_csv_to_sql`) :
  - `caractéristiques` — circonstances de l'accident (date, lumière, agglomération, intersection, météo,
    type de collision…).
  - `lieux` — infrastructure et voirie (catégorie de route, surface, profil, VMA…).
  - `véhicules` — véhicules impliqués (catégorie, manœuvre, choc, motorisation…).
  - `usagers` — personnes impliquées (sexe, âge/année de naissance, catégorie, gravité `grav`…).
- **Variable cible.** `grav` (1 = Indemne, 2 = Tué, 3 = Blessé hospitalisé, 4 = Blessé léger),
  **regroupée en binaire** par `group_grav_values` : 0 = {1, 4}, 1 = {2, 3}.
- **Volumétrie.** <!-- À COMPLÉTER : nombre de lignes par table + table d'entraînement -->
- **Période couverte.** <!-- À COMPLÉTER : années BAAC utilisées -->
- **Granularité.** Une ligne d'entraînement = un usager relié à son accident / véhicule / lieu.

## 3. Colonnes exclues au preprocessing

`general_tain_setup.py` retire notamment :

| Colonne(s) | Raison |
| --- | --- |
| `id`, `id_accident`, `id_usager`, `id_vehicule`, `date_ajout` | Identifiants / métadonnées techniques |
| `lat`, `long` | Géolocalisation précise (bruit + vie privée) |
| `an_nais` | Redondant avec `age` |
| `hrmn_scaled`, `date` | Remplacées par features temporelles (`cos_time`, `sin_time`, `day_of_week`…) |
| `vma` | Retirée pour les modèles non-arbres |
| `locp`, `is_weekend` | Écartées côté RandomForest |

## 4. Collecte et traitement

- **Source d'acquisition.** Fichiers CSV BAAC → import via endpoints `backend_sql` (`/*/csv-to-sql/`).
- **Nettoyage / features.** Imputation (médiane pour numériques, mode pour catégorielles), encodage
  `LabelEncoder`, features temporelles, regroupement de la cible. Voir `RandomForestClassifier.py`.
- **Validation.** Contrôle de schéma **non bloquant** (colonnes attendues logguées en warning) —
  à durcir. <!-- À COMPLÉTER : ajout de tests bloquants -->

## 5. Vie privée et conformité

- **Données personnelles.** Le dataset décrit des **personnes physiques** (usagers) : âge, sexe, gravité
  des blessures. Aucune donnée directement identifiante n'est conservée pour l'entraînement (ids et
  géolocalisation exclus).
- **Base légale / licence.** <!-- À COMPLÉTER : ex. Licence Ouverte Etalab — à confirmer -->
- **Politique de rétention.** <!-- À COMPLÉTER : durée de conservation, purge -->
- **Accès.** <!-- À COMPLÉTER : qui accède aux données, pourquoi -->

## 6. Distribution et maintenance

- **Disponibilité.** <!-- À COMPLÉTER : lien source data.gouv.fr / ONISR -->
- **Versioning.** ⚠️ Pas de versioning de données à ce jour (pas de DVC / digest). À mettre en place pour
  la lineage données → modèle.
- **Responsable de la maintenance.** <!-- À COMPLÉTER -->
- **Fréquence de mise à jour.** <!-- À COMPLÉTER -->

## 7. Biais et limites connus

- Déséquilibre de la cible (cas graves minoritaires).
- Qualité de saisie hétérogène selon les services verbalisateurs (biais possibles selon zone / année).
- <!-- À COMPLÉTER : autres biais identifiés lors de l'exploration -->

---

_Datasheet — projet « Gravité des accidents » (dépôt `nov23_alt_iia`). Document interne d'équipe._
