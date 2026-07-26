# Data versioning & lineage

Ce projet sépare **deux niveaux de traçabilité** des données :

1. **Versioning des données brutes** avec **DVC** (les 4 CSV BAAC), stockées hors
   git sur le **MinIO** déjà présent dans la stack (S3-compatible).
2. **Lineage par run** dans MLflow : chaque modèle entraîné est tagué avec une
   **empreinte déterministe du jeu d'entraînement** (`dataset_digest`) et le **SHA
   du commit git** du code (`git_sha`).

---

## 1. Versioning des données brutes (DVC + MinIO)

### Pourquoi

Les fichiers `backend_sql/scripts/csv/*.csv` (~33 Mo) sont aujourd'hui **versionnés
dans git**. DVC les remplace par de petits fichiers-pointeurs `*.csv.dvc` (le
contenu part sur MinIO), ce qui garde le dépôt léger tout en gardant l'historique
exact des données récupérable par `dvc pull`.

### Prérequis

```bash
pip install "dvc[s3]"
```

La stack tourne (`docker compose up -d`) pour que MinIO soit joignable, et les
identifiants MinIO sont exportés (mêmes valeurs que le `.env`) :

```bash
export AWS_ACCESS_KEY_ID="$MINIO_ROOT_USER"
export AWS_SECRET_ACCESS_KEY="$MINIO_ROOT_PASSWORD"
```

### Mise en place (une seule fois)

```bash
# 1) Initialiser DVC dans le dépôt
dvc init

# 2) Déclarer MinIO comme remote S3 (bucket "dvc" à créer dans la console MinIO :9001)
dvc remote add -d minio s3://dvc
dvc remote modify minio endpointurl http://localhost:9000

# 3) Placer les CSV bruts sous contrôle DVC (crée les *.csv.dvc, retire les CSV de git)
dvc add backend_sql/scripts/csv/caract-2023.csv \
        backend_sql/scripts/csv/lieux-2023.csv \
        backend_sql/scripts/csv/usagers-2023.csv \
        backend_sql/scripts/csv/vehicules-2023.csv

# 4) Pousser le contenu sur MinIO
dvc push

# 5) Committer les pointeurs + la config (jamais les CSV eux-mêmes)
git add .dvc/config .dvcignore \
        backend_sql/scripts/csv/*.csv.dvc \
        backend_sql/scripts/csv/.gitignore
git commit -m "chore(data): track BAAC CSVs with DVC (MinIO remote)"
```

> `dvc add` ajoute automatiquement les CSV à un `.gitignore` local et crée les
> `*.csv.dvc`. Vérifier avec `git status` qu'aucun CSV brut ne reste suivi par git.

### Utilisation au quotidien

```bash
dvc pull      # récupérer les données après un clone / checkout
dvc status    # vérifier que données et pointeurs sont synchronisés
dvc push      # après avoir modifié un CSV suivi
```

> ⚠️ Tant que `dvc push` n'a pas été exécuté vers MinIO, un clone frais n'aura pas
> les données (c'est le comportement normal de DVC). Exécuter la mise en place
> ci-dessus une fois la stack démarrée.

---

## 2. Lineage par run (MLflow)

Implémenté dans [`backend_sql/scripts/lineage.py`](../backend_sql/scripts/lineage.py)
et appelé depuis `RandomForestClassifier.py` à l'intérieur du run MLflow.

Chaque run est tagué et paramétré avec :

| Clé | Sens |
| --- | --- |
| `dataset_digest` | SHA-256 déterministe du contenu du DataFrame d'entraînement (valeurs + colonnes) |
| `dataset_rows` / `dataset_cols` | Dimensions du jeu d'entraînement |
| `dataset_columns` | Liste ordonnée des colonnes |
| `git_sha` | SHA du commit git du code (via `GIT_COMMIT_SHA`, sinon `git rev-parse`, sinon `unknown`) |

**Provenance du code :** injecter le SHA au lancement pour qu'il apparaisse dans
MLflow (le conteneur n'embarque pas `.git`) :

```bash
GIT_COMMIT_SHA=$(git rev-parse HEAD) docker compose up -d app
```

`GIT_COMMIT_SHA` est déjà câblé sur le service `app` dans `docker-compose.yml`
(défaut vide → `unknown`).

### Reproductibilité

Deux runs avec le **même `dataset_digest` et le même `git_sha`** partent des mêmes
données et du même code : combiné aux `random_state=42` fixés, l'entraînement est
reproductible. Un digest qui change alors que le git_sha est identique signale une
**dérive des données**, pas du code (et inversement).
