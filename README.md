# Screenshot API Flask - Déploiement Render

API Flask pour générer des screenshots avec flèche rouge et upload automatique sur Cloudinary.

## Déploiement sur Render

### Option 1 : Via GitHub (Recommandé)

1. **Créer un repo GitHub** pour le dossier `flask-api/` :

```bash
cd ~/Desktop/mon-screenshot-api/flask-api
git init
git add .
git commit -m "Initial commit: Screenshot API Flask"
gh repo create screenshot-api-flask --public --source=. --push
```

2. **Connecter à Render** :
   - Allez sur [render.com](https://render.com)
   - Cliquez "New +" → "Web Service"
   - Connectez votre repo GitHub `screenshot-api-flask`
   - Render détectera automatiquement `render.yaml`

3. **Configuration automatique** :
   - Name: `screenshot-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt && pyppeteer-install`
   - Start Command: `gunicorn app:app`
   - Plan: **Free**

4. **Déployer** :
   - Cliquez "Create Web Service"
   - Attendre 5-10 minutes (installation de Chromium)
   - URL obtenue : `https://screenshot-api-xxxx.onrender.com`

### Option 2 : Déploiement direct

```bash
# Installer Render CLI
npm install -g render-cli

# Se connecter
render login

# Déployer
render deploy
```

## Utilisation dans Clay

Une fois déployé sur Render, vous aurez une URL comme :
```
https://screenshot-api-xxxx.onrender.com
```

### Configuration Clay - HTTP API

1. **Dans votre table Clay**, ajoutez une colonne **HTTP API**

2. **Configuration** :

```
Method: GET
URL: https://screenshot-api-xxxx.onrender.com/api/generate
```

3. **Query Parameters** :

| Key | Value |
|-----|-------|
| `url` | `{{Company domain}}` |

4. **Advanced Settings** :
   - Timeout: `60 seconds` (important, génération prend du temps)
   - Retry on failure: ✅ Activé
   - Cache results: ✅ Activé

5. **Run** sur une ligne de test

6. **Réponse attendue** :

```json
{
  "success": true,
  "url": "https://example.com",
  "screenshot_url": "https://res.cloudinary.com/dqfnvegv2/image/upload/v1/screenshots/example-com.jpg",
  "message": "Screenshot generated and uploaded successfully"
}
```

### Mapper la réponse dans Clay

Dans la colonne **URL screen** (ou créer une nouvelle colonne) :

**Option A : Utiliser le résultat direct de l'HTTP API**

Clay devrait automatiquement extraire `screenshot_url` de la réponse.

**Option B : Formule pour extraire** (si besoin)

Si Clay retourne tout le JSON, créez une colonne Formula :

```javascript
// Extraire screenshot_url de la réponse HTTP API
const response = {{HTTP API Response}};
return response.screenshot_url;
```

## Test local (avant déploiement)

```bash
cd ~/Desktop/mon-screenshot-api/flask-api

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
pyppeteer-install

# Lancer l'API
python app.py
```

Tester :
```bash
curl "http://localhost:5000/api/generate?url=https://example.com"
```

## Endpoints disponibles

### GET /api/generate

Génère un screenshot avec flèche et upload sur Cloudinary.

**Paramètres** :
- `url` (required) : URL du site à screenshoter

**Exemple** :
```
GET /api/generate?url=https://example.com
```

**Réponse** :
```json
{
  "success": true,
  "url": "https://example.com",
  "screenshot_url": "https://res.cloudinary.com/dqfnvegv2/image/upload/v1/screenshots/example-com.jpg",
  "message": "Screenshot generated and uploaded successfully"
}
```

### GET /health

Health check de l'API.

**Réponse** :
```json
{
  "status": "ok"
}
```

## Configuration

Les paramètres de la flèche et du cercle sont dans `app.py` ligne 19 :

```python
CONFIG = {
    'arrow': {
        'startX': 85,  # Position de départ
        'endX': 60,    # Où la flèche pointe
        'width': 20    # Épaisseur
    },
    'circle': {
        'radius': 80   # Taille du cercle
    }
}
```

## Coûts

- **Render (Plan Free)** : Gratuit
  - 750h/mois
  - Se met en veille après 15min d'inactivité
  - Premier appel peut prendre 30s (cold start)

- **Cloudinary** : Gratuit (25GB stockage)

**Total : 0€**

## Troubleshooting

### Timeout sur Clay

Si vous avez des timeouts :
1. Augmenter le timeout Clay à 90 secondes
2. Le premier appel est lent (cold start Render)
3. Les appels suivants sont plus rapides

### Screenshot vide

Vérifiez les logs Render :
- Dashboard → Votre service → Logs
- Chercher les erreurs Python

### Render ne démarre pas

Vérifiez que `pyppeteer-install` est dans le build command.

## Mise à jour

Pour mettre à jour après modifications :

```bash
git add .
git commit -m "Update: amélioration de la flèche"
git push
```

Render redéploie automatiquement !

## Sécurité (Optionnel)

Pour protéger votre API avec une clé :

1. Ajouter dans Render : Environment Variables
   - `API_KEY` = `votre-clé-secrète`

2. Modifier `app.py` :

```python
@app.route('/api/generate', methods=['GET'])
def generate_screenshot():
    api_key = request.headers.get('X-API-Key')
    if api_key != os.environ.get('API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401
    # ... rest of code
```

3. Dans Clay, ajouter un Header :
   - Key: `X-API-Key`
   - Value: `votre-clé-secrète`

---

**Prêt à déployer !** 🚀
