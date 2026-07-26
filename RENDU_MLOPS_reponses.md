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
- ✅ Une **CI/CD GitHub Actions** et une **stratégie de branches par environnement** (`dev` / `staging` /
  `prod`) sont désormais en place (voir §11).
- ⚠️ Il nous manque encore le **Model Registry** formel, le **monitoring en production** et le
  **ré-entraînement continu (CT)** pour prétendre pleinement au niveau 2.

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
- ✅ Un **`README.md`** complet documente désormais l'architecture, les services/ports, le quickstart, le
  pipeline, les tests et la CI/CD ; un **`.env.example`** liste les variables d'environnement à fournir.
- ⚠️ **Limites restantes :** images non taguées (`build` local, pas de `model-api:1.x.y`) ; dépendances
  dans des `requirements.txt` par service dont les versions ne sont pas toutes épinglées ; pas de
  `Makefile` « one-command reproduce ».
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

✅ **MLflow Model Registry + quality gate mis en place** (*fait*).

- **À l'entraînement** (`RandomForestClassifier.py`) : le modèle est loggué (logged-model API MLflow 3.x),
  **enregistré** au Registry sous `gravity_classification`, et une **quality gate** décide de l'alias :
  promotion en **`champion`** seulement si `f1_macro ≥ F1_PROMOTION_THRESHOLD` (0.55 par défaut) **et** au
  moins aussi bon que le champion courant ; sinon **`challenger`**. Le `f1_macro` est désormais loggué en
  plus de l'accuracy.
- **Au serving** (`gravity_classification.py`) : le modèle est chargé par **alias**
  (`models:/gravity_classification@champion`), avec repli sur le meilleur run par accuracy. Le **chemin
  MinIO codé en dur a été supprimé**.
- **Vérifié en réel :** entraînement → version 2 enregistrée → `champion → v2` → le serving répond
  `source: registry:champion`, `version: 2`, `f1_macro ≈ 0.70`, `accuracy ≈ 0.80`.

- ⚠️ **Limites restantes :** pas encore de stage `Staging`/promotion multi-étapes ni de **rollback
  automatisé** via le Registry (le repli champion→ancienne version est manuel) ; la baseline du gate est
  un seuil fixe (pas de comparaison à un DummyClassifier).

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

✅ **Oui, désormais en place.** Nous avons adopté une **stratégie de branches à trois environnements** :
`dev` (ex-`main`, branche d'intégration par défaut) → `staging` → `prod`, documentée dans
`CONTRIBUTING.md`. Deux workflows **GitHub Actions** ont été ajoutés :

- **CI** (`.github/workflows/ci.yml`), sur chaque PR et push vers `dev`/`staging`/`prod` :
  **lint (ruff)** + **tests (pytest sur une base PostgreSQL de service)** + **validation Docker**
  (`docker compose config` + build de l'image backend).
- **CD** (`.github/workflows/cd.yml`), sur push vers `staging` et `prod` : **build + push des images** de
  tous les services vers **GHCR** (tag = environnement + SHA), puis un **job de déploiement rattaché à
  l'environnement GitHub** correspondant (revue requise possible sur `production`).

- ⚠️ **Limites / à finaliser :**
  - le **lint ruff** est encore en `continue-on-error` (non bloquant, le temps d'assainir le code) ;
  - les tests restent **CRUD uniquement** (pas encore de tests data/modèle dans la CI) ;
  - le **job `deploy` est un placeholder** (echo) : il reste à câbler sur la cible réelle
    (SSH + `docker compose pull && up -d`, ou k8s) ;
  - la **protection de branches** et les **Environments** GitHub (reviewers, secrets de déploiement)
    doivent être configurés dans l'UI (non versionnables).
- ✅ Reste à ajouter : tags/releases sémantiques et un **scan de sécurité** (bandit/trivy) dans la CI.

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

✅ **Mis en place et vérifié en conditions réelles.**

- **Observabilité temps réel :** le service `gravity_classification` est instrumenté (Prometheus via
  `prometheus-fastapi-instrumentator` + métriques custom : distribution des classes prédites, probabilité,
  latence d'inférence, erreurs). **Prometheus** scrape `/metrics` (vérifié `200 OK`) et **Grafana** (up,
  `database: ok`) affiche un dashboard provisionné (débit, latence p95, prédictions par classe, erreurs).
- **Drift ML :** endpoint `POST /monitoring/drift-report/` basé sur **Evidently** (data drift +
  target drift), exécuté quotidiennement par le DAG Airflow `ml_monitoring_drift` (seuil
  `DRIFT_SHARE_THRESHOLD`). **Testé en réel** sur 783 lignes → `16/37 features en drift`,
  `drift_share = 0.43 > 0.30` → **`alert: true`** + rapport HTML généré.

- ⚠️ **Limites restantes :** la fenêtre « courante » du drift est un **proxy** (split de la table
  d'entraînement — d'où un drift élevé — tant qu'il n'y a pas de journal des features de prédiction en
  production) ; l'**alerting** se limite aux logs (à router vers Slack/PagerDuty ou des règles Grafana) ;
  pas encore de suivi de **performance online** (nécessite les labels réels).
- 🐞 **Souci découvert en exécutant la chaîne :** l'**entraînement RF échoue silencieusement** (0 run
  MLflow, donc le serving renvoie « No valid model »). Le script `RandomForestClassifier.py` **avale son
  exception** dans un `try/except` global et la tâche Airflow est malgré tout marquée `success`
  (`No data found` → `Target column 'grav' not found`, race entre le filtre et l'entraînement).
  **✅ Corrigé** : endpoint de training bloquant + échec franc + gate « données prêtes » (voir §8).
- ⚠️ **Enjeu spécifique :** sur un modèle de **gravité corporelle**, l'**évaluation d'équité par
  sous-population** reste à mener (voir Model Card §5).

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
- ✅ **Premier pas fait :** un **`.env.example`** documente désormais toutes les variables à externaliser
  (avec des valeurs `change_me` et la commande de génération de `FERNET_KEY`), et le `README` rappelle de
  remplacer les identifiants par défaut avant tout déploiement.
- ✅ **Fait :** le `docker-compose.yml` est **entièrement branché sur `.env`** (`${VAR}` pour db, minio,
  pgadmin, AWS, URI MLflow, base + admin Airflow), avec une **`FERNET_KEY` réelle** propagée à tous les
  services Airflow et `LOAD_EXAMPLES=false`. Plus aucun secret en clair dans le fichier versionné ;
  `docker compose config` valide la résolution. Un vrai `.env` (gitignoré) reprend les valeurs courantes.
- ⚠️ **Reste :** TLS + authentification sur les API exposées, et un **scan** (bandit / trivy) dans la CI.
  Note d'application : après un `docker compose up` avec la nouvelle `FERNET_KEY`, recréer la connexion
  Airflow `backend_sql` si nécessaire.

---

## 16. Gouvernance et vie privée

- **Documentation et conformité ?**

✅ Une **Model Card** ([`docs/MODEL_CARD.md`](docs/MODEL_CARD.md)) et un **Datasheet** du jeu de données
([`docs/DATASET_DATASHEET.md`](docs/DATASET_DATASHEET.md)) ont été rédigés (structure complète, sections
usage/limites/fairness/privacy), avec des champs `À COMPLÉTER` pour les valeurs réelles (métriques,
propriétaires, licence, rétention). Les données BAAC concernent des **personnes** (usagers) : nous
excluons déjà les identifiants (`id`, `id_usager`, `lat/long`…) au preprocessing, ce qui limite
l'exposition.

- ⚠️ **Reste à faire :** renseigner les placeholders (notamment métriques réelles et **analyse
  d'équité**), et formaliser la **politique de rétention/anonymisation**.

---

## Bilan et auto-évaluation

- **Où en êtes-vous, et quelles sont vos priorités ?**

**Ce qui est solide :** containerisation complète, orchestration Airflow d'un pipeline
ingestion → training, experiment tracking MLflow avec stores Postgres + MinIO, serving FastAPI propre
avec sélection dynamique du modèle, preprocessing centralisé et déterministe, gestion du déséquilibre de
classes, et désormais **documentation (`README`/`CONTRIBUTING`)** + **CI/CD GitHub Actions** avec une
**stratégie de branches `dev`/`staging`/`prod`**, un **monitoring ML** (Prometheus + Grafana +
Evidently), des **fiches de gouvernance** (Model Card, Datasheet), et un **Model Registry avec quality
gate champion/challenger** (serving chargé par alias).

**Bug bloquant découvert puis corrigé :** l'entraînement RF échouait silencieusement (exception avalée +
race avec le filtrage) → aucun modèle en MLflow. **✅ Résolu** : endpoint bloquant + échec franc + gate
« données prêtes ». La chaîne complète (import → filtre → **entraînement → run MLflow → serving charge le
modèle**) tourne désormais en réel (accuracy ≈ 0.80).

**Ce qui manque pour l'état de l'art :** validation de données bloquante, tests data/modèle,
**alerting** effectif (les métriques/drift existent mais restent en logs) + suivi de performance online,
**rollback automatisé**/canary, data versioning et lineage complète, branchement effectif des secrets
(`.env` → compose). Côté gouvernance, la Model
Card et le Datasheet existent désormais mais restent à compléter (métriques réelles, **analyse
d'équité**). Côté CI/CD, il reste à durcir le lint, ajouter un scan sécurité et câbler le déploiement réel.

### Auto-évaluation /100

| Domaine | Points | Auto-éval | Justification |
| --- | ---: | ---: | --- |
| Git + qualité logicielle | 5 | 4 | README + CONTRIBUTING + branches `dev`/`staging`/`prod` + PR ; manque tags/releases, protections |
| Reproductibilité | 8 | 6 | Docker ✓, seeds ✓, README + `.env.example` ✓ ; images non taguées |
| Data versioning | 7 | 1 | Pas de DVC ni digest dataset |
| Data validation | 6 | 5 | Schéma **Pandera bloquant** avant entraînement + tests ; reste validation à l'ingestion |
| Experiment tracking | 6 | 5 | MLflow + Postgres + MinIO ✓ ; accuracy seule |
| Tests ML | 8 | 5 | CRUD + tests data (Pandera) + preprocessing + **smoke modèle** ; reste tests serving/contract |
| Pipeline automatisé | 8 | 6 | DAG ingestion→train→modèle ✓ (échec silencieux + race **corrigés**) ; reste orchestration à durcir |
| CI/CD | 10 | 7 | CI (lint + **scan bandit** + tests data/modèle + docker) + CD GHCR ✓ ; lint/scan non bloquants, deploy placeholder |
| Model Registry | 5 | 4 | Registry + gate champion/challenger + serving par alias ✓ ; pas de rollback auto/staging |
| Deploy / canary / rollback | 7 | 1 | Bascule brutale, pas de canary |
| Monitoring ML | 8 | 6 | Prometheus + Evidently **vérifiés en réel** (drift 0.43 → alert) ; fenêtre proxy, perf online absente |
| Monitoring infra + alerting | 5 | 3 | Prometheus + Grafana ✓ ; alerting encore en logs seulement |
| Lineage | 5 | 2 | MLflow partiel, pas de commit/dataset |
| Sécurité | 5 | 4 | Secrets externalisés (.env, compose en `${VAR}`) + Fernet réelle + LOAD_EXAMPLES=false ; reste TLS/auth/scan |
| Gouvernance / doc | 4 | 3 | Model Card + Datasheet rédigés ; placeholders (métriques/fairness) à remplir |
| Performance / coût | 3 | 1 | Pas de load test |
| **Total** | **100** | **≈ 63** | **Bon projet MLOps** |

### Feuille de route (par impact décroissant)

0. ✅ **Entraînement réparé** (*fait*) : endpoint de training rendu **bloquant** (renvoie 500/504 en cas
   d'échec au lieu de fire-and-forget toujours-200), `try/except` masquant retiré (échec franc), et
   **barrière « données prêtes »** ajoutée (attente de la table avant entraînement). Vérifié : un run
   MLflow réel est loggué (`accuracy ≈ 0.80`) et le serving `gravity_classification` le charge (HTTP 200).
1. ✅ **CI/CD GitHub Actions + branches `dev`/`staging`/`prod`** — *fait* ; reste à durcir le lint,
   ajouter un scan sécurité (bandit/trivy) et câbler le déploiement réel.
2. ✅ **MLflow Model Registry + quality gate** — *fait* (champion/challenger sur `f1_macro`, serving par
   alias, chemin MinIO codé en dur supprimé) ; reste le **rollback automatisé** et un stage `Staging`.
3. ✅ **Validation de données bloquante (Pandera)** + **tests data** en CI — *fait* (schéma appliqué
   avant l'entraînement, 5 tests) ; reste les tests **modèle/serving** et la validation à l'ingestion.
4. ✅ **Monitoring ML** (Prometheus + Grafana + Evidently) — *fait* ; reste à câbler l'**alerting**
   (Slack/PagerDuty ou règles Grafana) et le suivi de **performance online**.
5. ✅ **Secrets externalisés** (`.env` → `docker-compose.yml` en `${VAR}`, `FERNET_KEY` réelle,
   `LOAD_EXAMPLES=false`) — *fait* ; reste TLS + auth API + scan (bandit/trivy) en CI.
6. **Data versioning + lineage** (digest dataset + git SHA loggués par run).

> _Livrable MLOps — projet « Gravité des accidents » (dépôt `nov23_alt_iia`). Document interne d'équipe._
