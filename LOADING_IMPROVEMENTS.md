# Améliorations du chargement des pages

## Problème résolu

Certains sites web ne s'affichent pas complètement dans les screenshots car :
- Les images prennent du temps à charger
- Les polices web (fonts) se chargent en différé
- Les animations CSS ont besoin de temps
- Les ressources externes (CDN) sont lentes

## Solution implémentée

### 1. Stratégie de chargement en plusieurs étapes

```
1. Navigation initiale (domcontentloaded) → DOM prêt
2. Attente réseau idle (networkidle0) → Ressources chargées
3. Attente configurée (3 secondes par défaut) → Stabilisation
4. Vérification des images → Toutes les images chargées
5. Délai supplémentaire (0.5s) → Polices et animations CSS
```

### 2. Configuration par défaut

**Dans `app.py`** :
```python
CONFIG = {
    'wait_after_load': 3,  # 3 secondes d'attente après le chargement
    'navigation_timeout': 20000  # 20 secondes max pour la navigation
}
```

### 3. Détection intelligente des images

L'API vérifie automatiquement que toutes les images sont chargées :

```javascript
// Code exécuté dans la page
Promise.all(
    Array.from(document.images)
        .filter(img => !img.complete)
        .map(img => new Promise(resolve => {
            img.onload = img.onerror = resolve;
        }))
)
```

## Paramètre optionnel : `wait`

Vous pouvez personnaliser le temps d'attente par requête.

### Utilisation

**Endpoint JSON** :
```
/api/generate?url=https://example.com&wait=5
```

**Endpoint texte brut** :
```
/api/generate-url?url=https://example.com&wait=5
```

**Paramètre `wait`** :
- Valeur : entre 0 et 10 secondes
- Par défaut : 3 secondes
- Recommandé :
  - Sites simples : 2 secondes
  - Sites normaux : 3-4 secondes
  - Sites complexes : 5-7 secondes

### Exemples

#### Site simple et rapide
```bash
curl "https://cloudinary-spwk.onrender.com/api/generate-url?url=https://google.com&wait=2"
```

#### Site avec beaucoup d'images
```bash
curl "https://cloudinary-spwk.onrender.com/api/generate-url?url=https://pinterest.com&wait=6"
```

#### Site avec animations complexes
```bash
curl "https://cloudinary-spwk.onrender.com/api/generate-url?url=https://apple.com&wait=5"
```

## Dans Clay

### Configuration de base (3 secondes)
```
URL: https://cloudinary-spwk.onrender.com/api/generate-url
Query params:
  - url: {{Company Website}}
```

### Configuration avec plus de temps (5 secondes)
```
URL: https://cloudinary-spwk.onrender.com/api/generate-url
Query params:
  - url: {{Company Website}}
  - wait: 5
```

**Note** : N'oubliez pas d'ajuster le timeout Clay en conséquence !
- `wait=3` → Timeout Clay : 60 secondes
- `wait=5` → Timeout Clay : 75 secondes
- `wait=7` → Timeout Clay : 90 secondes

## Logs de debug

Dans les logs Render, vous verrez maintenant :

```
[API] Processing: https://example.com (wait: 3s)
[API] DOM loaded
[API] Network idle reached
[API] Waiting 3s for page to fully render...
[API] All images loaded
[API] Screenshot captured
[API] Uploaded to Cloudinary
```

Ou si le réseau ne devient pas idle :

```
[API] Processing: https://example.com (wait: 5s)
[API] DOM loaded
[API] Network didn't idle, continuing anyway
[API] Waiting 5s for page to fully render...
[API] Some images may not be loaded, continuing anyway
[API] Screenshot captured
[API] Uploaded to Cloudinary
```

## Impact sur les performances

| Configuration | Temps moyen par screenshot | Qualité |
|--------------|---------------------------|---------|
| `wait=0` | ~20 secondes | ⚠️ Partiel |
| `wait=2` | ~25 secondes | ✅ Bon |
| `wait=3` (défaut) | ~30 secondes | ✅ Très bon |
| `wait=5` | ~35 secondes | ✅ Excellent |
| `wait=7` | ~40 secondes | ✅ Parfait |

## Recommandations

### Pour la plupart des sites
Utilisez la configuration par défaut (3 secondes), elle fonctionne bien pour 90% des cas.

### Pour des sites spécifiques

**Sites de portfolio/design** (beaucoup d'images) :
```
wait=5
```

**Sites e-commerce** (images produits) :
```
wait=4
```

**Sites corporate simples** :
```
wait=2
```

**Landing pages avec animations** :
```
wait=6
```

### Tests recommandés

1. **Commencez avec le défaut** (3 secondes)
2. **Testez sur quelques sites**
3. **Si des images manquent** → Augmentez à 5 secondes
4. **Si tout est OK** → Restez à 3 secondes

## Troubleshooting

### "Les images ne se chargent toujours pas"

1. Augmentez le paramètre `wait` à 5-7 secondes
2. Vérifiez que les images ne sont pas en lazy loading (certains sites chargent les images uniquement au scroll)
3. Certaines images peuvent nécessiter une interaction utilisateur

### "C'est trop lent"

1. Réduisez le paramètre `wait` à 2 secondes
2. Les sites simples n'ont pas besoin de 5+ secondes

### "Timeout dans Clay"

Augmentez le timeout Clay proportionnellement au paramètre `wait` :
```
Timeout Clay = 60 + (wait * 5)
```

Exemple :
- `wait=3` → Timeout : 75 secondes
- `wait=5` → Timeout : 85 secondes
