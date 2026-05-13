# Publicar en GitHub + Streamlit Community Cloud

No subas datos personales: el `.gitignore` excluye `data/*.xlsx`, exportes y `secrets.toml`. Revisá `git status` antes del primer push.

## Problema frecuente: Git dentro de OneDrive

Si al hacer `git init` ves **Operation not permitted**, mové o cloná el proyecto a una carpeta **fuera de OneDrive**, por ejemplo:

```bash
cp -R "/Users/claudiolarrea/Library/CloudStorage/OneDrive-Personal/16 Secretaría de Investigación/68 Sistema de Gestión del PEI" \
      "$HOME/Developer/pei-uccuyo-streamlit"
cd "$HOME/Developer/pei-uccuyo-streamlit"
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

Trabajá desde `~/Developer/pei-uccuyo-streamlit` para Git y Streamlit Cloud.

## 1) GitHub CLI (`gh`)

```bash
brew install gh   # si no lo tenés
gh auth login -h github.com
```

Completá el login en el navegador hasta que `gh auth status` diga que estás logueado.

## 2) Crear repo y subir código

Desde la raíz del proyecto (donde está `app.py`):

```bash
chmod +x scripts/publicar_github_y_streamlit.sh
./scripts/publicar_github_y_streamlit.sh pei-uccuyo-streamlit public
```

El primer argumento es el nombre del repo en GitHub; el segundo `public` o `private`.

Si preferís manual:

```bash
git init
git branch -M main
git add -A
git commit -m "PEI UCCuyo: Streamlit"
gh repo create pei-uccuyo-streamlit --public --source=. --remote=origin --push
```

## 3) Streamlit Community Cloud

1. Entrá a [https://share.streamlit.io/](https://share.streamlit.io/) e iniciá sesión con GitHub.
2. **Create app** → elegí el repositorio, rama **main**, archivo principal **`app.py`**.
3. **Deploy**. La URL será del estilo `https://<nombre>.streamlit.app`.

### Páginas extra (`pages/`)

Streamlit detecta automáticamente la carpeta `pages/`; no hace falta configurar nada más.

### Python en la nube

En el asistente de deploy elegí **Python 3.11** (recomendado para alinear con dependencias).

### Google Sheets (opcional)

En la app en la nube: **Settings → Secrets** y pegá el TOML basado en `.streamlit/secrets.toml.example` (credenciales de cuenta de servicio con lectura a la hoja). Nunca commitees `secrets.toml`.

## 4) Probar

Tras el deploy, abrí la URL pública. Si falla el build, revisá los **logs** en Streamlit Cloud (suele ser un paquete faltante en `requirements.txt`).
