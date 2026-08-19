# Experiencia WebAR · Logo Mineral de la Reforma

Prototipo estático para abrir desde un QR, mostrar el logotipo como modelo 3D animado y permitir colocarlo en realidad aumentada desde un teléfono compatible.

## Contenido

- `index.html` — aplicación WebAR.
- `assets/logo_mr_3d.glb` — modelo 3D con animación `Giro360` embebida.
- `assets/logo_transparente.png` — poster / icono.
- `assets/logo_original.png` — imagen fuente suministrada.
- `generar_qr.py` — genera el QR después de conocer la URL pública.
- `build_logo.py` — script utilizado para reconstruir el GLB a partir del PNG.

## Despliegue

Es una aplicación **100% estática**. Puedes servir la carpeta con Nginx, Apache, GitHub Pages, Cloudflare Pages, Netlify, Vercel o cualquier hosting de archivos estáticos.

Ejemplo con Nginx:

```nginx
server {
    listen 80;
    server_name ar.tudominio.mx;
    root /var/www/mr-ar-logo;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Para producción configura HTTPS. Las funciones de cámara/WebXR de los navegadores se consideran funciones de contexto seguro y la experiencia AR móvil debe probarse desde la URL HTTPS definitiva.

## Prueba local

No abras `index.html` directamente con `file://`, porque el navegador puede bloquear recursos. Sirve la carpeta con un servidor local:

```bash
cd mr_ar_logo
python -m http.server 8080
```

En la computadora abre:

```text
http://localhost:8080
```

Para probar AR desde el teléfono, despliega primero en una URL HTTPS accesible desde el móvil.

## Generar el QR

Una vez desplegado, ejecuta:

```bash
python generar_qr.py "https://ar.tudominio.mx/"
```

Se creará:

```text
qr_experiencia_ar.png
```

Ese es el QR que puedes colocar en una lona, tarjeta, invitación o pieza impresa.

## Flujo para el usuario

1. Escanea el QR.
2. Se abre la página y el logo comienza a girar en 3D.
3. Toca **Ver en realidad aumentada**.
4. El teléfono abre el modo AR disponible.
5. Detecta una superficie y coloca el modelo.

## Compatibilidad

La página usa `<model-viewer>` con los modos `webxr`, `scene-viewer` y `quick-look`. El archivo fuente es GLB. En iOS, `<model-viewer>` puede generar el USDZ necesario para Quick Look a partir del modelo.

Documentación oficial:

- https://modelviewer.dev/
- https://modelviewer.dev/examples/augmentedreality/
- https://modelviewer.dev/docs/faq.html

## Personalización rápida

En `index.html` puedes cambiar:

- nombre y textos de la experiencia;
- colores CSS (`--vino`, `--dorado`, etc.);
- velocidad del giro: está embebida en el GLB a 12 segundos por vuelta;
- tamaño inicial modificando `camera-orbit`;
- escala en AR con `ar-scale`.

Si modificas el logo original, vuelve a generar el GLB con:

```bash
python build_logo.py
```

## Nota sobre el QR y el modo AR

El QR abre la experiencia. Por políticas de permisos del navegador, el acceso a AR/cámara normalmente requiere una interacción del usuario; por eso se presenta un botón grande de **Ver en realidad aumentada** en lugar de intentar abrir la cámara automáticamente.
