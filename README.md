# nov23_alt_iia — Classification de la gravité des accidents (MLOps)

[![CI](https://github.com/Xhiffer/nov23_alt_iia/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/Xhiffer/nov23_alt_iia/actions/workflows/ci.yml)

Projet de fin de formation **Ingénieur IA (DataScientest, alternance nov. 2023)**.
Il industrialise un modèle de **classification supervisée de la gravité corporelle des accidents de la
route** (données **BAAC** : usagers / véhicules / lieux / caractéristiques) au sein d'une chaîne
**MLOps** complète : ingestion orchestrée, suivi d'expériences, stockage d'artefacts, et exposition du
modèle via API.

> Cible `grav` regroupée en binaire par `group_grav_values` : **0** = Indemne + Blessé léger,
> **1** = Tué + Blessé hospitalisé. Modèle de production : **RandomForestClassifier**
> (`class_weight='balanced'`).

---

## Sommaire

- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Structure du dépôt](#structure-du-dépôt)
- [Démarrage rapide](#démarrage-rapide)
- [Services et ports](#services-et-ports)
- [Variables d'environnement](#variables-denvironnement)
- [Pipeline ML (Airflow)](#pipeline-ml-airflow)
- [Suivi d'expériences (MLflow)](#suivi-dexpériences-mlflow)
- [Prédiction (serving)](#prédiction-serving)
- [Tests](#tests)
- [CI/CD et stratégie de branches](#cicd-et-stratégie-de-branches)
- [Sécurité](#sécurité)
- [Feuille de route MLOps](#feuille-de-route-mlops)
- [Licence](#licence)

---

## Architecture

```
                 ┌─────────┐   trigger    ┌──────────────┐
                 │ Airflow │─────────────▶│  backend_sql │ (FastAPI, CRUD + training)
                 │ (Celery)│  HTTP calls  └──────┬───────┘
                 └─────────┘                     │ log runs / artifacts
                      │                          ▼
                CSV ──┘                    ┌──────────┐   artifacts (S3)   ┌───────┐
                                           │  MLflow  │───────────────────▶│ MinIO │
                                           └────┬─────┘   metadata (SQL)   └───────┘
                                                ▼               │
                                          ┌──────────┐          ▼
   User ──▶ api_gateway ──▶ model services│PostgreSQL│◀── backend store
              (:7000)      (gravity :81,   └──────────┘
                           detection :83,
                           labelisation :82)
```

- **`backend_sql`** : API principale (CRUD des tables BAAC, import CSV→SQL, déclenchement des trainings).
- **Micro-services modèles** : `gravity_classification`, `accident_detection`, `accident_data_labelisation`.
- **`api_gateway`** : point d'entrée frontal qui route vers le backend et les modèles.
- **MLflow + MinIO + PostgreSQL** : tracking des runs (backend store PostgreSQL, artefacts sur MinIO/S3).
- **Airflow (CeleryExecutor + Redis)** : orchestration du pipeline ingestion → filtrage → entraînement.

## Stack technique

| Domaine        | Technologies |
| -------------- | ------------ |
| API / serving  | FastAPI, Uvicorn, Pydantic |
| ML             | scikit-learn (RandomForest, LogisticRegression, DecisionTree, GradientBoosting), XGBoost, LightGBM, CatBoost |
| MLOps          | MLflow, Airflow (Celery + Redis), MinIO (S3), Docker Compose |
| Données        | PostgreSQL, SQLAlchemy, Alembic, pandas |
| Qualité        | pytest, ruff (CI) |

## Structure du dépôt

```
.
├── airflow/                 # DAGs, logs, config Airflow
│   └── dags/                # csv_bdd_dag.py (pipeline principal), etl_data_dag.py, train_model_dag.py
├── backend_sql/             # API FastAPI principale
│   ├── controllers/         # logique métier CRUD
│   ├── models/              # modèles SQLAlchemy (usagers, vehicules, lieux, caract...)
│   ├── routers/             # routes FastAPI
│   ├── scripts/             # ETL + scripts d'entraînement (ai_models/*)
│   └── pytests/             # tests CRUD
├── models/                  # micro-services modèles
│   ├── gravity_classification/
│   ├── accident_detection/
│   └── accident_data_labelisation/
├── api_gateway/             # passerelle API
├── front/                   # frontend
├── docker-compose.yml       # orchestration de toute la stack
├── Dockerfile.mlflow        # image MLflow custom (avec boto3 pour MinIO)
├── RENDU_MLOPS_questions.md # grille d'évaluation MLOps
└── RENDU_MLOPS_reponses.md  # auto-évaluation MLOps du projet
```

## Démarrage rapide

**Prérequis :** Docker + Docker Compose, ~8 Go de RAM libres.

```bash
git clone https://github.com/Xhiffer/nov23_alt_iia.git
cd nov23_alt_iia

# 1) Copier et adapter les variables d'environnement
cp .env.example .env

# 2) Initialiser la base Airflow et créer l'utilisateur admin
docker compose up airflow-init

# 3) Lancer toute la stack
docker compose up -d
```

Puis déclencher le pipeline dans l'UI Airflow (<http://localhost:8080>) en activant le DAG
`import_csv_to_sql`.

## Services et ports

| Service                         | URL / port                | Description |
| ------------------------------- | ------------------------- | ----------- |
| `api_gateway`                   | <http://localhost:7000>   | Passerelle API frontale |
| `backend_sql`                   | <http://localhost:8000/docs> | API principale (Swagger) |
| `gravity_classification`        | <http://localhost:81>     | Prédiction de gravité |
| `accident_data_labelisation`    | <http://localhost:82>     | Labellisation |
| `accident_detection`            | <http://localhost:83>     | Détection |
| `frontend`                      | <http://localhost:5010>   | Interface |
| Airflow                         | <http://localhost:8080>   | Orchestrateur (admin/admin) |
| MLflow                          | <http://localhost:5000>   | Tracking UI |
| MinIO console                   | <http://localhost:9001>   | Stockage artefacts |
| PgAdmin                         | <http://localhost:8084>   | Administration PostgreSQL |
| Prometheus                      | <http://localhost:9090>   | Collecte des métriques |
| Grafana                         | <http://localhost:3000>   | Dashboards monitoring (admin/admin) |

## Variables d'environnement

Les secrets ne doivent **pas** être commités : `.env` est ignoré par Git. Voir [`.env.example`](.env.example)
pour la liste des variables (PostgreSQL, MinIO/S3, MLflow, Airflow). Adaptez les valeurs par environnement
(`dev` / `staging` / `prod`) et remplacez impérativement les mots de passe par défaut avant tout
déploiement réel.

## Pipeline ML (Airflow)

DAG `import_csv_to_sql` (`airflow/dags/csv_bdd_dag.py`), déclenché manuellement :

```
import_caracts → import_lieux → import_usagers → import_vehicules
   → import_ai_training_data          (/ai-training-data/filter-data/)
   → import_..._RandomForestClassifier (/ai-models/train/RandomForestClassifier/)
```

Chaque tâche est un `SimpleHttpOperator` qui appelle un endpoint de `backend_sql`.

## Suivi d'expériences (MLflow)

- `tracking_uri = http://mlflow:5000`, **backend store** PostgreSQL, **artifact store** `s3://mlflow/` (MinIO).
- Le script `backend_sql/scripts/ai_models/RandomForestClassifier.py` logue params, métrique `accuracy`
  et le modèle (`mlflow.sklearn.log_model`) dans l'expérience `random_forest_training`.
- Preprocessing centralisé et déterministe dans `backend_sql/scripts/general_tain_setup.py`.

## Prédiction (serving)

Le service `gravity_classification` charge dynamiquement le meilleur run MLflow et expose :

| Endpoint            | Méthode | Description |
| ------------------- | ------- | ----------- |
| `/load_best_model`  | POST    | (Re)charge le meilleur modèle depuis MLflow |
| `/predict_gravite`  | POST    | Prédiction à partir d'un JSON `DonneesAccident` (36 features) |
| `/estimer_gravite`  | POST    | Vidéo + JSON → prédiction → persistance via `backend_sql` |

## Monitoring ML

Deux couches complémentaires :

- **Observabilité temps réel — Prometheus + Grafana.** Le service `gravity_classification` est instrumenté
  (`prometheus-fastapi-instrumentator` + métriques custom) et expose `/metrics` :
  `gravity_predictions_total{predicted_class}`, `gravity_prediction_probability`,
  `gravity_predict_latency_seconds`, `gravity_predict_errors_total`, plus les métriques HTTP standard.
  Prometheus (`monitoring/prometheus.yml`) les scrape ; Grafana charge automatiquement la datasource et le
  dashboard *Gravity Classification — ML Monitoring* (`monitoring/grafana/`).
- **Détection de drift — Evidently.** L'endpoint `POST /monitoring/drift-report/` compare un jeu de
  référence (données d'entraînement) à une fenêtre courante et renvoie
  `{dataset_drift, drift_share, n_drifted_features, alert}` + un rapport HTML
  (`backend_sql/monitoring_reports/`). Le seuil d'alerte est réglable via `DRIFT_SHARE_THRESHOLD`. Le DAG
  Airflow `ml_monitoring_drift` l'exécute quotidiennement.

> Limites : la fenêtre « courante » du drift est un **proxy** (dernières lignes de la table
> d'entraînement) tant qu'un journal des features de prédiction en production n'existe pas ; l'alerting se
> limite aux logs (à router vers Slack/PagerDuty ou des règles Grafana).

## Tests

```bash
cd backend_sql
pip install -r requirements.txt
pytest pytests/ -v
```

Les tests CRUD utilisent `fastapi.testclient` et nécessitent une base PostgreSQL accessible (fournie par
le service `postgres` en CI).

## CI/CD et stratégie de branches

Le projet suit un modèle **trois environnements** :

| Branche   | Environnement | Rôle |
| --------- | ------------- | ---- |
| `dev`     | development   | Branche d'intégration par défaut (ancien `main`). Toute PR cible `dev`. |
| `staging` | staging       | Pré-production. Reçoit `dev` après validation. |
| `prod`    | production    | Production. Reçoit `staging` (déploiement protégé par revue). |

Flux : `feature/* → PR → dev → staging → prod`.

- **CI** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) : sur chaque PR et push vers
  `dev`/`staging`/`prod` — **lint (ruff)**, **tests (pytest + PostgreSQL)**, **validation des images
  Docker**.
- **CD** ([`.github/workflows/cd.yml`](.github/workflows/cd.yml)) : sur push vers `staging` et `prod` —
  **build + push des images** vers GHCR (tag = environnement + SHA), puis **job de déploiement** rattaché
  à l'environnement GitHub correspondant (revue requise pour `production`).

Voir [`CONTRIBUTING.md`](CONTRIBUTING.md) pour la convention de commits et le workflow de PR.

## Sécurité

⚠️ Le `docker-compose.yml` actuel contient des identifiants **par défaut** (développement local
uniquement). Avant tout déploiement :

- Externaliser tous les secrets via `.env` / un gestionnaire de secrets (jamais en clair dans le compose).
- Générer une vraie `AIRFLOW__CORE__FERNET_KEY`.
- Passer `AIRFLOW__CORE__LOAD_EXAMPLES` à `false`.
- Ajouter authentification + TLS sur les API exposées.

## Feuille de route MLOps

L'auto-évaluation détaillée (≈ 59/100) et la feuille de route priorisée figurent dans
[`RENDU_MLOPS_reponses.md`](RENDU_MLOPS_reponses.md). La gouvernance du modèle est documentée dans
[`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) et [`docs/DATASET_DATASHEET.md`](docs/DATASET_DATASHEET.md).
Prochaines priorités : MLflow Model Registry + quality gate, validation de données bloquante,
monitoring/drift, branchement effectif des secrets (`.env` → compose).

## Licence

Projet pédagogique — usage interne à l'équipe et à la formation.
