# Contribuer

## Stratégie de branches

Trois branches longue durée, une par environnement :

| Branche   | Environnement | Rôle |
| --------- | ------------- | ---- |
| `dev`     | development   | Branche par défaut / d'intégration (ancien `main`). Base de toute feature. |
| `staging` | staging       | Pré-production. Fusion de `dev` après validation CI. |
| `prod`    | production    | Production. Fusion de `staging`, déploiement gaté par revue. |

Flux de travail :

```
feature/ma-feature ──PR──▶ dev ──PR──▶ staging ──PR──▶ prod
```

- On ne pousse **jamais** directement sur `staging` ni `prod` : uniquement via Pull Request.
- Une PR ne peut être fusionnée que si la **CI est verte**.

## Convention de commits

Format `type: description` — types : `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.

Exemples : `feat: ajout endpoint predict_gravite`, `ci: pipeline build/push GHCR`.

## CI/CD

- **CI** (`.github/workflows/ci.yml`) : lint (ruff), tests (pytest + PostgreSQL), validation Docker — sur
  chaque PR et push vers `dev` / `staging` / `prod`.
- **CD** (`.github/workflows/cd.yml`) : build + push des images vers GHCR puis déploiement, sur push vers
  `staging` (env `staging`) et `prod` (env `production`).

## Réglages GitHub à faire une seule fois

Ces réglages ne peuvent pas être versionnés dans le dépôt ; à configurer dans l'UI GitHub :

1. **Settings → Branches → Default branch** : passer la branche par défaut à `dev`.
2. **Settings → Branches → Branch protection rules** pour `dev`, `staging`, `prod` :
   - Require a pull request before merging.
   - Require status checks to pass (CI).
   - (pour `prod`) Require approvals.
3. **Settings → Environments** : créer `staging` et `production` ; ajouter à `production` des
   *required reviewers* et les secrets de déploiement (`DEPLOY_HOST`, `DEPLOY_KEY`, …).
