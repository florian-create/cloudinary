# 💻 Configuration optimale pour MacBook Air M1

Guide complet pour traiter 3700 URLs sans faire exploser ton Mac.

## 🔥 Comprendre les limites du MacBook Air

### ✅ Ce qui est génial
- **Puce M1** : Ultra-efficiente, 8 cœurs performants
- **Architecture ARM** : Consomme peu d'énergie
- **RAM unifiée** : Accès mémoire ultra-rapide
- **Thermal throttling** : Le CPU ralentit automatiquement au lieu de crasher

### ⚠️ Ce qui est limité
- **Pas de ventilateur** : Refroidissement passif uniquement
- **Surchauffe > 80°C** : Le CPU ralentit (normal, c'est pour te protéger)
- **RAM limitée** : 8GB ou 16GB selon ton modèle

## 🎯 Configuration recommandée par RAM

### Si tu as **8GB de RAM**

```python
CONFIG = {
    'concurrent_workers': 4,  # Conservateur mais sûr
    'batch_delay': 0.8
}
```

**Performance** :
- 3700 URLs en **~5-6 heures**
- CPU : 40-60%
- RAM : 50-60%
- Température : Tiède (pas de throttling)
- ✅ Tu peux continuer à utiliser ton Mac normalement

### Si tu as **16GB de RAM** (recommandé)

```python
CONFIG = {
    'concurrent_workers': 6,  # Déjà configuré par défaut
    'batch_delay': 0.5
}
```

**Performance** :
- 3700 URLs en **~3-4 heures**
- CPU : 60-75%
- RAM : 60-70%
- Température : Chaud mais OK
- ⚠️ Ferme les autres apps (Chrome, Slack, etc.)

### Mode "Turbo" (si tu es pressé)

```python
CONFIG = {
    'concurrent_workers': 10,
    'batch_delay': 0.3
}
```

**Performance** :
- 3700 URLs en **~2-2.5 heures**
- CPU : 85-95%
- RAM : 80-85%
- Température : **Très chaud** (throttling probable après 30-60min)
- ❌ Ne pas utiliser le Mac pendant ce temps

## 🌡️ Monitoring en temps réel

Le script affiche maintenant CPU et RAM :

```
📊 Progress: 520/3700 (14.1%) | ✅ 520 | ❌ 0 | ⏱️ 4.2/s | ETA: 12.6min | 💻 CPU: 68% | 🧠 RAM: 62%
```

### 🚦 Signaux d'alerte

| Signal | Signification | Action |
|--------|---------------|--------|
| CPU < 70% | ✅ Parfait | Continue |
| CPU 70-80% | ⚠️ Chaud | Normal, surveille |
| CPU > 80% | 🔥 Très chaud | Réduis `concurrent_workers` |
| RAM < 75% | ✅ OK | Continue |
| RAM > 85% | ⚠️ Limite | Réduis `concurrent_workers` |

### Warning automatique

Si CPU > 80% ou RAM > 85%, le script affiche :

```
⚠️  CPU usage high: 87% - Consider reducing workers
⚠️  RAM usage high: 88% - Consider reducing workers
```

**Action** : Stoppe le script (Ctrl+C) et relance avec moins de workers.

## 🧊 Conseils pour garder le Mac frais

### 1. **Position du Mac**
- ✅ Sur un bureau dur et plat
- ✅ Pas de housse/étui
- ❌ Pas sur le lit/coussin/genoux
- ❌ Pas au soleil

### 2. **Fermer les apps gourmandes**
```bash
# Avant de lancer le script
# Ferme :
- Google Chrome (surtout avec beaucoup d'onglets)
- Slack / Discord / Teams
- Zoom / Meet
- Photoshop / Final Cut
- Docker Desktop

# Garde ouvert :
- Terminal (pour le script)
- Activity Monitor (pour surveiller)
```

### 3. **Surveiller la température** (optionnel)

Install iTerm2 + monitoring :
```bash
# Installer iStats
sudo gem install iStats

# Voir la température en temps réel
istats cpu temp
```

Température normale :
- **Idle** : 35-45°C
- **Batch script (6 workers)** : 60-75°C
- **Throttling commence** : 80°C+
- **Max safe** : 100°C (mais on veut éviter ça)

## 🔄 Stratégies d'exécution

### Stratégie 1 : "Je peux attendre" (RECOMMANDÉ) ✅

**Config** : 6 workers (par défaut)
**Durée** : 3-4h
**Avantages** :
- Mac reste utilisable
- Pas de surchauffe
- Fiable

**Commande** :
```bash
python batch_screenshot_local.py
```

### Stratégie 2 : "Overnight" 🌙

**Config** : 4 workers (conservateur)
**Durée** : 5-6h
**Avantages** :
- Lance le soir, résultats le matin
- Zéro stress pour le Mac
- Zéro surveillance nécessaire

**Commande** :
```bash
# Avant de dormir
nohup python batch_screenshot_local.py > batch.log 2>&1 &

# Le matin
cat screenshot_results.csv
```

### Stratégie 3 : "Urgent" 🔥

**Config** : 10 workers (turbo)
**Durée** : 2-2.5h
**Inconvénients** :
- Mac très chaud
- Throttling probable
- Consommation élevée

**À faire** :
1. Fermer **toutes** les autres apps
2. Brancher sur secteur
3. Position optimale (bureau, ventilation)
4. Surveiller Activity Monitor

**Commande** :
```bash
# Éditer batch_screenshot_local.py ligne 36
concurrent_workers: 10

python batch_screenshot_local.py
```

## 📊 Tableau récapitulatif

| Workers | Durée | CPU | RAM | Température | Usage Mac |
|---------|-------|-----|-----|-------------|-----------|
| 4 | 5-6h | 40-60% | 50-60% | 😊 Tiède | ✅ Normal |
| **6** | **3-4h** | **60-75%** | **60-70%** | 😐 Chaud | ⚠️ Léger |
| 10 | 2-2.5h | 85-95% | 80-85% | 🔥 Très chaud | ❌ Éviter |

## 🎬 Checklist avant de lancer

- [ ] **RAM disponible** : Ferme Chrome, Slack, etc.
- [ ] **Branché sur secteur** : Ne pas utiliser sur batterie
- [ ] **Ventilation OK** : Bureau plat, pas de housse
- [ ] **Pas d'autres tâches** : Pas de build, backup, etc. en cours
- [ ] **Workers configurés** : 6 pour 16GB, 4 pour 8GB
- [ ] **Test avec 10 URLs** : Vérifie que ça marche avant le gros batch

## 🐛 Que faire si...

### Le Mac devient trop chaud
```
1. Ctrl+C pour arrêter le script
2. Laisser refroidir 5-10 min
3. Réduire concurrent_workers de 2
4. Relancer (le cache skip les URLs déjà faites)
```

### Le script est trop lent
```
1. Vérifier que tu es sur secteur (pas batterie)
2. Fermer toutes les autres apps
3. Augmenter concurrent_workers de 2
4. Surveiller CPU/RAM
```

### "Out of Memory" error
```
1. Arrêter le script
2. Redémarrer le Mac (vider la RAM)
3. Réduire concurrent_workers à 4
4. Relancer
```

## 💡 Bonus : Split en batches

Si tu stresses vraiment pour ton Mac, découpe en batches :

```python
# Au lieu de tout en une fois
urls = load_urls_from_csv('companies.csv')

# Découpe en 4 batches de ~900
batch_1 = urls[0:925]
batch_2 = urls[925:1850]
batch_3 = urls[1850:2775]
batch_4 = urls[2775:]

# Lance batch 1, laisse refroidir 30min, puis batch 2, etc.
asyncio.run(process_batch(batch_1, output_csv='results_1.csv'))
```

## ✅ Conclusion

**Pour MacBook Air M1** :
- **8GB RAM** → 4 workers → 5-6h → Zéro stress
- **16GB RAM** → 6 workers → 3-4h → Configuration par défaut ✅
- **Pressé** → 10 workers → 2-2.5h → Surveillance requise

**Ton Mac va bien s'en sortir** ! Le M1 est conçu pour ce genre de tâche. Le throttling est là pour te protéger, pas de panique. 😎
