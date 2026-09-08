# Desplegar `frontend/` como nuevo servicio en Railway

Este dashboard reemplaza a `dashboard/app.py` (Streamlit). El backend
FastAPI **no cambia** — este frontend solo consume `/triaje`, `/incidencias`
y `/chat` por HTTP, igual que hacía Streamlit.

## 1. Probar en local primero

```bash
cd frontend
npm install
npm run dev
```

Esto no se pudo verificar en el entorno donde se generó el código (sin
acceso a red para `npm install`), así que ejecuta esto antes de desplegar.

## 2. Diferencia importante frente a Streamlit: `API_URL` es de build-time

Streamlit leía `API_URL` con `os.getenv(...)` **en cada arranque del
proceso** (runtime). Una SPA compilada con Vite **no puede** hacer eso: la
variable `VITE_API_URL` se incrusta en el JS **al ejecutar `npm run
build`**, no al servir los archivos después.

Consecuencia práctica: en Railway, define `VITE_API_URL` en las variables
del nuevo servicio **antes** del primer deploy (Railway las expone también
durante el paso de build, así que basta con tenerla configurada). Si más
adelante cambias la URL del backend, hace falta un **rebuild** del
frontend — reiniciar el servicio no es suficiente, porque la URL ya quedó
"horneada" en el bundle de JS.

```
VITE_API_URL = https://backend-civicmind.up.railway.app
```

## 3. Crear el servicio en Railway

1. New Service → Deploy from GitHub repo → mismo repo
   (`yohperez/civicmind-urban-triage`), rama `main`.
2. Settings → Build:
   - **Watch Paths**: `frontend/**` (para que este servicio solo redeploye
     cuando cambie esta carpeta — el mismo problema de watch paths que tuvo
     el dashboard de Streamlit).
   - Build Command: `npm run build` (Railpack debería detectarlo solo al
     ver `package.json`, pero puedes forzarlo aquí si no lo hace).
3. Settings → Deploy:
   - Start Command: `npm run preview`
     (usa `vite preview --host 0.0.0.0 --port $PORT`, ya definido en
     `package.json`).
4. Settings → Variables: añade `VITE_API_URL` (ver punto 2).
5. Genera un dominio público para este servicio (Settings → Networking →
   Generate Domain), o usa un dominio custom.

## 4. Qué hacer con el servicio `dashboard` viejo

Cuando confirmes que el nuevo frontend funciona, puedes:
- Borrar el servicio `dashboard` (Streamlit) en Railway, o
- Dejarlo apagado como respaldo mientras migras.

`dashboard/app.py` y su entrada en `requirements.txt`/Procfile pueden
quedarse en el repo sin problema (el watch path de `backend` no lo toca),
pero si ya no lo vas a usar, bórralos en otro commit para no confundir.
