# Paquete V7 · Reloj Monumento AR · inicio directo de cámara

Esta versión conserva el modelo refinado del reloj monumento y cambia el flujo de la experiencia para que el usuario llegue **directamente al intento de realidad aumentada**.

## Cambios principales respecto a V6

- Se corrigió la zona de los faroles/candelabros para que sus soportes se entiendan como parte del monumento y no como líneas u objetos flotantes.
- Se eliminaron las barras inferiores que se percibían desconectadas.
- Los faroles quedan montados sobre los pilares mediante brazos cortos y soportes diagonales.
- Se conservan el texto `2DO INFORME 2026`, los logotipos de las cuatro caras, la cubierta superior y el resto de la composición anterior.
- Se restauró la animación embebida `GiroLentoAR`, de 24 segundos por vuelta, para que el modelo siga girando lentamente cuando el visor AR lo permita.

## Flujo nuevo de `experiencia_ar.html`

Al abrir la página desde un teléfono:

1. Se solicita inmediatamente permiso de cámara.
2. En cuanto el permiso es concedido y el modelo está listo, la página intenta abrir AR automáticamente.
3. Si el navegador impide iniciar una sesión AR sin una interacción del usuario, aparece un único botón: **Abrir cámara y comenzar**.
4. Una vez dentro de AR, el usuario puede colocar, mover, rotar y escalar el reloj.

### Importante: restricción de seguridad del navegador

No existe una forma web universal de obligar a Chrome, Safari, WebXR, Scene Viewer o Quick Look a entrar en AR sin ninguna interacción. Algunos navegadores requieren un gesto del usuario para iniciar una sesión inmersiva, incluso si el permiso de cámara ya fue concedido.

Por eso esta V7 hace el máximo flujo automático permitido: **solicita la cámara al cargar y trata de abrir AR de inmediato**. Solo muestra el botón de un toque cuando el navegador lo exige.

## Archivos principales

- `index.html` → redirige inmediatamente a la experiencia AR. Útil si el QR apunta a la raíz del sitio.
- `experiencia_ar.html` → flujo directo: permiso de cámara + intento automático de AR.
- `reloj_ar.html` → alias de la misma experiencia directa para conservar compatibilidad con enlaces anteriores.
- `assets/reloj_monumento_ar_v7.glb` → modelo V7 con animación embebida `GiroLentoAR`.
- `assets/variantes/preview_reloj_v7.png` → vista previa.
- `tools/build_reloj_v7.py` → script de edición de V6 a V7 y restauración de la animación.

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

## Recomendación para el QR

Apunta el QR a la raíz de esta carpeta o directamente a:

```text
https://TU-DOMINIO/experiencia_ar.html
```

Así la persona no pasa por una pantalla de selección: entra directo al flujo de cámara.
