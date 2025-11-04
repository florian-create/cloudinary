# Configuration Render Dashboard

⚠️ **IMPORTANT** : Le fichier `render.yaml` n'est utilisé que lors de la création initiale du service. Pour modifier la configuration d'un service existant, il faut utiliser le dashboard Render.

## Configuration requise dans le dashboard Render

### 1. Build Command
```bash
pip install -r requirements.txt && pyppeteer-install
```

### 2. Start Command (IMPORTANT)
```bash
gunicorn app:app --timeout 180 --workers 1 --threads 2 --worker-tmp-dir /dev/shm --max-requests 10 --max-requests-jitter 5
```

**Explication des paramètres :**
- `--timeout 180` : Timeout de 180s (vs 120s par défaut) pour laisser le temps aux sites lents
- `--workers 1` : Un seul worker pour économiser la RAM
- `--threads 2` : 2 threads pour gérer 2 requêtes simultanées
- `--worker-tmp-dir /dev/shm` : Utilise la RAM au lieu du disque (plus rapide)
- `--max-requests 10` : Recycle le worker après 10 requêtes (évite memory leaks)
- `--max-requests-jitter 5` : Ajoute du random (5-15 requêtes) pour éviter de recycler tous les workers en même temps

### 3. Environment Variables
```
PYTHON_VERSION=3.11.0
WEB_CONCURRENCY=1
```

## Comment modifier la configuration

1. Va sur le dashboard Render : https://dashboard.render.com/
2. Clique sur ton service `cloudinary`
3. Va dans **Settings**
4. Scroll jusqu'à **Build & Deploy**
5. Modifie le **Start Command** avec la commande ci-dessus
6. Clique sur **Save Changes**
7. Le service va automatiquement redéployer

## Vérification

Une fois déployé, vérifie les logs :
- Tu dois voir : `[INFO] Starting gunicorn 21.2.0` avec `--timeout 180`
- **Pas** : `--timeout 120` (ancienne config)

## Timeouts actuels

| Composant | Timeout | Raison |
|-----------|---------|--------|
| Gunicorn worker | 180s | Temps max pour traiter une requête |
| Code Python (global_timeout) | 90s | Timeout pour générer un screenshot |
| Navigation Chromium | 20s | Chargement initial de la page |
| Network idle | 4s | Attente réseau inactif |
| Image loading | 6s | Chargement des images |

Total théorique max : ~90s par requête
Temps typique : 20-40s pour un nouveau screenshot, <1s pour un screenshot en cache
