"""Descarga los beneficios de restaurantes de cada banco y los guarda en crudo en scraper/crudo/<banco>.json.
Usa un Chrome real (Playwright) porque varios bancos bloquean pedidos que no vienen de un navegador."""
import asyncio, json, os, sys, time, traceback
from playwright.async_api import async_playwright

OUT = os.path.join(os.path.dirname(__file__), "crudo")
os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

STRIP = r"const strip=s=>(s||'').toString().replace(/<[^>]+>/g,' ').replace(/&nbsp;/g,' ').replace(/&gt;/g,'>').replace(/&amp;/g,'&').replace(/\s+/g,' ').trim();"

JS = {}
JS["bch"] = ("https://sitiospublicos.bancochile.cl/personas/beneficios/sabores", r"""async()=>{
let all=[];for(let p=1;p<=15;p++){const r=await fetch(`/api/content/spaces/personas/types/beneficios/entries?page=${p}&per_page=100`).then(r=>r.json());const items=r.entries||[];if(!items.length)break;all.push(...items);}
const strip=s=>(s||'').toString().replace(/<[^>]+>/g,';').replace(/&nbsp;/g,' ').replace(/\s+/g,' ');
const RG=/(arica|tarapac|antofagasta|atacama|coquimbo|valpara[ií]so|metropolitana|o'?higgins|libertador|maule|ñuble|nuble|b[ií]o ?b[ií]o|araucan|los r[ií]os|los lagos|ays[eé]n|magallanes)/i;
const D={lunes:'1',martes:'2',miercoles:'3',jueves:'4',viernes:'5',sabado:'6',domingo:'7'};
const cats=['40-de-descuento-visa','50-de-descuento-visa-infinite','cafeterias','restaurantes-y-bares'];
const out=[];
for(const e of all){const cat=(e.meta.category||'').split('/').pop();if(!cats.includes(cat))continue;const f=e.fields;
 const pct=(strip(f['Tipo Beneficio']).match(/(\d+)\s*%/)||[])[1];if(!pct)continue;
 const days=(e.meta.tags||[]).map(t=>D[t]).filter(Boolean).sort().join('');
 const u=e.meta.unpublish_at?new Date(new Date(e.meta.unpublish_at).getTime()-4*3600e3).toISOString().slice(0,10):'';
 const desc=strip(f.Descripcion);const tope=((desc.match(/[Tt]ope[^.;]*?\$\s?[\d.]+[^.;]*/)||[''])[0]).replace(/^[Tt]ope (de )?(dto\.?|descuento)?:?\s*/,'').slice(0,40);
 const seg=strip(f.Sucursales).split(/;/).map(s=>s.replace(/VACIO/g,'').trim()).filter(Boolean);
 const br=[];for(let i=0;i<seg.length;i++){if(RG.test(seg[i])&&seg[i].length<60&&seg[i+1]&&!RG.test(seg[i+1])){let com=seg[i+1].replace(/Tel[eé]fono.*$/i,'').replace(/[-\d.,]+$/,'').trim();if(com.length>30||!com)continue;br.push(com+'~'+seg[i].replace(/Regi[oó]n (de |del )?(la )?/i,'')+'~'+(seg[i-1]||'').slice(0,60));}}
 const card=cat.includes('infinite')?'VI':cat.includes('visa')?'V':'';
 out.push([(f.Titulo||e.meta.name).trim(),pct,days,u,card,cat==='cafeterias'?'C':'R',(e.meta.tags||[]).includes('segmentado')?'S':'',tope,[...new Set(br)].join('^')].join('|'));}
return {total:all.length,lines:out};}""")

JS["san"] = ("https://banco.santander.cl/beneficios", r"""async()=>{
const j=await fetch('/beneficios/promociones.json?per_page=9999&custom_fields=true').then(r=>r.json());
""" + STRIP + r"""
return j.promociones.filter(p=>(p.tags||[]).includes('cat-sabores')).map(p=>({t:p.title,u:p.url,b:strip(p.custom_fields['Bajada externa']?.value),v:strip(p.custom_fields['Vigencia']?.value),c:strip(p.custom_fields['Comuna cobertura']?.value),r:strip(p.custom_fields['Región cobertura']?.value),tags:(p.tags||[]).join(','),d:strip(p.description).slice(0,900)}));}""")

JS["sco"] = ("https://www.scotiarewards.cl/scclubfront/categoria/platosycomida/rutagourmet", r"""async()=>{
const s=[...document.scripts].map(x=>x.textContent).find(t=>t.includes('const sitiosSantiago'));
const grab=n=>{const i=s.indexOf('const '+n);const a=s.indexOf('[',i);let d=0,k=a,q=false,esc=false;for(;k<s.length;k++){const c=s[k];if(q){if(esc)esc=false;else if(c==='\\')esc=true;else if(c==='"')q=false;continue}if(c==='"')q=true;else if(c==='[')d++;else if(c===']'){d--;if(d===0)break}}return JSON.parse(s.slice(a,k+1))};
""" + STRIP + r"""
const all=[...grab('sitiosSantiago').map(x=>({...x,zona:'santiago'})),...grab('sitiosRegiones').map(x=>({...x,zona:'regiones'}))];
return {sitios:all.map(x=>({n:strip(x.nombre),a:strip(x.direccion),e:strip(x.especialidad),r:x.id_region,z:x.zona,d:strip(x.descripcion).slice(0,1400)}))};}""")

JS["fal"] = ("https://www.bancofalabella.cl/descuentos/restaurantes", r"""async()=>{
const h=document.documentElement.innerHTML.replace(/\\"/g,'"');const re=/\{"benefitCard":\{[\s\S]*?"benefitTitle":"[^"]*"[^\]]*?\]\}/g;const m=h.match(re)||[];
const seen={};const items=[];for(const s of m){let o;try{o=JSON.parse(s)}catch(e){continue}const c=o.benefitCard||{};const k=c.linkUrl;if(!k||seen[k])continue;seen[k]=1;items.push({t:o.benefitTitle,desc:c.description,url:k,days:Array.isArray(c.discountDays)?c.discountDays:[],pct:(c.topDiscountText||'')+' '+(c.centerDiscountText||'')+' '+(c.bottomDiscountText||''),end:c.endDate||o.limitDate,reg:o.region,cards:o.creditCards})}
const strip=x=>x.replace(/<script[\s\S]*?<\/script>/g,' ').replace(/<style[\s\S]*?<\/style>/g,' ').replace(/<[^>]+>/g,' ').replace(/&nbsp;/g,' ').replace(/\s+/g,' ');
const work=async it=>{for(let k=0;k<4;k++){try{const x=strip(await fetch(it.url).then(r=>r.text()));const i=x.indexOf('Disfruta de tu beneficio');it.det=i>=0?x.slice(i,i+1100):'';if(/Este beneficio ya no est/.test(x))it.expired=1;if(it.det||it.expired)return}catch(e){it.det=''}await new Promise(r=>setTimeout(r,1500*(k+1)))}};
for(let i=0;i<items.length;i+=3){await Promise.all(items.slice(i,i+3).map(work));await new Promise(r=>setTimeout(r,300))}
return items;}""")

JS["sec"] = ("https://personas.bancosecurity.cl/beneficios/gourmet", r"""async()=>{
const links=new Set();for(let p=0;p<15;p++){const html=await fetch('/beneficios/gourmet?page='+p).then(r=>r.ok?r.text():'').catch(()=>'');if(!html)break;const d=new DOMParser().parseFromString(html,'text/html');const ls=[...d.querySelectorAll('a[href*="/beneficios/gourmet/"]')].map(a=>a.href.split('?')[0]).filter(h=>!/page/.test(h));const before=links.size;ls.forEach(l=>links.add(l));if(links.size===before&&p>0)break}
const out=[];const work=async u=>{try{const h=await fetch(u).then(r=>r.text());const d=new DOMParser().parseFromString(h,'text/html');d.querySelectorAll('script,style,header,footer,nav').forEach(e=>e.remove());const t=d.body.textContent.replace(/\s+/g,' ');const v=t.indexOf('Visitar página');const i=t.lastIndexOf('Security Pesos ',v);const j=t.indexOf('Dólar Observado');out.push({u,txt:t.slice(i>0?i+15:Math.max(0,v-100),j>0?j:v+1500).slice(0,1500)})}catch(e){}};
const items=[...links];for(let i=0;i<items.length;i+=8)await Promise.all(items.slice(i,i+8).map(work));return out;}""")

JS["rip"] = ("https://www.bancoripley.cl/beneficios-y-promociones", r"""async()=>{
for(let i=0;i<20&&document.querySelectorAll('minibox-beneficios').length<10;i++)await new Promise(r=>setTimeout(r,1000));
return [...document.querySelectorAll('minibox-beneficios')].map(m=>({t:m.innerText.replace(/\s+/g,' ').trim(),id:(m.querySelector('a.linkDetalle')||{}).id||''}));}""")

JS["ita"] = ("https://itaubeneficios.cl/beneficios/beneficios-y-descuentos/ruta-gourmet/", r"""async()=>{
return [...document.querySelectorAll('.beneficio__item')].filter(a=>a.href).map(a=>({h:a.href,t:a.innerText.replace(/\s*\n\s*/g,'|')}));}""")

DETALLE_ITA = r"""()=>{const m=(document.querySelector('main')||document.body).cloneNode(true);m.querySelectorAll('script,style,nav,header,footer').forEach(e=>e.remove());return m.textContent.replace(/\s*\n\s*/g,'|').replace(/[ \t]+/g,' ').slice(0,2500)}"""

async def detalles_itau(page, its, limite):
    """Itaú bloquea los pedidos en ráfaga: abre cada ficha como una visita normal (máx. ~7 minutos;
    si no alcanza, las fichas que falten se completan con los datos del listado)."""
    for it in its:
        if time.time() > limite: break
        for intento in range(2):
            try:
                await page.goto(it["h"], wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(1200)
                for _ in range(10):
                    if "momento" not in (await page.title()).lower() and "just a moment" not in (await page.title()).lower(): break
                    await page.wait_for_timeout(1500)
                it["d"] = await page.evaluate(DETALLE_ITA)
                if "Enable JavaScript and cookies" not in it["d"]: break
            except Exception as ex:
                it["d"] = "ERR " + repr(ex)[:100]
            await page.wait_for_timeout(3000 * (intento + 1))
    return its

JS["bice"] = ("https://banco.bice.cl/personas/beneficios", r"""async()=>{
let all=[];for(let p=1;p<=10;p++){const r=await fetch(`/api/content/spaces/beneficios-bice/types/beneficios/entries?page=${p}&per_page=100`);const t=await r.text();if(t.trim().startsWith('<'))break;const j=JSON.parse(t);if(!j.entries.length)break;all.push(...j.entries)}
const st=v=>v==null?'':(typeof v==='string'?v:(Array.isArray(v)?v.map(st).join(';'):(v.name||v.title||v.slug||JSON.stringify(v)))).replace(/<[^>]+>/g,' ').replace(/&nbsp;/g,' ').replace(/&amp;/g,'&').replace(/\s+/g,' ').trim();
return all.filter(e=>['restaurante','gourmet'].includes(e.meta.category_slug)).map(e=>{const f=e.fields;return {n:e.meta.name,slug:e.meta.slug,big:st(f['Texto-promo-big']),small:st(f['Texto-promo-small']),baj:st(f.Bajada),reg:st(f.Region),ciu:st(f.Ciudades),dir:st(f.Direccion),tipo:st(f['Tipo Tarjeta']),hasta:st(f['Fecha-hasta']).slice(0,10),cond:st(f.Condiciones_beneficio).slice(0,500)}});}""")

JS["be"] = ("https://nwm.bancoestado.cl/content/bancoestado-public/cl/es/home/home/todosuma---bancoestado-personas/un-mes-de-sabores---bancoestado-personas.html", r"""async()=>{
const ms=[...document.querySelectorAll('.modal-sabores')].map(m=>{const im=m.querySelector('img');return {n:(im?im.alt:m.id).replace(/^Logo /,''),ps:[...m.querySelectorAll('p')].map(p=>p.textContent.replace(/\s+/g,' ').trim()).filter(Boolean),li:[...m.querySelectorAll('li')].map(l=>l.textContent.replace(/\s+/g,' ').trim())}});
const t=document.body.innerText;const a=t.indexOf('Conoce más');
const pre=t.slice(0,a).split('\n').map(s=>s.trim()).filter(Boolean).slice(-4).join('|');
const cards=[pre,...t.slice(a).replace(/\s*\n\s*/g,'|').split('Conoce más').map(s=>s.replace(/^\||\|$/g,'')).filter(Boolean)];
return {cards,ms};}""")

JS["bci"] = ("https://www.bci.cl/beneficios/beneficios-del-mes", r"""async()=>{
return [...document.querySelectorAll('table.vp-tabla--rest tr.vp-item')].map(r=>({day:r.dataset.day||'',card:r.dataset.card||'',com:r.dataset.comuna||'',pct:r.dataset.pct||'',name:r.dataset.name||'',cond:(r.querySelector('.vp-c-cond')||{}).innerText||'',vig:(r.querySelector('.vp-c-vig')||{}).innerText||'',dia:(r.querySelector('.vp-c-dia')||{}).innerText||'',href:(r.querySelector('a')||{}).href||''}));}""")

async def run(only=None):
    rep = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", args=["--disable-blink-features=AutomationControlled"])
        for k, (url, js) in JS.items():
            if only and k not in only: continue
            t0 = time.time()
            ctx = await b.new_context(user_agent=UA, locale="es-CL", timezone_id="America/Santiago", viewport={"width": 1280, "height": 900})
            page = await ctx.new_page()
            ultimo = None
            for vuelta in range(3 if k == 'bice' else 2):
                try:
                    resp = None
                    for intento in range(2):
                        resp = await page.goto(url, wait_until="domcontentloaded", timeout=90000)
                        await page.wait_for_timeout(8000 if intento == 0 else 25000)
                        titulo = ""
                        try: titulo = await page.title()
                        except Exception: pass
                        if resp and resp.status < 400 and "Un momento" not in titulo: break
                    data = await asyncio.wait_for(page.evaluate(js), timeout=300)
                    if k == "ita": data = await detalles_itau(page, data, limite=time.time() + 420)
                    n = len(data["lines"] if isinstance(data, dict) and "lines" in data else data["sitios"] if isinstance(data, dict) and "sitios" in data else data["cards"] if isinstance(data, dict) and "cards" in data else data)
                    if not n: raise RuntimeError("sin datos (posible bloqueo)")
                    json.dump(data, open(os.path.join(OUT, f"{k}.json"), "w"), ensure_ascii=False)
                    rep[k] = {"ok": True, "n": n, "status": resp.status if resp else None, "s": round(time.time() - t0), "vuelta": vuelta}
                    break
                except Exception as e:
                    ultimo = e
                    rep[k] = {"ok": False, "error": repr(e)[:300], "s": round(time.time() - t0)}
                    try:
                        await page.close()
                    except Exception: pass
                    await ctx.close()
                    await asyncio.sleep(20)
                    ctx = await b.new_context(user_agent=UA, locale="es-CL", timezone_id="America/Santiago", viewport={"width": 1280, "height": 900})
                    page = await ctx.new_page()
            await ctx.close()
            print(k, rep[k], flush=True)
        await b.close()
    json.dump(rep, open(os.path.join(OUT, "_extraccion.json"), "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1:] or None))
