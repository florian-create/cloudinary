"""
API Flask pour générer des screenshots et upload Cloudinary
Déployable sur Render
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
import cloudinary.api
import asyncio
from pyppeteer import launch
import tempfile
import os
import re
import hashlib

app = Flask(__name__)
CORS(app)

# Configuration Cloudinary
cloudinary.config(
    cloud_name='dqfnvegv2',
    api_key='563415363382115',
    api_secret='59NwZ6QGma6WHJkYCKmisMG73Lg'
)

# Configuration
CONFIG = {
    'width': 1200,
    'height': 800,
    'format': 'jpeg',
    'quality': 85,
    'wait_after_load': 1.5,  # Réduit à 1.5s pour Clay
    'navigation_timeout': 12000,  # Réduit à 12s
    'network_idle_timeout': 2000,  # Réduit à 2s
    'image_load_timeout': 4000,  # Réduit à 4s
    'global_timeout': 45  # Timeout global en secondes (pour Clay < 60s)
}

def sanitize_domain(domain):
    """Normalise un domaine en nom de fichier valide"""
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    domain = re.sub(r'/$', '', domain)
    domain = re.sub(r'[^a-z0-9]', '-', domain, flags=re.IGNORECASE)
    return domain.lower()

def get_url_hash(url):
    """Génère un hash court pour l'URL (pour le cache)"""
    normalized = url.lower().strip().rstrip('/')
    return hashlib.md5(normalized.encode()).hexdigest()[:12]

def check_screenshot_exists(url):
    """Vérifie si un screenshot existe déjà sur Cloudinary"""
    try:
        filename = sanitize_domain(url)
        public_id = f'screenshots/{filename}'

        # Essayer de récupérer l'info de l'image
        result = cloudinary.api.resource(public_id, resource_type='image')

        # Si on arrive ici, l'image existe
        return result['secure_url']
    except cloudinary.exceptions.NotFound:
        # L'image n'existe pas
        return None
    except Exception as e:
        print(f"[API] Error checking Cloudinary cache: {e}")
        return None

async def capture_screenshot_internal(url, wait_time=None):
    """Capture un screenshot du site (fonction interne sans timeout)"""
    browser = None

    try:
        # Utiliser le wait_time fourni ou celui par défaut
        if wait_time is None:
            wait_time = CONFIG['wait_after_load']

        # Normaliser l'URL
        if not url.startswith('http'):
            url = 'https://' + url

        print(f"[API] Launching browser for {url}...")

        # Lancer le navigateur avec options d'optimisation mémoire et stabilité
        browser = await launch(
            headless=True,
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-sync',
                '--metrics-recording-only',
                '--mute-audio',
                '--no-first-run',
                '--safebrowsing-disable-auto-update',
                '--disable-notifications',
                '--disable-crash-reporter',
                '--disable-in-process-stack-traces',
                '--disable-logging',
                '--log-level=3',
                '--single-process'
            ]
        )

        print(f"[API] Browser launched successfully")

        page = await browser.newPage()

        # Configuration viewport
        await page.setViewport({
            'width': CONFIG['width'],
            'height': CONFIG['height']
        })

        # User agent
        await page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        )

        # Navigation avec timeout et gestion d'erreur
        try:
            # D'abord attendre que le DOM soit chargé
            await page.goto(url, {
                'waitUntil': 'domcontentloaded',
                'timeout': CONFIG['navigation_timeout']
            })
            print(f"[API] DOM loaded")

            # Puis attendre que les ressources se chargent (images, CSS, fonts)
            # On utilise networkidle0 avec un timeout court pour éviter d'attendre trop longtemps
            try:
                await page.waitForNavigation({
                    'waitUntil': 'networkidle0',  # Attendre que le réseau soit idle
                    'timeout': CONFIG['network_idle_timeout']
                })
                print(f"[API] Network idle reached")
            except:
                # Si timeout, pas grave, on continue
                print(f"[API] Network didn't idle, continuing anyway")
                pass

        except Exception as nav_error:
            # Si timeout ou erreur de navigation, continuer quand même
            print(f"[API] Navigation warning: {str(nav_error)[:100]}")

        # Attendre que la page se stabilise complètement (images, animations, etc.)
        print(f"[API] Waiting {wait_time}s for page to fully render...")
        await asyncio.sleep(wait_time)

        # Vérifier que les images sont chargées (avec timeout)
        try:
            await asyncio.wait_for(
                page.evaluate("""
                    () => {
                        return Promise.all(
                            Array.from(document.images)
                                .filter(img => !img.complete)
                                .map(img => new Promise(resolve => {
                                    img.onload = img.onerror = resolve;
                                }))
                        );
                    }
                """),
                timeout=CONFIG['image_load_timeout'] / 1000  # Convertir ms en secondes
            )
            print(f"[API] All images loaded")
        except asyncio.TimeoutError:
            print(f"[API] Image loading timeout, continuing anyway")
        except Exception as e:
            print(f"[API] Some images may not be loaded, continuing anyway")
            pass

        # Petit délai supplémentaire pour les polices et animations CSS (réduit à 0.2s)
        await asyncio.sleep(0.2)

        # CSS pour masquer cookies/popups/ads - Liste exhaustive
        await page.addStyleTag({
            'content': """
                /* Cookies et GDPR */
                [class*="cookie" i],
                [id*="cookie" i],
                [class*="gdpr" i],
                [id*="gdpr" i],
                [class*="consent" i],
                [id*="consent" i],
                [class*="privacy" i]:not(a):not(span),
                [id*="privacy" i]:not(a):not(span),

                /* Popups et modals */
                [class*="popup" i],
                [id*="popup" i],
                [class*="modal" i]:not([class*="mode" i]),
                [id*="modal" i],
                [class*="overlay" i],
                [id*="overlay" i],

                /* Banners */
                [class*="banner" i]:not([class*="hero" i]):not([class*="slider" i]),
                [id*="banner" i]:not([id*="hero" i]),

                /* Publicités */
                [class*="ad-" i],
                [class*="ads" i],
                [id*="ad-" i],

                /* Newsletter */
                [class*="newsletter" i][class*="popup" i],
                [id*="newsletter" i][id*="popup" i],

                /* Common cookie tools */
                #onetrust-consent-sdk,
                #cookieConsentContainer,
                #gdpr-cookie-message,
                .cc-window,
                .cc-banner,
                .cookie-consent,
                .cookie-notice,
                .cookie-bar,
                div[class*="CookieBanner"],
                div[class*="cookieBanner"],
                div[id*="CookieBanner"],

                /* Tarteaucitron */
                #tarteaucitronRoot,
                #tarteaucitronAlertBig,

                /* Axeptio */
                #axeptio_overlay,
                #axeptio_main_container,

                /* Didomi */
                #didomi-host,
                .didomi-popup-container {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                }

                /* Empêcher le scroll lock */
                body {
                    overflow: auto !important;
                }
            """
        })

        # Supprimer les éléments de cookies via JavaScript
        await page.evaluate("""
            () => {
                // Supprimer les overlays et backdrops
                const selectors = [
                    '[class*="cookie"]',
                    '[id*="cookie"]',
                    '[class*="consent"]',
                    '[id*="consent"]',
                    '[class*="gdpr"]',
                    '[id*="gdpr"]',
                    '#onetrust-consent-sdk',
                    '.cc-window',
                    '#tarteaucitronRoot',
                    '#axeptio_overlay',
                    '#didomi-host'
                ];

                selectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => el.remove());
                });

                // Retirer le scroll lock
                document.body.style.overflow = 'auto';
                document.documentElement.style.overflow = 'auto';
            }
        """)

        # Attendre que les suppressions prennent effet (minimal)
        await asyncio.sleep(0.1)

        # Capturer le screenshot dans un fichier temporaire
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpeg')
        await page.screenshot({
            'path': temp_file.name,
            'type': CONFIG['format'],
            'quality': CONFIG['quality'],
            'fullPage': False
        })

        await browser.close()

        return temp_file.name

    except Exception as e:
        if browser:
            try:
                await browser.close()
            except:
                pass
        raise e

async def capture_screenshot(url, wait_time=None, retry=0):
    """Capture un screenshot avec timeout global optimisé pour Clay et retry"""
    max_retries = 2

    try:
        # Timeout global de 45 secondes pour Clay (qui a ~60s de timeout)
        screenshot_path = await asyncio.wait_for(
            capture_screenshot_internal(url, wait_time),
            timeout=CONFIG['global_timeout']
        )
        return screenshot_path
    except asyncio.TimeoutError:
        print(f"[API] Screenshot timeout after {CONFIG['global_timeout']}s for {url}")
        raise Exception(f"Screenshot generation timeout after {CONFIG['global_timeout']} seconds")
    except Exception as e:
        error_msg = str(e)
        print(f"[API] Screenshot error (attempt {retry + 1}/{max_retries + 1}): {error_msg[:200]}")

        # Retry si "Browser closed unexpectedly" et retry disponibles
        if "Browser closed" in error_msg and retry < max_retries:
            print(f"[API] Retrying screenshot generation (attempt {retry + 2}/{max_retries + 1})...")
            await asyncio.sleep(1)  # Petit délai avant retry
            return await capture_screenshot(url, wait_time, retry + 1)

        raise

def upload_to_cloudinary(file_path, domain):
    """Upload vers Cloudinary avec gestion d'erreur améliorée"""
    filename = sanitize_domain(domain)

    try:
        result = cloudinary.uploader.upload(
            file_path,
            folder='screenshots',
            public_id=filename,
            overwrite=True,
            resource_type='image'
        )
        return result['secure_url']
    finally:
        # Toujours supprimer le fichier temporaire, même en cas d'erreur
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"[API] Warning: Could not delete temp file {file_path}: {e}")

@app.route('/')
def index():
    """Page d'accueil"""
    return jsonify({
        'service': 'Screenshot API',
        'version': '1.0.0',
        'endpoints': {
            'generate': '/api/generate?url=https://example.com'
        }
    })

@app.route('/api/generate', methods=['GET'])
def generate_screenshot():
    """
    Endpoint principal : génère screenshot + upload Cloudinary
    Query params: url (required)
    """
    try:
        # Récupérer l'URL
        url = request.args.get('url', '').strip()

        if not url:
            return jsonify({
                'error': 'Missing URL parameter'
            }), 400

        # Rejeter les messages d'erreur de Clay
        if 'exceeded' in url.lower() or 'error' in url.lower() or 'result' in url.lower():
            return jsonify({
                'error': 'Invalid URL: looks like an error message'
            }), 400

        # Valider l'URL
        if not re.match(r'^https?://', url):
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', url):
                return jsonify({
                    'error': 'Invalid URL format'
                }), 400

        # Récupérer le paramètre wait optionnel (délai d'attente en secondes)
        wait_time = request.args.get('wait', type=int)
        if wait_time and (wait_time < 0 or wait_time > 10):
            return jsonify({
                'error': 'Wait parameter must be between 0 and 10 seconds'
            }), 400

        print(f"[API] Processing: {url} (wait: {wait_time if wait_time else 'default'}s)")

        # Générer le screenshot (async) avec timeout
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            screenshot_path = loop.run_until_complete(capture_screenshot(url, wait_time))
            print(f"[API] Screenshot captured")

            # Upload vers Cloudinary
            cloudinary_url = upload_to_cloudinary(screenshot_path, url)
            print(f"[API] Uploaded to Cloudinary")
        finally:
            # Nettoyer l'event loop
            loop.close()

        # Retourner UNIQUEMENT l'URL du screenshot (format minimal pour Clay)
        return jsonify({
            'screenshot_url': cloudinary_url
        }), 200

    except Exception as e:
        # Limiter la taille du message d'erreur
        error_msg = str(e)[:200]  # Max 200 caractères
        print(f"[API] Error: {error_msg}")
        return jsonify({
            'error': error_msg
        }), 500

@app.route('/api/generate-url', methods=['GET'])
def generate_screenshot_url_only():
    """
    Version ultra-minimaliste avec cache : retourne UNIQUEMENT l'URL du screenshot en texte brut
    NOUVEAU : Vérifie d'abord si le screenshot existe sur Cloudinary (retour instantané)
    """
    try:
        url = request.args.get('url', '').strip()
        if not url:
            return 'ERROR: Missing URL parameter', 400

        # Rejeter les messages d'erreur de Clay
        if 'exceeded' in url.lower() or 'error' in url.lower() or 'result' in url.lower():
            return 'ERROR: Invalid URL (error message detected)', 400

        if not re.match(r'^https?://', url):
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', url):
                return 'ERROR: Invalid URL format', 400

        # NOUVEAU : Vérifier si le screenshot existe déjà (cache ultra-rapide)
        print(f"[API] Checking cache for: {url}")
        cached_url = check_screenshot_exists(url)
        if cached_url:
            print(f"[API] Cache HIT! Returning cached screenshot")
            return cached_url, 200

        print(f"[API] Cache MISS - Generating new screenshot")

        # Récupérer le paramètre wait optionnel
        wait_time = request.args.get('wait', type=int)
        if wait_time and (wait_time < 0 or wait_time > 10):
            return 'ERROR: Wait parameter must be between 0 and 10 seconds', 400

        # Générer le screenshot avec timeout optimisé
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            screenshot_path = loop.run_until_complete(capture_screenshot(url, wait_time))
            # Upload vers Cloudinary
            cloudinary_url = upload_to_cloudinary(screenshot_path, url)
            print(f"[API] Screenshot generated and uploaded successfully")
        finally:
            # Nettoyer l'event loop
            loop.close()

        # Retourner UNIQUEMENT l'URL en texte brut (pas de JSON)
        return cloudinary_url, 200

    except Exception as e:
        error_msg = str(e)[:100]
        print(f"[API] Error: {error_msg}")
        return f'ERROR: {error_msg}', 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
