# Guide de dépannage Clay

## Problème : "The result of this run exceeded the cell size limit (200 kB)"

### Cause
Clay a renvoyé ce message d'erreur lors d'une tentative précédente, et maintenant il utilise ce message d'erreur comme URL !

### Solution

#### Étape 1 : Nettoyer la colonne dans Clay
1. Dans votre table Clay, trouvez la colonne HTTP API qui a échoué
2. **Supprimez la colonne** ou créez une nouvelle colonne HTTP API
3. Ne réutilisez PAS une colonne qui contient déjà des erreurs

#### Étape 2 : Configurer la nouvelle colonne correctement

**Configuration recommandée** :

```
Method: GET
URL: https://cloudinary-spwk.onrender.com/api/generate-url
```

**Query Parameters** :
| Key | Value |
|-----|-------|
| `url` | `{{Company Website}}` ou `{{Domain}}` |

⚠️ **Important** : Assurez-vous que la colonne source (`Company Website`) contient bien des URLs valides, pas des messages d'erreur !

**Advanced Settings** :
- Timeout: `60 seconds` (important !)
- Retry on failure: ✅ Activé
- Cache results: ✅ Activé

#### Étape 3 : Tester sur UNE SEULE ligne d'abord
1. Sélectionnez UNE ligne avec un domaine simple (ex: `google.com`)
2. Cliquez "Run"
3. Attendez 30-60 secondes
4. Vérifiez que vous obtenez une URL Cloudinary

#### Étape 4 : Si ça marche, lancez sur toutes les lignes
- Run all rows (mais par petits lots si vous avez beaucoup de lignes)

---

## Problème : Navigation Timeout (30000 ms exceeded)

### Cause
Certains sites web prennent trop de temps à charger complètement.

### ✅ Solution automatique implémentée
L'API continue maintenant même si le site timeout, elle prend un screenshot partiel.

### Si le problème persiste
1. Augmentez le timeout dans Clay à **90 secondes**
2. Vérifiez que l'URL du site est correcte et accessible

---

## Problème : L'API retourne une erreur mais pas de screenshot

### Vérifications
1. **L'URL est-elle valide ?**
   - ✅ Bon : `example.com` ou `https://example.com`
   - ❌ Mauvais : `example` ou `http://localhost`

2. **Le site est-il accessible ?**
   - Testez l'URL dans un navigateur
   - Certains sites bloquent les scrapers

3. **Render est-il éveillé ?**
   - Le premier appel prend 30-60 secondes (cold start)
   - Les appels suivants sont plus rapides

---

## Logs Render - Comment les consulter

1. Allez sur [render.com](https://render.com)
2. Ouvrez votre service `cloudinary-spwk`
3. Cliquez sur "Logs" dans le menu
4. Cherchez les lignes avec `[API]` pour voir ce qui se passe

**Logs normaux** :
```
[API] Processing: https://example.com
[API] Screenshot captured
[API] Uploaded to Cloudinary
```

**Logs d'erreur** :
```
[API] Error: Navigation Timeout Exceeded
[API] Error: Invalid URL format
```

---

## Réponses attendues

### Endpoint `/api/generate` (JSON)
```json
{
  "screenshot_url": "https://res.cloudinary.com/dqfnvegv2/image/upload/v1/screenshots/example-com.jpg"
}
```

### Endpoint `/api/generate-url` (Texte brut)
```
https://res.cloudinary.com/dqfnvegv2/image/upload/v1/screenshots/example-com.jpg
```

---

## Checklist complète pour Clay

- [ ] Nouvelle colonne HTTP API (pas une ancienne avec erreurs)
- [ ] URL correcte : `https://cloudinary-spwk.onrender.com/api/generate-url`
- [ ] Query param `url` configuré avec une colonne valide
- [ ] Timeout : 60 secondes minimum
- [ ] Retry activé
- [ ] Cache activé
- [ ] Test sur 1 ligne d'abord
- [ ] La colonne source contient des URLs valides (pas des erreurs)

---

## Encore des problèmes ?

### Option 1 : Test manuel avec curl
```bash
curl "https://cloudinary-spwk.onrender.com/api/generate-url?url=https://google.com"
```

Si ça fonctionne, le problème vient de la config Clay.

### Option 2 : Vérifier les logs Render
Les logs vous diront exactement quelle URL est reçue et quelle erreur se produit.

### Option 3 : Contacter le support
Si vraiment rien ne fonctionne après avoir suivi tous ces steps, il peut y avoir un problème avec Render ou Cloudinary.
