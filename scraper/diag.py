"""Diagnóstico: descarga las fuentes de cada banco desde el runner de GitHub y guarda lo recibido."""
import os, json, gzip, urllib.request, ssl, time
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SRC = {
 "bch_p1": "https://sitiospublicos.bancochile.cl/api/content/spaces/personas/types/beneficios/entries?page=1&per_page=100",
 "san": "https://banco.santander.cl/beneficios/promociones.json?per_page=9999&custom_fields=true",
 "sco": "https://www.scotiarewards.cl/scclubfront/categoria/platosycomida/rutagourmet",
 "fal": "https://www.bancofalabella.cl/descuentos/restaurantes",
 "sec": "https://personas.bancosecurity.cl/beneficios/gourmet?page=0",
 "rip": "https://www.bancoripley.cl/beneficios-y-promociones",
 "bci": "https://www.bci.cl/beneficios/beneficios-del-mes",
 "ita": "https://itaubeneficios.cl/beneficios/beneficios-y-descuentos/ruta-gourmet/",
 "ita_det": "https://itaubeneficios.cl/lunes-gourmet/carnal/",
 "bice": "https://banco.bice.cl/api/content/spaces/beneficios-bice/types/beneficios/entries?page=1&per_page=100",
 "be_nwm": "https://nwm.bancoestado.cl/content/bancoestado-public/cl/es/home/home/todosuma---bancoestado-personas/un-mes-de-sabores---bancoestado-personas.html",
 "be_www": "https://www.bancoestado.cl/content/bancoestado-public/cl/es/home/home/todosuma---bancoestado-personas/un-mes-de-sabores---bancoestado-personas.html",
}
os.makedirs("diag", exist_ok=True)
rep = {}
for k, u in SRC.items():
    t0 = time.time()
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "text/html,application/json;q=0.9,*/*;q=0.8", "Accept-Language": "es-CL,es;q=0.9"})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            if r.headers.get("Content-Encoding") == "gzip": body = gzip.decompress(body)
            rep[k] = {"status": r.status, "len": len(body), "ct": r.headers.get("Content-Type"), "s": round(time.time()-t0, 1)}
            open(f"diag/{k}.txt", "wb").write(body)
    except Exception as e:
        rep[k] = {"error": repr(e)[:300], "s": round(time.time()-t0, 1)}
        if hasattr(e, "read"):
            try: open(f"diag/{k}.err.txt", "wb").write(e.read()[:20000])
            except Exception: pass
json.dump(rep, open("diag/_reporte.json", "w"), indent=1)
print(json.dumps(rep, indent=1))
