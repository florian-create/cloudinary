# Tests des endpoints

## Test local (après avoir lancé `python app.py`)

### Test endpoint JSON
```bash
curl "http://localhost:5000/api/generate?url=https://example.com"
```

**Réponse attendue** :
```json
{
  "screenshot_url": "https://res.cloudinary.com/dqfnvegv2/image/upload/v1/screenshots/example-com.jpg"
}
```

### Test endpoint texte brut
```bash
curl "http://localhost:5000/api/generate-url?url=https://example.com"
```

**Réponse attendue** :
```
https://res.cloudinary.com/dqfnvegv2/image/upload/v1/screenshots/example-com.jpg
```

### Test health check
```bash
curl "http://localhost:5000/health"
```

**Réponse attendue** :
```json
{
  "status": "ok"
}
```

## Test sur Render (après déploiement)

Remplacer `YOUR_RENDER_URL` par votre URL Render.

### Test endpoint JSON
```bash
curl "https://YOUR_RENDER_URL.onrender.com/api/generate?url=https://example.com"
```

### Test endpoint texte brut
```bash
curl "https://YOUR_RENDER_URL.onrender.com/api/generate-url?url=https://example.com"
```

### Test health check
```bash
curl "https://YOUR_RENDER_URL.onrender.com/health"
```

## Différences entre les endpoints

| Endpoint | Format réponse | Taille | Cas d'usage |
|----------|---------------|--------|-------------|
| `/api/generate` | JSON | ~100 bytes | Standard, facile à parser |
| `/api/generate-url` | Texte brut | ~80 bytes | Clay avec limite de taille |

## Résolution des problèmes

### Erreur "exceeded cell size limit" dans Clay
✅ **Solution** : Utiliser `/api/generate-url` au lieu de `/api/generate`

### Timeout dans Clay
✅ **Solution** : Augmenter le timeout à 60-90 secondes dans Clay

### Erreur 400 "Missing URL parameter"
❌ **Problème** : Le paramètre `url` n'est pas fourni
✅ **Solution** : Vérifier la configuration des Query Parameters dans Clay

### Erreur 400 "Invalid URL format"
❌ **Problème** : L'URL fournie n'est pas valide
✅ **Solution** : S'assurer que la colonne dans Clay contient un domaine valide (ex: `example.com` ou `https://example.com`)
