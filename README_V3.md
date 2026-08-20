# Variante 3 · Reloj monumento mejorado

Este paquete conserva la variante original del logotipo y agrega una reconstrucción 3D mejorada del reloj monumento para realidad aumentada.

## Cambios principales

- Geometría estructural simétrica.
- Cuatro pilares de piedra con ligera conicidad.
- Cuatro caras de reloj.
- Dos niveles de barandales y plataformas.
- Cuerpo blanco con remates vino.
- Cubierta superior a cuatro aguas.
- Faroles simétricos en la base.
- Logotipo 3D original integrado al frente del monumento.
- Texto 3D flotante sobre la torre:
  - `2DO INFORME`
  - `2026`

## Archivos para usar

- `experiencia_ar.html` — página recomendada, permite cambiar entre logotipo y reloj.
- `reloj_ar.html` — abre directamente la nueva variante del reloj.
- `index.html` — conserva intacta la primera experiencia del logotipo.
- `assets/reloj_monumento_ar_v2.glb` — modelo 3D nuevo.
- `assets/logo_mr_3d.glb` — modelo 3D original.
- `assets/variantes/preview_reloj_v2.png` — vista conceptual del resultado.

## Prueba local

Desde esta carpeta:

```bash
py -m http.server 8000
```

Luego abre:

```text
http://localhost:8000/experiencia_ar.html
```

## Realidad aumentada

Para probar AR en un teléfono, lo ideal es alojar la carpeta por HTTPS y abrir `experiencia_ar.html` o `reloj_ar.html` desde el celular.

## Nota de fidelidad

El modelo se reconstruyó visualmente a partir de las dos fotografías de referencia disponibles. Es una aproximación 3D para una experiencia institucional/AR, no un levantamiento fotogramétrico ni arquitectónico exacto.
