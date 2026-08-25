# Paquete V8 · Reloj Monumento AR · carátulas uniformes

Esta versión conserva el flujo directo de cámara/AR de V7 y hace un ajuste puntual en el modelo del reloj:
**las cuatro caras ahora usan la misma carátula y la misma forma de manecillas**, manteniendo el estilo circular en las 4.

## Cambios principales respecto a V7

- Se conservaron los faroles/candelabros corregidos y el resto de la geometría refinada.
- Se conservaron el texto `2DO INFORME 2026`, los logotipos de las cuatro caras, la cubierta superior y la animación `GiroLentoAR`.
- Se sustituyeron las piezas de las carátulas para que las **4 muestren el mismo diseño**.
- Se unificó la forma de las manecillas y los marcadores horarios en los cuatro lados.
- Se mantuvo la experiencia que pide la cámara al abrir y trata de iniciar AR de inmediato.

## Flujo de `experiencia_ar.html`

Al abrir la página desde un teléfono:

1. Se solicita inmediatamente permiso de cámara.
2. En cuanto el permiso es concedido y el modelo está listo, la página intenta abrir AR automáticamente.
3. Si el navegador impide iniciar una sesión AR sin una interacción del usuario, aparece un único botón: **Abrir cámara y comenzar**.
4. Una vez dentro de AR, el usuario puede colocar, mover, rotar y escalar el reloj.

## Archivos principales

- `index.html` → redirige inmediatamente a la experiencia AR.
- `experiencia_ar.html` → flujo directo: permiso de cámara + intento automático de AR.
- `reloj_ar.html` → alias de la misma experiencia directa.
- `assets/reloj_monumento_ar_v8.glb` → modelo V8 con las 4 carátulas uniformes y animación embebida `GiroLentoAR`.
- `assets/variantes/preview_reloj_v8.png` → vista previa.
- `tools/build_reloj_v8.py` → script de edición de V7 a V8.

## Publicación

La cámara requiere un contexto seguro. Para producción, publica toda la carpeta mediante **HTTPS**.

Para una prueba local en computadora:

```bash
py -m http.server 8000
```

Luego abre:

```text
http://localhost:8000/
```

Para probar la cámara/AR real, abre la URL HTTPS desde el teléfono.
