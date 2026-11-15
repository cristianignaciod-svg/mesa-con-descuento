# Mesa con Descuento

Descuentos en restaurantes, cafés y bares con tarjetas de bancos chilenos, filtrables por región, ciudad, banco y día.

- `index.html`: la página (sin servidor ni base de datos).
- `datos.json`: todos los descuentos, `{meta, ciudades:[{ciudad, region, actualizado, items:[...]}]}`.

Los datos se actualizan los días 2 y 15 de cada mes revisando los sitios de Banco de Chile, BCI, Santander, Scotiabank, Banco Falabella, Security, Ripley, Itaú, BICE y BancoEstado. Cada actualización es un commit a `datos.json`, y Netlify publica la nueva versión automáticamente.

## Actualización automática

GitHub Actions (`.github/workflows/actualizar.yml`) corre los días 2 y 15:

1. `scraper/extraer.py` abre cada sitio con Chrome (Playwright) y guarda los datos crudos.
2. `scraper/construir.py` los convierte en descuentos por ciudad y reescribe `datos.json`. Si un banco falla o trae menos de la mitad de los descuentos que antes, se conservan sus descuentos anteriores vigentes y la página lo indica.
3. `scraper/reporte.json` resume cuántos descuentos trajo cada banco.

Para correrlo a mano: pestaña **Actions → Actualizar descuentos → Run workflow**.
