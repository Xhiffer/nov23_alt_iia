# Rendu MLOps — Industrialisation du projet « Gravité des accidents »

> Livrable au format DataScientest (question / réponse). Il décrit la démarche **MLOps** mise en place
> autour du modèle de **classification de la gravité corporelle des accidents** (données BAAC :
> usagers / véhicules / lieux / caractéristiques), et évalue honnêtement son niveau de maturité.
>
> Stack réelle : **Airflow (Celery + Redis)**, **MLflow + MinIO (S3) + PostgreSQL (backend store)**,
> **FastAPI `backend_sql` + microservices modèles + `api_gateway`**, **Docker Compose**.

---

## Périmètre et classification du problème

- **À quel niveau de maturité MLOps votre projet se situe-t-il ?**

Nous nous situons entre le **niveau 0 et le niveau 1** de la grille Google (pipeline ML partiellement
automatisé). Concrètement :

- ✅ Nous avons dépassé le stade « notebook + modèle pickle » : le cycle **ingestion → filtrage →
  entraînement** est orchestré par Airflow et suivi dans MLflow.
- ⚠️ Il nous manque encore la **CI/CD**, le **Model Registry** formel, le **monitoring en production** et
  le **ré-entraînement continu (CT)** pour prétendre au niveau 2.

- **Quelle est la tâche ML industrialisée ?**

Une **classification supervisée binaire** : la cible `grav` (4 modalités BAAC) est regroupée en 2 classes
via `group_grav_values` — **0 = Indemne + Blessé léger**, **1 = Tué + Blessé hospitalisé**. Le modèle
retenu pour la chaîne automatisée est un **RandomForestClassifier** (`class_weight='balanced'` pour gérer
le déséquilibre).

---

## 1. Architecture et orchestration

- **Comment le pipeline est-il orchestré ?**

Par **Airflow** (`CeleryExecutor` + Redis + Postgres dédié). Le DAG `import_csv_to_sql`
(`csv_bdd_dag.py`) enchaîne, via des `SimpleHttpOperator` qui appellent le backend FastAPI :

```
import_caracts → import_lieux → import_usagers → import_vehicules
   → import_ai_training_data (/ai-training-data/filter-data/)
   → import_ai_training_data_RandomForestClassifier (/ai-models/train/RandomForestClassifier/)
```

- **Limites :** les DAGs `train_model_dag.py` et `etl_data_dag.py` sont **vides** (des ébauches non
  utilisées) ; l'orchestration réelle passe donc par `csv_bdd_dag`. Le déclenchement est manuel
  (`schedule_interval=None`). L'ordonnancement inter-tâches côté scripts s'appuie aussi sur un mécanisme
  de **lock files** (`check_lock_file`), redondant avec les dépendances natives d'Airflow.

- **Quelle est l'architecture de service ?**

Micro-services Dockerisés sur un réseau `dbnet` : `backend_sql` (API principale + CRUD + déclenchement
training), micro-services modèles (`gravity_classification`, `accident_detection`,
`accident_data_labelisation`), `api_gateway` en frontal, `frontend`, plus `mlflow`, `minio`, `db`,
PgAdmin. **Preuve à fournir :** un schéma `evidence/01_architecture.png`.

---

## 2. Reproductibilité et environnement

- **Le projet est-il reproductible ?**

Partiellement. ✅ Tout est **containerisé** (`docker-compose.yml`, un `Dockerfile` par service,
`Dockerfile.mlflow`). Le lancement est documenté en bas du compose :

```bash
docker compose up airflow-init
docker compose up
```

- ✅ Les **seeds** sont fixées là où ça compte (`train_test_split(random_state=42)`,
  `RandomForestClassifier(random_state=42)`).
- ⚠️ **Limites :** pas de `README` à la racine ; images non taguées (`build` local, pas de
  `model-api:1.x.y`) ; dépendances dans des `requirements.txt` par service dont les versions ne sont pas
  toutes épinglées ; pas de `Makefile` « one-command reproduce ».
- ✅ Bon point : `.gitignore` exclut bien `.env`, `*.log`, `backend_sql/postgres-data/` et
  `airflow/logs/` — les secrets et la base ne sont pas censés être versionnés.

---

## 3. Versioning des données

- **Comment versionnez-vous les données ?**

Aujourd'hui, **pas d'outil de data versioning** (pas de DVC ni lakeFS). Les CSV BAAC sont importés en
base PostgreSQL, puis une table `ai_training_data` est construite par l'endpoint `filter-data`.

- ⚠️ **Limite majeure :** on ne peut pas, à ce jour, associer un modèle à un **hash de dataset** précis.
  La table d'entraînement est régénérée à la demande.
- **Piste :** logguer le **digest MLflow du dataset** (`mlflow.data`) à chaque run, ou versionner la
  table filtrée avec DVC, pour établir la lineage données → modèle.

---

## 4. Validation automatique des données

- **Validez-vous les données avant l'entraînement ?**

Il existe une **validation de schéma légère** dans le script d'entraînement : une liste
`expected_columns` (37 colonnes) est comparée au DataFrame, et les colonnes manquantes / en trop sont
**logguées en `warning`**. Les valeurs uniques de chaque colonne sont aussi tracées pour audit.

- ⚠️ **Limite :** cette validation **n'interrompt pas** le pipeline (warning seulement, pas d'échec) et
  ne couvre pas les types, plages, taux de nuls, doublons, ni le train/serve skew.
- **Piste :** intégrer **Great Expectations / Pandera** en amont du training et faire **échouer** le DAG
  sur violation de contrat (preuve forte : `evidence/…` d'un run bloqué volontairement).

---

## 5. Feature engineering reproductible

- **Le preprocessing est-il reproductible et partagé entre train et inférence ?**

✅ Les transformations sont **centralisées et déterministes** dans `scripts/general_tain_setup.py`
(`remove_excluded_columns`, `remove_lat_long_columns`, `remove_vma_column`, `remove_an_nais_column`,
`delete_hrmn_scaled_column`, `delete_date_column`, `group_grav_values`). L'imputation (médiane /
mode) et l'encodage (`LabelEncoder`) sont faits dans `prepare_data`.

- ⚠️ **Risque de train/serve skew identifié :** le service `gravity_classification` **n'applique aucun
  preprocessing** à l'inférence (commentaire : *« No extra preprocessing here… the model was trained
  directly on these 36 features »*). Il attend des features déjà numériques. Or les `LabelEncoder`
  ajustés à l'entraînement **ne sont pas sauvegardés ni réutilisés** : si le client envoie des libellés
  bruts, l'encodage divergera.
- ⚠️ Le `StandardScaler` est **commenté** dans le RandomForest (acceptable pour un modèle à arbres, mais
  incohérent avec le `scaler.pkl` présent dans d'anciens runs LogisticRegression).
- **Piste :** encapsuler preprocessing + modèle dans un **`sklearn.Pipeline`** loggué comme un seul
  artefact MLflow → garantit la même transformation des deux côtés.

---

## 6. Experiment tracking (MLflow)

- **Comment suivez-vous vos expériences ?**

✅ **MLflow** est pleinement en place : `tracking_uri=http://mlflow:5000`, **backend store PostgreSQL**,
**artifact store MinIO/S3** (`s3://mlflow/`). Le training logue l'expérience `random_forest_training`
avec `mlflow.start_run`, les **hyperparamètres** (`n_estimators`, `max_depth`, `class_weight`,
`random_state`…), la métrique **accuracy**, et le **modèle** (`mlflow.sklearn.log_model`).

- ⚠️ **Limites :** seule l'`accuracy` est envoyée à MLflow ; le `classification_report` et la matrice de
  confusion ne partent que dans les logs fichier. Peu de runs comparables, et les autres algorithmes
  disponibles (`XGBoost`, `CatBoost`, `LightGBM`, `LogisticRegression`, `DecisionTree`,
  `GradientBoosting`) ne sont pas systématiquement benchmarkés dans une même expérience.

---

## 7. Évaluation ML

- **Vos métriques sont-elles adaptées au problème ?**

Partiellement. Sur un problème **déséquilibré** (les cas graves sont minoritaires), l'**accuracy seule
est trompeuse**. Nous calculons bien un `classification_report` (precision/recall/F1) et une matrice de
confusion, mais **dans les logs uniquement**, et la sélection du « meilleur » modèle se fait sur
l'accuracy (voir §8).

- **Points forts :** `class_weight='balanced'`, `stratify=y` au split, analyse de la **feature
  importance** (top 10).
- **Pistes :** logguer **F1 macro / recall de la classe « grave » / ROC-AUC / PR-AUC** dans MLflow ;
  comparer à une **baseline** (`DummyClassifier`) ; évaluer par **sous-population** (agglo/hors-agglo,
  sexe, catégorie d'usager) — enjeu de fairness (§13).

---

## 8. Model Registry et sélection du modèle

- **Comment le modèle de production est-il choisi ?**

Le service `gravity_classification` sélectionne dynamiquement, via `MlflowClient.search_runs`, le run
**non-`FAILED` d'accuracy maximale** de l'expérience `random_forest_training`, puis le charge par
`runs:/{run_id}/model`.

- ⚠️ **Limites importantes :**
  - Ce n'est **pas** le **MLflow Model Registry** (pas de versions `Staging`/`Production`, pas d'alias
    `champion`/`challenger`).
  - La sélection sur l'**accuracy** est discutable pour des classes déséquilibrées.
  - Il subsiste un **chemin MinIO codé en dur** en fallback
    (`s3://mlflow/1/models/m-…/artifacts/model.pkl`) — fragile et non reproductible.
- **Piste :** enregistrer le modèle au **Registry**, promouvoir en `Production` via une **quality gate**
  (F1 > baseline), et faire charger le serving par alias plutôt que par recherche d'accuracy.

---

## 9. Serving / API

- **Comment le modèle est-il exposé ?**

Par un micro-service **FastAPI** (`gravity_classification.py`) avec un schéma **Pydantic**
`DonneesAccident` (36 features typées) et les endpoints `/load_best_model`, `/predict_gravite`,
`/estimer_gravite` (multipart vidéo + JSON → prédiction → persistance via `backend_sql`). Le modèle est
chargé en **lazy-load** et mis en cache dans une variable globale.

- ⚠️ **Limites :** pas d'authentification ni de rate limiting sur les endpoints modèles ; le
  rechargement d'un nouveau modèle nécessite un appel manuel à `/load_best_model` (pas de hot-reload sur
  promotion).

---

## 10. Tests

- **Quelle est votre couverture de tests ?**

Il existe des **tests pytest CRUD** (`backend_sql/pytests/crud_test/…` : caracts, lieux, usagers,
véhicules, resultat_ai, ai_training_data) et un `pytest.py` dans `gravity_classification`.

- ⚠️ **Limites :** **aucun test de données** (schéma/qualité), **aucun test de modèle** (F1 > seuil, pas
  de NaN, artefact produit), **aucun test de contrat d'API** ni de charge. La couverture n'est pas
  mesurée/publiée.
- **Piste :** ajouter les couches *data tests* + *model tests* + *serving contract tests* et un
  `pytest --cov` en CI.

---

## 11. CI / CD

- **Avez-vous une intégration/déploiement continu ?**

**Non.** Il n'y a pas de dossier `.github/` ni de pipeline GitLab CI. Les commits sont poussés
directement sur `main` (peu de branches/PR, pas de tags de release). Le déploiement se fait par
`docker compose up` manuel ; les images sont reconstruites localement, sans registry.

- **Piste prioritaire :** une **GitHub Actions** `lint → tests (unit + data + model) → build → scan`
  déclenchée sur PR, puis un CD `build → push registry → staging → prod`. C'est le poste où nous
  gagnerions le plus de points (10/100).

---

## 12. Déploiement progressif et rollback

- **Gérez-vous canary / shadow / rollback ?**

**Non** à ce stade. Le passage d'un modèle à l'autre est **brutal** (le serving prend le meilleur run au
prochain `/load_best_model`). Il n'y a ni **canary**, ni **shadow deployment**, ni **rollback
automatisé**.

- **Atténuation :** MLflow conserve tous les runs, donc un retour arrière est *possible* manuellement
  (pointer un `run_id` précédent). **Piste :** rollback en une commande via alias Registry.

---

## 13. Monitoring, alerting, fairness

- **Surveillez-vous le modèle en production ?**

**Non.** Pas de monitoring **système** (Prometheus/OpenTelemetry) au-delà des `healthcheck` Docker
(`/health`, `/minio/health/live`), et **pas de monitoring ML** (data drift, prediction drift/PSI,
dégradation de performance). Pas d'**alerting** (Slack/PagerDuty).

- ⚠️ **Enjeu spécifique :** sur un modèle qui estime une **gravité corporelle**, l'absence de suivi de
  drift et d'**évaluation d'équité par sous-population** est une vraie limite éthique et métier.
- **Pistes :** Evidently/Prometheus + dashboard « santé modèle » (AUC, latence, drift), alertes sur
  seuils, et une **Model Card** documentant limites, biais et modes d'échec.

---

## 14. Continuous Training et lineage

- **Le ré-entraînement est-il continu ? La lineage est-elle traçable ?**

Le ré-entraînement est **déclenché à la demande** (fin du DAG `import_csv_to_sql`), pas sur événement
(drift/planning). La traçabilité repose sur **MLflow** (run → params → métriques → artefact), mais la
chaîne **prédiction → run → dataset → données brutes → commit git** n'est pas complète (ni git commit
loggué au run, ni version de dataset, ni OpenLineage).

- **Pistes :** logguer le **git SHA** et le **digest dataset** dans chaque run ; déclencher un CT
  **sous quality gate** (jamais de déploiement aveugle).

---

## 15. Sécurité

- **Comment gérez-vous les secrets et la sécurité ?**

⚠️ **Point faible identifié.** Le `docker-compose.yml` contient des **secrets en clair** :
`POSTGRES_USER/PASSWORD: db/db`, `MINIO_ROOT_PASSWORD: minio123`, `AWS_SECRET_ACCESS_KEY: minio123`,
`PGADMIN_DEFAULT_PASSWORD: supersecret`, et un utilisateur Airflow `admin/admin`. De plus
`AIRFLOW__CORE__FERNET_KEY` est **vide** (connexions non chiffrées) et `LOAD_EXAMPLES: "true"` charge les
DAGs d'exemple.

- ✅ **Bon point :** `.gitignore` exclut `.env` et `.env.*`, donc les vrais secrets ne sont pas
  versionnés.
- **Pistes :** externaliser via `.env`/secrets manager, générer une vraie `FERNET_KEY`, désactiver les
  exemples, ajouter TLS + auth API, et un **scan** (bandit / trivy) en CI.

---

## 16. Gouvernance et vie privée

- **Documentation et conformité ?**

Pas encore de **Model Card** ni de **datasheet** du jeu de données. Les données BAAC concernent des
**personnes** (usagers) : nous excluons déjà les identifiants (`id`, `id_usager`, `lat/long`…) au
preprocessing, ce qui limite l'exposition, mais aucune **politique de rétention/anonymisation** n'est
formalisée.

---

## Bilan et auto-évaluation

- **Où en êtes-vous, et quelles sont vos priorités ?**

**Ce qui est solide :** containerisation complète, orchestration Airflow d'un pipeline
ingestion → training, experiment tracking MLflow avec stores Postgres + MinIO, serving FastAPI propre
avec sélection dynamique du modèle, preprocessing centralisé et déterministe, gestion du déséquilibre de
classes.

**Ce qui manque pour l'état de l'art :** CI/CD, Model Registry (champion/challenger + quality gate),
validation de données bloquante, tests data/modèle, monitoring + drift + alerting, rollback/canary,
data versioning et lineage complète, sécurité (secrets), gouvernance (Model Card, fairness).

### Auto-évaluation /100

| Domaine | Points | Auto-éval | Justification |
| --- | ---: | ---: | --- |
| Git + qualité logicielle | 5 | 2 | Pas de README/PR/tags, commits directs `main` |
| Reproductibilité | 8 | 5 | Docker ✓, seeds ✓ ; images non taguées, pas de README |
| Data versioning | 7 | 1 | Pas de DVC ni digest dataset |
| Data validation | 6 | 2 | Contrôle de schéma en warning, non bloquant |
| Experiment tracking | 6 | 5 | MLflow + Postgres + MinIO ✓ ; accuracy seule |
| Tests ML | 8 | 2 | CRUD seulement, pas de tests data/modèle |
| Pipeline automatisé | 8 | 5 | DAG ingestion→train ✓ ; DAGs vides, lock files |
| CI/CD | 10 | 0 | Absent |
| Model Registry | 5 | 1 | Sélection par accuracy, pas de Registry |
| Deploy / canary / rollback | 7 | 1 | Bascule brutale, pas de canary |
| Monitoring ML | 8 | 0 | Absent |
| Monitoring infra + alerting | 5 | 1 | Healthchecks Docker seulement |
| Lineage | 5 | 2 | MLflow partiel, pas de commit/dataset |
| Sécurité | 5 | 1 | Secrets en clair, Fernet vide |
| Gouvernance / doc | 4 | 0 | Pas de Model Card |
| Performance / coût | 3 | 1 | Pas de load test |
| **Total** | **100** | **≈ 29** | **« ML avec quelques outils Ops » → MLOps basique en cours** |

### Feuille de route (par impact décroissant)

1. **CI GitHub Actions** (lint + tests + build + scan) → +points immédiats, base de tout le reste.
2. **MLflow Model Registry + quality gate** (F1 > baseline) → sélection et rollback propres.
3. **Validation de données bloquante** (Great Expectations/Pandera) + **tests data/modèle**.
4. **Monitoring + drift + alerting** (Evidently/Prometheus) et **Model Card** (sujet sensible).
5. **Externaliser les secrets**, `FERNET_KEY`, désactiver `LOAD_EXAMPLES`.
6. **Data versioning + lineage** (digest dataset + git SHA loggués par run).

> _Livrable MLOps — projet « Gravité des accidents » (dépôt `nov23_alt_iia`). Document interne d'équipe._
