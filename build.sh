#!/bin/bash
set -e

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🌐 Installing Chromium via pyppeteer..."
pyppeteer-install

echo "🔐 Setting executable permissions on Chromium..."
CHROMIUM_DIR="/opt/render/.local/share/pyppeteer/local-chromium"
if [ -d "$CHROMIUM_DIR" ]; then
    chmod -R +x "$CHROMIUM_DIR"
    echo "✅ Permissions set successfully"
else
    echo "⚠️  Warning: Chromium directory not found at $CHROMIUM_DIR"
fi

echo "✨ Build completed successfully!"
