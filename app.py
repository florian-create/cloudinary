"""
API Flask pour générer des screenshots avec flèche et upload Cloudinary
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
    'arrow': {
        'enabled': True,
        'startX': 85,
        'startY': 50,
        'endX': 60,
        'endY': 30,
        'color': '#FF0000',
        'width': 20
    },
    'circle': {
        'enabled': True,
        'x': 60,
        'y': 30,
        'radius': 80,
        'color': '#FF0000',
        'borderWidth': 12
    }
}

def sanitize_domain(domain):
    """Normalise un domaine en nom de fichier valide"""
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    domain = re.sub(r'/$', '', domain)
    domain = re.sub(r'[^a-z0-9]', '-', domain, flags=re.IGNORECASE)
    return domain.lower()

def generate_arrow_svg(width, height):
    """Génère le SVG de la flèche et du cercle"""
    startX = (CONFIG['arrow']['startX'] / 100) * width
    startY = (CONFIG['arrow']['startY'] / 100) * height
    endX = (CONFIG['arrow']['endX'] / 100) * width
    endY = (CONFIG['arrow']['endY'] / 100) * height

    import math
    angle = math.atan2(endY - startY, endX - startX)
    arrowHeadLength = 60

    arrowPoint1X = endX - arrowHeadLength * math.cos(angle - math.pi / 6)
    arrowPoint1Y = endY - arrowHeadLength * math.sin(angle - math.pi / 6)
    arrowPoint2X = endX - arrowHeadLength * math.cos(angle + math.pi / 6)
    arrowPoint2Y = endY - arrowHeadLength * math.sin(angle + math.pi / 6)

    circleX = (CONFIG['circle']['x'] / 100) * width
    circleY = (CONFIG['circle']['y'] / 100) * height

    return f"""
    <svg width="{width}" height="{height}" style="position: absolute; top: 0; left: 0; pointer-events: none; z-index: 9999;">
      <defs>
        <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.5"/>
        </filter>
      </defs>
      <line
        x1="{startX}" y1="{startY}"
        x2="{endX}" y2="{endY}"
        stroke="{CONFIG['arrow']['color']}"
        stroke-width="{CONFIG['arrow']['width']}"
        filter="url(#shadow)"
        stroke-linecap="round"
      />
      <polygon
        points="{endX},{endY} {arrowPoint1X},{arrowPoint1Y} {arrowPoint2X},{arrowPoint2Y}"
        fill="{CONFIG['arrow']['color']}"
        filter="url(#shadow)"
      />
      <circle
        cx="{circleX}" cy="{circleY}"
        r="{CONFIG['circle']['radius']}"
        fill="none"
        stroke="{CONFIG['circle']['color']}"
        stroke-width="{CONFIG['circle']['borderWidth']}"
        filter="url(#shadow)"
      />
      <circle
        cx="{circleX}" cy="{circleY}"
        r="{CONFIG['circle']['radius'] - 10}"
        fill="none"
        stroke="{CONFIG['circle']['color']}"
        stroke-width="2"
        opacity="0.5"
      />
    </svg>
    """

async def capture_screenshot(url):
    """Capture un screenshot avec flèche"""
    browser = None

    try:
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

        # Navigation
        await page.goto(url, {
            'waitUntil': 'networkidle2',
            'timeout': 15000
        })

        # CSS pour masquer cookies/ads
        await page.addStyleTag({
            'content': """
                [class*="cookie" i],
                [id*="cookie" i],
                [class*="gdpr" i],
                [class*="consent" i],
                [class*="ad-" i],
                [class*="banner" i]:not([class*="hero" i]) {
                    display: none !important;
                    visibility: hidden !important;
                }
            """
        })

        await asyncio.sleep(0.5)

        # Injecter la flèche
        svg = generate_arrow_svg(CONFIG['width'], CONFIG['height'])
        await page.evaluate(f"""
            (svgContent) => {{
                const div = document.createElement('div');
                div.innerHTML = svgContent;
                div.style.position = 'fixed';
                div.style.top = '0';
                div.style.left = '0';
                div.style.width = '100%';
                div.style.height = '100%';
                div.style.pointerEvents = 'none';
                div.style.zIndex = '99999';
                document.body.appendChild(div);
            }}
        """, svg)

        await asyncio.sleep(0.2)

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
        'service': 'Screenshot API with Arrow',
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
        url = request.args.get('url')

        if not url:
            return jsonify({
                'error': 'Missing required parameter',
                'message': 'The "url" parameter is required',
                'example': '/api/generate?url=https://example.com'
            }), 400

        # Valider l'URL
        if not re.match(r'^https?://', url):
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', url):
                return jsonify({
                    'error': 'Invalid URL',
                    'message': 'URL must be a valid domain or full URL'
                }), 400

        print(f"[API] Processing: {url}")

        # Générer le screenshot (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        screenshot_path = loop.run_until_complete(capture_screenshot(url))

        print(f"[API] Screenshot captured: {screenshot_path}")

        # Upload vers Cloudinary
        cloudinary_url = upload_to_cloudinary(screenshot_path, url)

        print(f"[API] Uploaded to Cloudinary: {cloudinary_url}")

        # Retourner l'URL
        return jsonify({
            'success': True,
            'url': url,
            'screenshot_url': cloudinary_url,
            'message': 'Screenshot generated and uploaded successfully'
        }), 200

    except Exception as e:
        print(f"[API] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Screenshot generation failed',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
