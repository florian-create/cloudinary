# Screenshot API - Cloudinary

API Flask pour générer des screenshots de sites web et les uploader automatiquement sur Cloudinary.

## Fonctionnalités

✅ Screenshot automatique de n'importe quel site web
✅ Suppression intelligente des bandeaux de cookies et popups
✅ Upload automatique sur Cloudinary
✅ Déployable gratuitement sur Render
✅ Prêt à utiliser avec Clay

## Déploiement sur Render

### 1. Via GitHub (Recommandé)

Le code est déjà sur GitHub : https://github.com/florian-create/cloudinary

1. **Connecter à Render** :
   - Allez sur [render.com](https://render.com)
   - Cliquez "New +" → "Web Service"
   - Connectez votre repo GitHub `cloudinary`
   - Render détectera automatiquement `render.yaml`

2. **Configuration automatique** :
   - Name: `screenshot-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt && pyppeteer-install`
   - Start Command: `gunicorn app:app`
   - Plan: **Free**

3. **Déployer** :
   - Cliquez "Create Web Service"
   - Attendre 5-10 minutes (installation de Chromium)
   - URL obtenue : `https://screenshot-api-xxxx.onrender.com`

## Utilisation

### Endpoint principal

```
GET /api/generate?url=https://example.com
```

**Paramètres optionnels** :
- `wait` : Temps d'attente en secondes après le chargement (0-10, défaut: 3)

**Exemples** :
```bash
# Avec délai par défaut (3 secondes)
curl "https://cloudinary-spwk.onrender.com/api/generate-url?url=https://example.com"

# Avec délai personnalisé (5 secondes pour sites complexes)
curl "https://cloudinary-spwk.onrender.com/api/generate-url?url=https://example.com&wait=5"
```

**Réponse** :
```json
{
  "screenshot_url": "https://res.cloudinary.com/dqfnvegv2/image/upload/v1/screenshots/example-com.jpg"
}
```

### Test local

```bash
cd screenshot-api-clean

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

## Intégration avec Clay

### ⚠️ DEUX OPTIONS DISPONIBLES

#### Option 1 : Endpoint JSON (Recommandé)

**URL** : `/api/generate`

1. Dans votre table Clay, ajoutez une colonne **HTTP API**
2. **Configuration** :
   - Method: `GET`
   - URL: `https://your-render-url.onrender.com/api/generate`
3. **Query Parameters** :
   | Key | Value | Note |
   |-----|-------|------|
   | `url` | `{{Company domain}}` | Requis |
   | `wait` | `5` | Optionnel : 0-10 secondes (défaut: 3) |
4. **Advanced Settings** :
   - Timeout: `75 seconds` (ajustez si vous changez `wait`)
   - Retry on failure: ✅
   - Cache results: ✅

**Réponse** :
```json
{
  "screenshot_url": "https://res.cloudinary.com/..."
}
```

#### Option 2 : Endpoint Texte Brut (Si Clay limite la taille)

**URL** : `/api/generate-url`

Si vous obtenez l'erreur "exceeded the cell size limit", utilisez cet endpoint qui retourne **uniquement l'URL en texte brut** (pas de JSON) :

1. Dans votre table Clay, ajoutez une colonne **HTTP API**
2. **Configuration** :
   - Method: `GET`
   - URL: `https://your-render-url.onrender.com/api/generate-url`
3. **Query Parameters** :
   | Key | Value | Note |
   |-----|-------|------|
   | `url` | `{{Company domain}}` | Requis |
   | `wait` | `5` | Optionnel : 0-10 secondes (défaut: 3) |
4. **Advanced Settings** :
   - Timeout: `75 seconds` (ajustez si vous changez `wait`)
   - Retry on failure: ✅
   - Cache results: ✅

**Réponse** : Texte brut directement utilisable
```
https://res.cloudinary.com/dqfnvegv2/image/upload/v1/screenshots/example-com.jpg
```

## Gestion des cookies et popups

L'API supprime automatiquement :
- ✅ Bandeaux de cookies (GDPR)
- ✅ Popups de consentement
- ✅ Modales
- ✅ Newsletters popups
- ✅ Publicités

Outils supportés :
- OneTrust
- Tarteaucitron
- Axeptio
- Didomi
- Cookie Consent
- Et la plupart des solutions standard

## Configuration

Les paramètres sont dans `app.py` :

```python
CONFIG = {
    'width': 1200,    # Largeur du screenshot
    'height': 800,    # Hauteur du screenshot
    'format': 'jpeg', # Format (jpeg ou png)
    'quality': 85     # Qualité (1-100)
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
- Augmenter le timeout Clay à 90 secondes
- Le premier appel est lent (cold start Render)
- Les appels suivants sont plus rapides

### Screenshot contient encore des cookies
- Certains sites utilisent des techniques avancées
- Vous pouvez ajouter des sélecteurs CSS spécifiques dans le code

### Render ne démarre pas
- Vérifier que `pyppeteer-install` est dans le build command
- Consulter les logs Render pour les erreurs

## Mise à jour

Pour mettre à jour après modifications locales :

```bash
git add .
git commit -m "Description des changements"
git push
```

Render redéploie automatiquement !

## Endpoints disponibles

### GET /
Page d'accueil avec infos sur l'API

### GET /api/generate
Génère un screenshot et l'upload sur Cloudinary

**Paramètres** :
- `url` (required) : URL du site

**Réponse JSON** :
```json
{
  "screenshot_url": "https://res.cloudinary.com/..."
}
```

### GET /api/generate-url
Version minimaliste qui retourne l'URL en texte brut (pas de JSON)

**Paramètres** :
- `url` (required) : URL du site

**Réponse texte brut** :
```
https://res.cloudinary.com/dqfnvegv2/image/upload/v1/screenshots/example-com.jpg
```

### GET /health
Health check de l'API

## Technologies

- Flask (API)
- Pyppeteer (Chromium headless)
- Cloudinary (Stockage images)
- Render (Hébergement)

---

**Prêt à déployer !** 🚀
