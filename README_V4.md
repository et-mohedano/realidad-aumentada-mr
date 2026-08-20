# Paquete V4 · Reloj AR mejorado

Esta versión ajusta específicamente la variante del reloj monumento:

- El texto flotante fue movido más arriba para separarlo del monumento.
- La parte superior del reloj fue corregida para verse más completa y simétrica.
- Se agregó una **animación embebida en el GLB** para que el reloj **gire lentamente también dentro de la cámara AR**.
- Se conserva la interacción manual: mover, rotar y escalar.

## Archivos principales

- `experiencia_ar.html` → selector entre logotipo y reloj.
- `reloj_ar.html` → abre directamente la variante del reloj.
- `assets/reloj_monumento_ar_v3.glb` → modelo actualizado con animación en AR.
- `tools/build_reloj_v4.py` → script de construcción del modelo V4.
