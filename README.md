# Mesa con Descuento

Descuentos en restaurantes, cafés y bares con tarjetas de bancos chilenos, filtrables por región, ciudad, banco y día.

- `index.html`: la página (sin servidor ni base de datos).
- `datos.json`: todos los descuentos, `{meta, ciudades:[{ciudad, region, actualizado, items:[...]}]}`.

Los datos se actualizan los días 2 y 15 de cada mes revisando los sitios de Banco de Chile, BCI, Santander, Scotiabank, Banco Falabella, Security, Ripley, Itaú, BICE y BancoEstado. Cada actualización es un commit a `datos.json`, y Netlify publica la nueva versión automáticamente.
