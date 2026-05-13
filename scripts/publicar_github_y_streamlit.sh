#!/usr/bin/env bash
# Publica el proyecto en GitHub y deja listo el siguiente paso en Streamlit Community Cloud.
set -euo pipefail

REPO_NAME="${1:-pei-uccuyo-streamlit}"
VISIBILITY="${2:-public}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "Instalá GitHub CLI: brew install gh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "=== Primero autenticate en GitHub ==="
  echo "Ejecutá en esta terminal:  gh auth login -h github.com"
  echo "Elegí HTTPS o SSH según uses, y completá el login en el navegador."
  exit 1
fi

if [[ ! -d .git ]]; then
  if ! git init; then
    echo "ERROR: no se pudo crear .git en esta carpeta (OneDrive u otra sync suele bloquearlo)."
    echo "Copiá el proyecto a una carpeta LOCAL (ej. ~/Developer/pei-uccuyo-streamlit) y volvé a ejecutar:"
    echo "  ./scripts/publicar_github_y_streamlit.sh $REPO_NAME $VISIBILITY"
    echo "Guía: docs/DEPLOY_GITHUB_STREAMLIT.md"
    exit 1
  fi
  git branch -M main
fi

if [[ -z "$(git config --get user.name 2>/dev/null || true)" ]]; then
  git config user.name "Claudio Larrea"
  git config user.email "claudiomlarrea@users.noreply.github.com"
fi

git add -A
if git diff --cached --quiet; then
  echo "No hay cambios nuevos para commitear."
else
  git commit -m "PEI UCCuyo: app Streamlit, ingesta, informes y docs"
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote origin ya existe. Haciendo push..."
  git push -u origin main
else
  echo "Creando repo GitHub: $REPO_NAME ($VISIBILITY) y push..."
  gh repo create "$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push
fi

echo ""
echo "=== GitHub listo ==="
echo "Repo: https://github.com/$(gh api user -q .login)/$REPO_NAME"
echo ""
echo "=== Streamlit Community Cloud (lo hacés una vez en el navegador) ==="
echo "1. Abrí https://share.streamlit.io/ e iniciá sesión con GitHub."
echo "2. New app → elegí el repo $REPO_NAME, rama main, archivo principal: app.py"
echo "3. Deploy. Te dará una URL pública tipo https://<nombre>.streamlit.app"
echo "4. Si usás Google Sheets: en la app → Settings → Secrets, pegá el contenido"
echo "   basado en .streamlit/secrets.toml.example (sin commitear secretos reales)."
echo ""
echo "Importante: no subas Excel con datos personales; usá data/ vacío o muestras anonimizadas."
