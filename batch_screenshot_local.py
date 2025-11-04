"""
Script local pour générer des screenshots en masse
Parallélisé + Upload Cloudinary direct + Cache
"""

import asyncio
import cloudinary
import cloudinary.uploader
import cloudinary.api
from pyppeteer import launch
import tempfile
import os
import re
import csv
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time
import psutil  # Pour monitoring CPU/RAM

# Configuration Cloudinary
cloudinary.config(
    cloud_name='dqfnvegv2',
    api_key='563415363382115',
    api_secret='59NwZ6QGma6WHJkYCKmisMG73Lg'
)

# Configuration optimisée pour MacBook Air M1
CONFIG = {
    'width': 1200,
    'height': 800,
    'format': 'jpeg',
    'quality': 80,
    'wait_after_load': 1.5,
    'navigation_timeout': 20000,
    'network_idle_timeout': 4000,
    'concurrent_workers': 6,  # OPTIMISÉ pour MacBook Air M1 (6 workers = doux)
    'max_retries': 2,
    'batch_delay': 0.5  # Délai entre chaque worker (évite les pics)
}

def sanitize_domain(domain):
    """Normalise un domaine en nom de fichier valide"""
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    domain = re.sub(r'/$', '', domain)
    domain = re.sub(r'[^a-z0-9]', '-', domain, flags=re.IGNORECASE)
    return domain.lower()

def check_screenshot_exists(url):
    """Vérifie si un screenshot existe déjà sur Cloudinary (CACHE)"""
    try:
        filename = sanitize_domain(url)
        public_id = f'screenshots/{filename}'
        result = cloudinary.api.resource(public_id, resource_type='image')
        return result['secure_url']
    except:
        return None

def check_system_health():
    """Vérifie la santé du système (CPU/RAM/Température)"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()

    # Warning si CPU > 80% ou RAM > 85%
    if cpu_percent > 80:
        print(f"⚠️  CPU usage high: {cpu_percent}% - Consider reducing workers")
    if memory.percent > 85:
        print(f"⚠️  RAM usage high: {memory.percent}% - Consider reducing workers")

    return {
        'cpu_percent': cpu_percent,
        'ram_percent': memory.percent,
        'ram_available_gb': memory.available / (1024**3)
    }

async def capture_screenshot(url, semaphore):
    """Capture un screenshot avec contrôle de concurrence"""
    # Petit délai pour éviter les pics de démarrage
    await asyncio.sleep(CONFIG.get('batch_delay', 0))

    async with semaphore:
        browser = None
        try:
            # Normaliser l'URL
            if not url.startswith('http'):
                url = 'https://' + url

            print(f"📸 Capturing: {url}")

            # Lancer le navigateur
            browser = await launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions'
                ]
            )

            page = await browser.newPage()
            await page.setViewport({
                'width': CONFIG['width'],
                'height': CONFIG['height']
            })

            # Navigation
            try:
                await page.goto(url, {
                    'waitUntil': 'domcontentloaded',
                    'timeout': CONFIG['navigation_timeout']
                })
            except Exception as e:
                print(f"⚠️  Navigation warning: {str(e)[:50]}")

            # Attendre stabilisation
            await asyncio.sleep(CONFIG['wait_after_load'])

            # Screenshot
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpeg')
            await page.screenshot({
                'path': temp_file.name,
                'type': CONFIG['format'],
                'quality': CONFIG['quality'],
                'fullPage': False
            })

            await browser.close()

            # Upload Cloudinary
            filename = sanitize_domain(url)
            result = cloudinary.uploader.upload(
                temp_file.name,
                folder='screenshots',
                public_id=filename,
                overwrite=True,
                resource_type='image'
            )

            # Cleanup
            os.unlink(temp_file.name)

            print(f"✅ Success: {url} → {result['secure_url']}")
            return {
                'url': url,
                'screenshot_url': result['secure_url'],
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            print(f"❌ Error: {url} - {str(e)[:100]}")
            return {
                'url': url,
                'screenshot_url': None,
                'status': 'error',
                'error': str(e)[:200],
                'timestamp': datetime.now().isoformat()
            }

async def process_batch(urls, output_csv='results.csv'):
    """Traite un batch d'URLs en parallèle"""
    # Créer un sémaphore pour limiter la concurrence
    semaphore = asyncio.Semaphore(CONFIG['concurrent_workers'])

    results = []
    total = len(urls)
    processed = 0
    cached = 0
    success = 0
    errors = 0

    print(f"\n🚀 Starting batch processing of {total} URLs")
    print(f"⚙️  Concurrent workers: {CONFIG['concurrent_workers']}")
    print(f"📁 Output file: {output_csv}\n")

    start_time = time.time()

    # Vérifier le cache d'abord (rapide)
    print("🔍 Checking cache...")
    tasks_to_run = []

    for url in urls:
        cached_url = check_screenshot_exists(url)
        if cached_url:
            print(f"⚡ Cache HIT: {url}")
            results.append({
                'url': url,
                'screenshot_url': cached_url,
                'status': 'cached',
                'timestamp': datetime.now().isoformat()
            })
            cached += 1
            processed += 1
        else:
            tasks_to_run.append(url)

    print(f"\n📊 Cache results: {cached}/{total} already exist")
    print(f"🎯 Will generate: {len(tasks_to_run)} new screenshots\n")

    # Traiter les URLs qui ne sont pas en cache
    if tasks_to_run:
        tasks = [capture_screenshot(url, semaphore) for url in tasks_to_run]

        # Exécuter avec progress tracking
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            processed += 1

            if result['status'] == 'success':
                success += 1
            elif result['status'] == 'error':
                errors += 1

            # Progress avec monitoring système (toutes les 10 URLs)
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total - processed) / rate if rate > 0 else 0

            # Check système toutes les 10 URLs
            health_info = ""
            if processed % 10 == 0:
                health = check_system_health()
                health_info = f" | 💻 CPU: {health['cpu_percent']:.0f}% | 🧠 RAM: {health['ram_percent']:.0f}%"

            print(f"📊 Progress: {processed}/{total} ({processed/total*100:.1f}%) | "
                  f"✅ {success + cached} | ❌ {errors} | "
                  f"⏱️  {rate:.1f}/s | ETA: {eta/60:.1f}min{health_info}")

    # Sauvegarder les résultats
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'screenshot_url', 'status', 'error', 'timestamp'])
        writer.writeheader()
        writer.writerows(results)

    # Résumé final
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✨ Batch processing completed!")
    print(f"{'='*60}")
    print(f"📊 Total: {total}")
    print(f"⚡ Cached: {cached}")
    print(f"✅ Success: {success}")
    print(f"❌ Errors: {errors}")
    print(f"⏱️  Time: {elapsed/60:.1f} minutes")
    print(f"🚀 Rate: {total/elapsed:.1f} URLs/second")
    print(f"📁 Results saved to: {output_csv}")
    print(f"{'='*60}\n")

    return results

def load_urls_from_csv(csv_path, url_column='website'):
    """Charge les URLs depuis un CSV"""
    urls = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get(url_column, '').strip()
            if url:
                urls.append(url)
    return urls

# Usage
if __name__ == '__main__':
    # OPTION 1 : Charger depuis un CSV
    # urls = load_urls_from_csv('companies.csv', url_column='website')

    # OPTION 2 : Liste manuelle pour tester
    urls = [
        'https://www.google.com',
        'https://www.github.com',
        'https://www.stackoverflow.com',
        'https://www.reddit.com',
        'https://www.wikipedia.org'
    ]

    # Lancer le traitement
    asyncio.run(process_batch(urls, output_csv='screenshot_results.csv'))
