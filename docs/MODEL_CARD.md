# Model Card — Classification de la gravité des accidents

> Fiche de gouvernance du modèle, format inspiré des *Model Cards* (Mitchell et al., 2019).
> Les champs `<!-- À COMPLÉTER -->` doivent être renseignés avec les valeurs réelles avant toute
> présentation / mise en production.

## 1. Détails du modèle

| Champ | Valeur |
| --- | --- |
| Nom | Gravité accident — RandomForestClassifier |
| Version | <!-- À COMPLÉTER : ex. v1 / run_id MLflow --> |
| Date | <!-- À COMPLÉTER --> |
| Propriétaire(s) / contact | <!-- À COMPLÉTER : noms + email équipe --> |
| Type | Classification supervisée binaire |
| Algorithme | `sklearn.ensemble.RandomForestClassifier` |
| Framework | scikit-learn |
| Suivi | MLflow — expérience `random_forest_training` (artefacts sur MinIO `s3://mlflow/`) |
| Code d'entraînement | `backend_sql/scripts/ai_models/RandomForestClassifier.py` |
| Preprocessing | `backend_sql/scripts/general_tain_setup.py` |

**Hyperparamètres** (`default_params`) :

```
n_estimators=200, max_depth=5, min_samples_split=2, min_samples_leaf=10,
max_samples=None, random_state=42, class_weight=<compute_class_weight('balanced')>, n_jobs=-1
```

## 2. Usage prévu

- **Cible.** Prédire `grav` regroupée en binaire par `group_grav_values` :
  **0 = Indemne + Blessé léger**, **1 = Tué + Blessé hospitalisé**.
- **Usage prévu.** Aide à l'estimation / priorisation à partir des caractéristiques d'un accident.
- **Utilisateurs visés.** <!-- À COMPLÉTER : ex. équipe interne, démo pédagogique -->
- **Hors périmètre (interdit).** Toute décision **médicale, assurantielle ou d'orientation des secours**
  automatisée sans supervision humaine. Le modèle ne constitue pas un avis médical.

## 3. Données

- **Source.** Données BAAC (voir [`DATASET_DATASHEET.md`](DATASET_DATASHEET.md)).
- **Découpage.** `train_test_split(test_size=0.2, random_state=42, stratify=y)`.
- **Features utilisées (~36).** `manv, plan, mois, age, n_passager, motor, larrout, an, cos_time,
  n_pieton, catr, surf, lum, sin_time, senc, circ, infra, dep, catv, vosp, situ, agg, day_of_week, obs,
  prof, int_, sexe, obsm, pr, jour, atm, is_holiday, choc, pr1, col, vma_cat`.
- **Version du dataset.** <!-- À COMPLÉTER : digest / hash / date d'extraction -->

## 4. Métriques de performance

> ⚠️ Aujourd'hui, seule l'`accuracy` est loguée dans MLflow. Compléter avec les métriques adaptées au
> **déséquilibre de classes** (les cas graves sont minoritaires).

| Métrique | Valeur (jeu de test) |
| --- | --- |
| Accuracy | <!-- À COMPLÉTER --> |
| F1 (macro) | <!-- À COMPLÉTER --> |
| Recall — classe « grave » (1) | <!-- À COMPLÉTER --> |
| Precision — classe « grave » (1) | <!-- À COMPLÉTER --> |
| ROC-AUC | <!-- À COMPLÉTER --> |
| PR-AUC | <!-- À COMPLÉTER --> |
| Matrice de confusion | <!-- À COMPLÉTER --> |
| Baseline comparée (DummyClassifier) | <!-- À COMPLÉTER --> |

## 5. Analyse par sous-population (fairness)

> Enjeu fort pour un modèle de gravité corporelle. Renseigner le recall / F1 par groupe et documenter les
> seuils d'acceptation.

| Groupe | Métrique | Valeur | Écart acceptable ? |
| --- | --- | --- | --- |
| Sexe (`sexe`) | <!-- À COMPLÉTER --> | | |
| Catégorie d'usager (`catv`/`catu`) | <!-- À COMPLÉTER --> | | |
| Agglomération vs hors-agglo (`agg`) | <!-- À COMPLÉTER --> | | |
| Département / région (`dep`) | <!-- À COMPLÉTER --> | | |

**Seuils d'équité retenus.** <!-- À COMPLÉTER -->

## 6. Limites et modes d'échec connus

- **Déséquilibre de classes** : traité par `class_weight='balanced'`, mais performances à valider sur la
  classe minoritaire (métriques ci-dessus).
- **Risque de train/serve skew** : le service `gravity_classification` n'applique pas de preprocessing et
  les `LabelEncoder` de l'entraînement ne sont pas persistés — un encodage divergent côté client fausse
  la prédiction.
- **Sélection du modèle par accuracy** (pas de Model Registry, chemin MinIO de secours codé en dur).
- **Pas de monitoring de drift** en production : dégradation non détectée si la distribution évolue.
- **Généralisation temporelle** : <!-- À COMPLÉTER : le modèle est-il validé sur une autre année BAAC ? -->

## 7. Considérations éthiques, sécurité et vie privée

- **Éthique.** Sujet sensible (intégrité corporelle) ; l'analyse fairness (§5) est requise avant tout
  usage réel.
- **Vie privée.** Données relatives à des personnes ; identifiants exclus au preprocessing
  (`id`, `id_usager`, `lat/long`, `an_nais`…). Politique de rétention : voir Datasheet.
- **Sécurité.** <!-- À COMPLÉTER : auth API, contrôle d'accès aux prédictions -->

## 8. Maintenance

- **Ré-entraînement.** Déclenché en fin de DAG `import_csv_to_sql` (à la demande).
- **Fréquence prévue.** <!-- À COMPLÉTER -->
- **Quality gate avant promotion.** <!-- À COMPLÉTER : critère F1 > baseline, etc. (non implémenté) -->

---

_Model Card — projet « Gravité des accidents » (dépôt `nov23_alt_iia`). Document interne d'équipe._
