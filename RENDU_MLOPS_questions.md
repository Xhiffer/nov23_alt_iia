# Rendu MLOps : grille de questions de soutenance

> Questionnaire au format DataScientest (question / réponse), ancré sur la stack réelle du dépôt
> `nov23_alt_iia` : **Airflow (Celery + Redis)**, **MLflow + MinIO (S3)**, **FastAPI `backend_sql` +
> microservices modèles + `api_gateway`**, **Docker Compose**, **PostgreSQL**, classifieurs
> `LogisticRegression / RandomForest / XGBoost / CatBoost / LightGBM / GradientBoosting / DecisionTree`.
>
> Objectif : permettre au jury (ou à l'équipe) de vérifier que le projet est **reproductible,
> automatisé, testé, tracé, observable, sécurisé et gouverné**, et pas seulement « Docker + une API ».

---

## 1. Structure, reproductibilité et environnement

- Le dépôt Git contient-il un `README` décrivant le problème métier, l'architecture et la procédure de
  lancement ? *(aujourd'hui absent à la racine)*
- Un `git clone` suivi d'une commande unique (`make`, `docker compose up airflow-init && up`) suffit-il à
  reconstruire l'ensemble de la stack ? Quelle est la commande exacte ?
- Les dépendances sont-elles figées ? Chaque service a son `requirements.txt` — les versions sont-elles
  épinglées (`==`) ou laissées libres ?
- Utilisez-vous des seeds contrôlées (`random_state`) partout où c'est nécessaire pour rendre un
  entraînement reproductible ? *(présent dans les params MLflow — est-ce systématique ?)*
- Les images Docker sont-elles versionnées (tag `model-api:1.x.y`) ou seulement `latest` / reconstruites
  à la volée ?
- Pourquoi le volume `./backend_sql/postgres-data` (données PostgreSQL) est-il committé dans le dépôt ?
  N'est-ce pas un risque de reproductibilité et de fuite de données ?

## 2. Versioning des données

- Comment versionnez-vous le jeu de données d'accidents (BAAC) ? Un outil type **DVC / lakeFS** est-il en
  place, ou seulement les CSV bruts ? *(pas de `dvc.yaml` détecté)*
- Pouvez-vous associer un modèle donné à la **version exacte** des données qui l'a produit
  (hash / fingerprint du dataset, nombre de lignes, date) ?
- Le découpage **train / validation / test** est-il défini de manière stable et reproductible, ou
  recalculé à chaque run ?
- Enregistrez-vous le **schéma** et les **statistiques** du dataset d'entraînement (via
  `mlflow.data` / digest) pour établir la *lineage* données → modèle ?

## 3. Validation automatique des données

- Le DAG `csv_bdd_dag` (import CSV → SQL) effectue-t-il une **validation de schéma** avant insertion
  (types, colonnes obligatoires, valeurs manquantes, doublons, plages) ?
- Que se passe-t-il si un CSV arrive avec une colonne manquante ou renommée (ex. `annual_revenue_v2`) ?
  Le pipeline échoue-t-il proprement ou insère-t-il des données corrompues ?
- Comment détectez-vous une anomalie de **volume** (fichier tronqué) ou un **train/serve skew** entre les
  colonnes utilisées à l'entraînement et celles reçues par l'API de prédiction ?
- Le mécanisme actuel de `lock files` (`import_*.lock`, `check_lock_file`) garantit-il l'ordre des tâches,
  mais valide-t-il la **qualité** des données importées, ou seulement leur présence ?

## 4. Feature engineering reproductible

- Les transformations de `general_tain_setup.py` (`remove_excluded_columns`, `remove_lat_long_columns`,
  `remove_vma_column`…) sont-elles **déterministes** et couvertes par des tests ?
- La **même** chaîne de features est-elle appliquée à l'entraînement **et** à l'inférence, ou existe-t-il
  un risque de divergence entre le training et le service `gravity_classification` ?
- Le `scaler.pkl` loggué dans MLflow est-il rechargé côté serving, ou le scaling est-il ré-appliqué
  différemment en production ?
- Certaines features dépendent-elles du type de modèle (ex. `remove_vma_column` seulement pour les
  modèles non-arbres) ? Comment garantissez-vous que le bon preprocessing suit le bon modèle ?

## 5. Experiment tracking (MLflow)

- Pour un run MLflow donné, pouvez-vous répondre à : *« Pourquoi ce modèle précis est-il en production ? »*
  Le run trace-t-il **git commit + version dataset + hyperparamètres + seed + métriques + artefacts** ?
- Combien de runs comparables avez-vous (10, 50, 100+) et comparez-vous réellement les 7 algorithmes
  (`LogisticRegression`, `RandomForest`, `XGBoost`, `CatBoost`, `LightGBM`…) dans une même expérience ?
- Les métriques logguées se limitent-elles à `accuracy`, ou incluez-vous des métriques adaptées à un
  problème de **classification déséquilibrée** (gravité d'accident) ?

## 6. Évaluation ML sérieuse

- Au-delà de l'accuracy, mesurez-vous **precision / recall / F1 / ROC-AUC / PR-AUC** par classe de
  gravité ? La classe la plus rare (tués/blessés graves) est-elle correctement évaluée ?
- Comparez-vous le modèle candidat à une **baseline** (DummyClassifier, régression logistique, modèle
  actuellement déployé) ?
- Évaluez-vous la performance par **sous-population** (type d'usager, milieu urbain/rural, conditions
  météo) pour détecter des écarts ?
- Le `class_weight` observé dans les params MLflow suffit-il à traiter le déséquilibre, ou avez-vous testé
  d'autres stratégies (rééchantillonnage, seuil ajusté) ?

## 7. Tests (code, data, modèle, pipeline, serving)

- Les tests actuels (`backend_sql/pytests/crud_test/…`) couvrent le **CRUD**. Où sont les tests de
  **data** (schéma, qualité) et de **modèle** (F1 > seuil, pas de NaN, artefact produit) ?
- Testez-vous que l'entraînement **converge** et **produit un artefact** avant de considérer un run réussi ?
- Avez-vous des tests de **contrat d'API** sur `api_gateway` et les microservices (réponse, requête
  malformée, latence) ?
- Quel est le **taux de couverture** actuel, et sur quel périmètre (backend seul ? scripts de training ?) ?

## 8. Pipeline ML automatisé (Airflow)

- Le DAG `train_model_dag.py` est **vide** dans le dépôt : l'entraînement est-il réellement orchestré par
  Airflow, ou lancé manuellement (cf. `actuall_problem.txt`) ?
- Pouvez-vous montrer le DAG de bout en bout `ingestion → validation → preprocessing → training →
  evaluation → register` sous forme de graphe, sans exécution manuelle de script ?
- La coordination par `lock files` remplace-t-elle les **dépendances de tâches** natives d'Airflow ?
  Pourquoi ce choix plutôt que des `TaskFlow` / `dependencies` explicites ?

## 9. CI (intégration continue)

- Il n'y a pas de dossier `.github/` : existe-t-il une **CI** (GitHub Actions / GitLab CI) déclenchée à
  chaque Pull Request ?
- Si oui, quelles étapes : `lint → tests unitaires → tests data → tests modèle → scan sécurité →
  build image` ? Un badge « CI passing » / « coverage » est-il disponible ?
- L'historique Git montre des commits directs sur `main` : utilisez-vous des **branches + Pull Requests +
  tags/releases** pour tracer les changements ?

## 10. CD (déploiement continu)

- Le déploiement se fait-il par un pipeline automatisé (build → registry → staging → tests d'intégration →
  prod), ou par `docker compose up` manuel sur la machine ?
- Les images sont-elles poussées dans un **registry** versionné, ou reconstruites localement à chaque fois
  (`build: context: …`) ?

## 11. Model Registry

- Utilisez-vous le **MLflow Model Registry** (stages `Staging` / `Production`, alias `champion` /
  `challenger`), ou seulement le suivi d'expériences ?
- Comment le service `gravity_classification` sait-il **quelle version** de modèle charger ? Par un alias
  registry, ou par un chemin d'artefact codé en dur ?
- Pouvez-vous remonter d'une version de modèle registry → run MLflow → commit git → dataset ?

## 12. Quality gate avant production

- Existe-t-il une **porte de qualité automatique** qui refuse la promotion d'un modèle si
  `F1 < baseline` ou `latence > seuil` ?
- Pouvez-vous démontrer un cas où la CI/pipeline **bloque volontairement** un mauvais modèle ? *(preuve
  très forte en soutenance)*

## 13. Déploiement progressif

- Le passage d'une version de modèle à la suivante est-il **brutal (100 %)** ou progressif
  (**canary 95/5 → 50/50 → 0/100**) ?
- Avez-vous envisagé un **shadow deployment** (le modèle candidat reçoit le trafic en parallèle, sans
  impacter l'utilisateur) pour comparer avant bascule ?

## 14. Rollback

- En cas d'incident, combien de temps / de commandes faut-il pour revenir à la version précédente du
  modèle ? Le registry conserve-t-il les versions antérieures pour ce retour arrière ?
- Pouvez-vous faire une **démo de rollback** (déployer vN+1, simuler une erreur, revenir à vN) ?

## 15. Monitoring système (infra)

- Collectez-vous des métriques système (requests/sec, latence p50/p95/p99, taux d'erreur, CPU/RAM) sur
  `api_gateway` et les microservices ? Avec quel outil (Prometheus / OpenTelemetry) ?
- Le healthcheck actuel se limite à `/health` sur `app` et `/minio/health` : est-ce suffisant pour
  affirmer que le système « fonctionne » ?

## 16. Monitoring ML (drift & performance)

- Surveillez-vous le **data drift**, le **prediction drift** (PSI) et la dégradation de performance du
  classifieur de gravité une fois en production ?
- Comment détecteriez-vous que la distribution des accidents a évolué (nouvelle année de données BAAC) et
  que le modèle se dégrade ?
- Existe-t-il un **dashboard** « santé du modèle » (AUC, latence, drift, error rate) ?

## 17. Alerting

- Le monitoring déclenche-t-il des **alertes** (Slack / e-mail / PagerDuty) sur des symptômes à impact
  réel (drift > seuil pendant N minutes, taux d'erreur, échec de pipeline) ?
- Sur quoi alertez-vous : sur chaque anomalie technique, ou sur les symptômes qui affectent réellement
  l'utilisateur ?

## 18. Continuous Training (CT)

- Un ré-entraînement peut-il être **déclenché** (planning, nouvelles données, drift, dégradation) ?
- Si un CT est mis en place, passe-t-il **obligatoirement** par les quality gates avant déploiement, ou
  ré-entraîne-t-on et déploie-t-on à l'aveugle ?

## 19. Lineage de bout en bout

- Pour une prédiction donnée, pouvez-vous remonter : `prédiction → version modèle → run MLflow →
  pipeline → version dataset → données brutes` ? Et dans l'autre sens ?
- Un standard type **OpenLineage** est-il envisagé, ou la traçabilité est-elle uniquement dans MLflow ?

## 20. Infrastructure as Code

- L'infrastructure est-elle décrite en **IaC** (Terraform / Pulumi / Helm), ou uniquement dans un
  `docker-compose.yml` lancé manuellement ?
- Les environnements **dev / staging / prod** sont-ils reproductibles à l'identique ?

## 21. Sécurité (⚠ points sensibles détectés)

- Le `docker-compose.yml` contient des **secrets en clair** : `POSTGRES_USER/PASSWORD: db/db`,
  `MINIO_ROOT_PASSWORD: minio123`, `AWS_SECRET_ACCESS_KEY: minio123`, `PGADMIN_DEFAULT_PASSWORD:
  supersecret`, `airflow users create … --password admin`. Pourquoi ne sont-ils pas externalisés
  (secrets manager / `.env` non committé) ?
- `AIRFLOW__CORE__FERNET_KEY: ""` est vide : les connexions Airflow ne sont donc **pas chiffrées**.
  Est-ce voulu ?
- `AIRFLOW__CORE__LOAD_EXAMPLES: "true"` charge les DAGs d'exemple en production : est-ce intentionnel ?
- Les API (`backend_sql`, `api_gateway`) ont-elles de l'**authentification**, du **rate limiting**, du
  **TLS** ? Y a-t-il un scan de dépendances / d'images (bandit, trivy) ?
- Les fichiers `.env` (`airflow/.env`, `backend_sql/.env`) sont-ils bien exclus du dépôt via
  `.gitignore` ?

## 22. Gouvernance du modèle

- Existe-t-il une **Model Card** (objectif, propriétaire, données d'entraînement/évaluation, métriques,
  limites, modes d'échec connus, contraintes de déploiement) pour le classifieur de gravité ?
- Un **datasheet** documente-t-il le jeu de données BAAC (provenance, licence, biais connus) ?

## 23. Fairness / IA responsable

- Sur un sujet aussi sensible que la **gravité corporelle d'un accident**, évaluez-vous la performance par
  groupe (âge, sexe de l'usager, région) pour détecter des écarts inacceptables ?
- Des seuils d'acceptation d'équité sont-ils documentés ?

## 24. Privacy

- Les données BAAC contiennent des informations sur des personnes (usagers). Avez-vous une politique de
  **minimisation / anonymisation / rétention** ? Qui accède aux données, pourquoi, et combien de temps ?

## 25. Observabilité complète

- Face à une **prédiction incorrecte signalée**, pouvez-vous passer de `request_id → trace → version
  modèle → features → dataset → run → commit` ?
- Les logs (fichier `logs/app.log` en `logging.INFO`) sont-ils centralisés et corrélés à des **metrics**
  et des **traces** (OpenTelemetry), ou restent-ils locaux au conteneur ?

## 26. Performance & coût

- Avez-vous mesuré latence p95/p99, débit, taille de modèle et **coût / 1000 prédictions** pour chaque
  service modèle ? Un modèle légèrement moins précis mais bien plus rapide serait-il préférable ?
- Des **load tests** ont-ils été réalisés sur `api_gateway` avant de considérer le système « prêt » ?

## 27. SLO / SLA

- Avez-vous défini des objectifs mesurables : `disponibilité > 99.x %`, `latence p95 < X ms`,
  `taux d'erreur < Y %`, `AUC modèle > Z`, `drift PSI < 0.2` ?

## 28. Gestion des incidents

- Disposez-vous de **runbooks** (`model_drift.md`, `api_down.md`, `bad_data.md`, `rollback.md`,
  `training_failure.md`) ?
- Le processus `détection → alerte → investigation → rollback → retrain → postmortem` est-il documenté ?

## 29. Architecture documentée

- Pouvez-vous présenter un **schéma d'architecture** reliant Git → CI/CD → stockage données → validation →
  training → MLflow Registry → Docker → serving (`api_gateway` + microservices) → monitoring → alertes ?
- Le rôle de chaque conteneur du `docker-compose` (db, app, mlflow, minio, redis, airflow-*, api_gateway,
  microservices modèles, frontend) est-il documenté ?

## 30. README professionnel

- Le README couvre-t-il : problème métier · architecture · dataset · modèle · reproduction locale ·
  training · tests · CI/CD · déploiement · monitoring · sécurité · limites ? *(à créer)*

---

## Dossier de preuves suggéré (`evidence/`)

À joindre au rendu pour **démontrer** plutôt qu'affirmer :

```
evidence/
├── 01_architecture.png          # schéma des conteneurs docker-compose
├── 02_data_lineage.png
├── 03_mlflow_experiments.png    # comparaison des 7 classifieurs
├── 04_model_registry.png        # stages champion/challenger
├── 05_pipeline_dag.png          # DAG Airflow d'entraînement (non vide)
├── 06_ci_pipeline.png           # GitHub Actions
├── 07_tests_report.html         # data + model tests, coverage
├── 08_deployment.png
├── 09_monitoring.png            # métriques infra + santé modèle
├── 10_drift_detection.png
├── 11_rollback.png
├── 12_security_scan.png         # trivy/bandit + secrets externalisés
└── 13_model_card.md
```

## Grille de notation /100 (adaptée du référentiel MLOps)

| Domaine | Points | État probable du dépôt |
| --- | ---: | --- |
| Git + qualité logicielle | 5 | Partiel (pas de README/PR/tags) |
| Reproductibilité | 8 | Partiel (compose ✓, versions/tags ?) |
| Data versioning | 7 | Manquant (pas de DVC) |
| Data validation | 6 | Manquant / à prouver |
| Experiment tracking | 6 | Présent (MLflow ✓) |
| Tests ML | 8 | Partiel (CRUD seulement) |
| Pipeline automatisé | 8 | Partiel (DAG train vide) |
| CI/CD | 10 | Manquant (pas de `.github/`) |
| Model Registry | 5 | À prouver |
| Deploy / canary / rollback | 7 | Manquant |
| Monitoring ML | 8 | Manquant |
| Monitoring infra + alerting | 5 | Partiel (healthchecks) |
| Lineage | 5 | Partiel (MLflow) |
| Sécurité | 5 | Faible (secrets en clair) |
| Gouvernance / doc | 4 | Manquant |
| Performance / coût | 3 | À prouver |
| **Total** | **100** | |

**Lecture :** `< 40` = ML avec quelques outils Ops · `40-60` = MLOps basique · `60-75` = bon projet ·
`75-90` = production-grade · `90+` = excellente démonstration.

> Priorité pour passer « à l'état de l'art » : compléter la **chaîne vérifiable de bout en bout**
> (Git → data versioning → validation → pipeline Airflow réel → MLflow + Registry → CI/CD → serving →
> monitoring/drift → alertes → rollback → lineage), plutôt que d'empiler de nouveaux outils.
