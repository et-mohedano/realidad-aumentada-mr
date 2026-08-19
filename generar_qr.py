"""Genera un PNG de QR apuntando a la URL pública de la experiencia.
Uso:
    python generar_qr.py https://tu-dominio.mx/ar/
"""
from pathlib import Path
import sys
import qrcode

if len(sys.argv) != 2:
    raise SystemExit('Uso: python generar_qr.py https://tu-dominio.mx/ar/')

url = sys.argv[1].strip()
if not url.startswith(('https://', 'http://')):
    raise SystemExit('La URL debe comenzar con https:// o http://')

qr = qrcode.QRCode(
    version=None,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=12,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image(fill_color='#5C1522', back_color='white').convert('RGB')
out = Path(__file__).resolve().parent / 'qr_experiencia_ar.png'
img.save(out, quality=95)
print(f'QR generado: {out}')
print(f'URL: {url}')
