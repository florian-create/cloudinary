# 📸 Batch Screenshot - Guide d'utilisation

Script local optimisé pour générer des milliers de screenshots en parallèle.

## 🎯 Pourquoi utiliser ce script au lieu de l'API Render ?

| Aspect | API Render | Script Local |
|--------|------------|--------------|
| **Vitesse** | ~30h pour 3700 URLs | **1.5-3h** en parallèle |
| **Coût** | $7/mo + usage CPU | **Gratuit** (ton CPU) |
| **Contrôle** | ❌ Limité | ✅ Pause/reprise, retry |
| **Cache** | ✅ Cloudinary | ✅ Cloudinary + vérif locale |
| **Progression** | ❌ Invisible | ✅ Temps réel avec ETA |
| **Stabilité** | ⚠️ Timeouts réseau | ✅ Retry automatique |

## 🚀 Installation

### 1. Installer les dépendances locales

```bash
cd /Users/florian/Desktop/cloudinary-fix
pip install -r requirements.txt
pyppeteer-install
```

### 2. Préparer ton CSV

Ton CSV doit avoir une colonne avec les URLs. Exemple :

```csv
company_name,website,country
Acme Corp,https://acme.com,France
Widget Inc,widget.io,USA
Tech Solutions,www.techsolutions.fr,France
```

**Note** : Le script accepte les URLs avec ou sans `https://`, avec ou sans `www.`

## 📝 Utilisation

### Option A : Depuis un CSV (RECOMMANDÉ pour 3700 URLs)

Édite `batch_screenshot_local.py` ligne 245-246 :

```python
# Décommenter ces lignes
urls = load_urls_from_csv('ton_fichier.csv', url_column='website')

# Commenter la liste de test
# urls = [...]
```

Puis lance :

```bash
python batch_screenshot_local.py
```

### Option B : Liste manuelle (pour tester)

Le script contient déjà une liste de test. Lance directement :

```bash
python batch_screenshot_local.py
```

## ⚙️ Configuration

Dans `batch_screenshot_local.py`, ligne 31-40 :

```python
CONFIG = {
    'concurrent_workers': 10,  # 🔧 AJUSTER ICI
    'width': 1200,
    'height': 800,
    'quality': 80,
    'wait_after_load': 1.5
}
```

### Recommandations `concurrent_workers`

| Machine | RAM | Workers recommandés | Temps (3700 URLs) |
|---------|-----|--------------------:|------------------:|
| MacBook Air M1 | 8GB | **10** | ~3-4h |
| MacBook Pro M1/M2 | 16GB | **15-20** | ~1.5-2h |
| PC Gaming | 16GB+ | **20-30** | ~1-1.5h |
| Serveur | 32GB+ | **50+** | ~30-45min |

**⚠️ Attention** : Plus de workers = plus de RAM utilisée (~200-300MB par worker)

## 📊 Output

### Pendant l'exécution

```
🚀 Starting batch processing of 3700 URLs
⚙️  Concurrent workers: 10
📁 Output file: screenshot_results.csv

🔍 Checking cache...
⚡ Cache HIT: https://google.com
⚡ Cache HIT: https://github.com
📊 Cache results: 1245/3700 already exist
🎯 Will generate: 2455 new screenshots

📸 Capturing: https://example.com
✅ Success: https://example.com → https://res.cloudinary.com/...
📊 Progress: 523/3700 (14.1%) | ✅ 1768 | ❌ 12 | ⏱️ 8.3/s | ETA: 6.4min
```

### Résultat final

**Fichier CSV généré** : `screenshot_results.csv`

```csv
url,screenshot_url,status,error,timestamp
https://acme.com,https://res.cloudinary.com/.../acme-com.jpg,success,,2025-11-04T15:30:45
https://widget.io,https://res.cloudinary.com/.../widget-io.jpg,cached,,2025-11-04T15:30:45
https://bad-url.com,,error,Navigation timeout,2025-11-04T15:31:12
```

**Colonnes** :
- `url` : URL source
- `screenshot_url` : Lien Cloudinary (ou vide si erreur)
- `status` : `success` | `cached` | `error`
- `error` : Message d'erreur (si échec)
- `timestamp` : Horodatage

## 🔄 Reprendre après interruption

Si le script plante ou que tu l'interromps (Ctrl+C) :

1. **Relancer simplement** : Le cache Cloudinary est déjà vérifié, donc les screenshots existants seront skip instantanément
2. **Filtrer les erreurs** : Ouvre `screenshot_results.csv`, filtre par `status=error`, crée un nouveau CSV avec ces URLs, et relance

## 💡 Astuces

### 1. Lancer la nuit
```bash
# Lancer en arrière-plan
nohup python batch_screenshot_local.py > batch.log 2>&1 &

# Suivre la progression
tail -f batch.log
```

### 2. Traiter par lots
Pour 3700 URLs, tu peux découper en lots de 500 :

```python
urls_batch_1 = urls[0:500]
urls_batch_2 = urls[500:1000]
# etc.
```

### 3. Ignorer les erreurs récurrentes

Si certains domaines timeoutent toujours (ex: sites bloquant les bots), crée une blacklist :

```python
blacklist = ['problematic-site.com', 'another-bad-one.io']
urls = [u for u in urls if not any(b in u for b in blacklist)]
```

## 🐛 Dépannage

### Erreur : `Browser closed unexpectedly`
- Réduis `concurrent_workers` (10 → 5)
- Ferme les autres apps pour libérer de la RAM

### Trop lent
- Augmente `concurrent_workers` (10 → 20)
- Réduis `wait_after_load` (1.5 → 1.0)

### Beaucoup d'erreurs "Navigation timeout"
- Augmente `navigation_timeout` (20000 → 30000)

## 📈 Estimation de temps

**Formule** : `Temps = (URLs totales - Cached) / (Workers × 2.5/s)`

Exemples pour 3700 URLs (0% cached) :

- 5 workers : ~5h
- 10 workers : ~2.5h
- 20 workers : ~1.2h
- 50 workers : ~30min

**Avec cache 30%** (déjà fait) : Divise par ~1.5

## 🆚 Quand utiliser l'API vs Script local ?

| Utilise l'API Render | Utilise le script local |
|----------------------|------------------------|
| < 50 URLs | > 100 URLs |
| Intégration avec Clay | Batch processing |
| Pas de setup local | Tu as Python installé |
| Screenshots à la demande | Screenshots massifs planifiés |

## ✅ Checklist avant de lancer

- [ ] CSV prêt avec colonne URLs
- [ ] `pyppeteer-install` exécuté
- [ ] `concurrent_workers` ajusté selon ta RAM
- [ ] Assez d'espace disque (~50MB temporaire pour 3700 URLs)
- [ ] Pas d'apps lourdes en arrière-plan
- [ ] Cloudinary config vérifiée (credentials dans le script)

Prêt à lancer ! 🚀
