"""Diagnóstico 2: fuentes bloqueadas, con un Chromium real (Playwright)."""
import json, os, asyncio
from playwright.async_api import async_playwright
os.makedirs("diag", exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
CASES = {
 "bch": ("https://sitiospublicos.bancochile.cl/personas/beneficios/sabores", "fetch('/api/content/spaces/personas/types/beneficios/entries?page=1&per_page=100').then(r=>r.status+' '+r.headers.get('content-type')+' '+'').catch(e=>'ERR '+e)", "fetch('/api/content/spaces/personas/types/beneficios/entries?page=1&per_page=100').then(r=>r.text())"),
 "san": ("https://banco.santander.cl/beneficios", "fetch('/beneficios/promociones.json?per_page=9999&custom_fields=true').then(r=>r.status+'').catch(e=>'ERR '+e)", "fetch('/beneficios/promociones.json?per_page=9999&custom_fields=true').then(r=>r.text())"),
 "bice": ("https://banco.bice.cl/personas/beneficios", "fetch('/api/content/spaces/beneficios-bice/types/beneficios/entries?page=1&per_page=100').then(r=>r.status+'').catch(e=>'ERR '+e)", "fetch('/api/content/spaces/beneficios-bice/types/beneficios/entries?page=1&per_page=100').then(r=>r.text())"),
 "be": ("https://nwm.bancoestado.cl/content/bancoestado-public/cl/es/home/home/todosuma---bancoestado-personas/un-mes-de-sabores---bancoestado-personas.html", "Promise.resolve(document.querySelectorAll('.modal-sabores').length+' modales')", "Promise.resolve(document.documentElement.outerHTML)"),
 "rip": ("https://www.bancoripley.cl/beneficios-y-promociones", "new Promise(r=>setTimeout(()=>r(document.querySelectorAll('minibox-beneficios').length+' minibox'),6000))", "Promise.resolve(JSON.stringify([...document.querySelectorAll('minibox-beneficios')].map(m=>({t:m.innerText.replace(/\\s+/g,' ').trim(),id:(m.querySelector('a.linkDetalle')||{}).id||''}))))"),
}
async def main():
    rep = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", args=["--disable-blink-features=AutomationControlled"])
        for k, (url, probe, grab) in CASES.items():
            ctx = await b.new_context(user_agent=UA, locale="es-CL", timezone_id="America/Santiago")
            page = await ctx.new_page()
            reqs = []
            page.on("request", lambda r: reqs.append(r.url) if r.resource_type in ("xhr", "fetch") else None)
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(8000)
                st = await page.evaluate(probe)
                body = await page.evaluate(grab)
                open(f"diag/pw_{k}.txt", "w").write(body or "")
                rep[k] = {"nav": resp.status if resp else None, "title": await page.title(), "probe": st, "len": len(body or ""), "xhr": reqs[:25]}
            except Exception as e:
                rep[k] = {"error": repr(e)[:400], "xhr": reqs[:25]}
            await ctx.close()
        await b.close()
    json.dump(rep, open("diag/_reporte_pw.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(rep, indent=1, ensure_ascii=False))
asyncio.run(main())
