"""
API Flask pour générer des screenshots et upload Cloudinary
Déployable sur Render
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
import asyncio
from pyppeteer import launch
import tempfile
import os
import re

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
    'wait_after_load': 3,  # Secondes d'attente après le chargement initial
    'navigation_timeout': 20000  # Timeout navigation en ms
}

def sanitize_domain(domain):
    """Normalise un domaine en nom de fichier valide"""
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    domain = re.sub(r'/$', '', domain)
    domain = re.sub(r'[^a-z0-9]', '-', domain, flags=re.IGNORECASE)
    return domain.lower()

async def capture_screenshot(url, wait_time=None):
    """Capture un screenshot du site"""
    browser = None

    try:
        # Utiliser le wait_time fourni ou celui par défaut
        if wait_time is None:
            wait_time = CONFIG['wait_after_load']

        # Normaliser l'URL
        if not url.startswith('http'):
            url = 'https://' + url

        # Lancer le navigateur
        browser = await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )

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
                    'timeout': 5000  # Max 5 secondes supplémentaires
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

        # Vérifier que les images sont chargées
        try:
            await page.evaluate("""
                () => {
                    return Promise.all(
                        Array.from(document.images)
                            .filter(img => !img.complete)
                            .map(img => new Promise(resolve => {
                                img.onload = img.onerror = resolve;
                            }))
                    );
                }
            """)
            print(f"[API] All images loaded")
        except:
            print(f"[API] Some images may not be loaded, continuing anyway")
            pass

        # Petit délai supplémentaire pour les polices et animations CSS
        await asyncio.sleep(0.5)

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

        # Attendre que les suppressions prennent effet
        await asyncio.sleep(0.5)

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
            await browser.close()
        raise e

def upload_to_cloudinary(file_path, domain):
    """Upload vers Cloudinary"""
    filename = sanitize_domain(domain)

    result = cloudinary.uploader.upload(
        file_path,
        folder='screenshots',
        public_id=filename,
        overwrite=True,
        resource_type='image'
    )

    # Supprimer le fichier temporaire
    os.unlink(file_path)

    return result['secure_url']

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

        # Générer le screenshot (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        screenshot_path = loop.run_until_complete(capture_screenshot(url, wait_time))

        print(f"[API] Screenshot captured")

        # Upload vers Cloudinary
        cloudinary_url = upload_to_cloudinary(screenshot_path, url)

        print(f"[API] Uploaded to Cloudinary")

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
    Version ultra-minimaliste : retourne UNIQUEMENT l'URL du screenshot en texte brut
    Idéal pour Clay si le JSON pose problème
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

        # Récupérer le paramètre wait optionnel
        wait_time = request.args.get('wait', type=int)
        if wait_time and (wait_time < 0 or wait_time > 10):
            return 'ERROR: Wait parameter must be between 0 and 10 seconds', 400

        # Générer le screenshot
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        screenshot_path = loop.run_until_complete(capture_screenshot(url, wait_time))

        # Upload vers Cloudinary
        cloudinary_url = upload_to_cloudinary(screenshot_path, url)

        # Retourner UNIQUEMENT l'URL en texte brut (pas de JSON)
        return cloudinary_url, 200

    except Exception as e:
        error_msg = str(e)[:100]
        return f'ERROR: {error_msg}', 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
