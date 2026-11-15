"""Construye datos.json a partir de los datos crudos de scraper/crudo/ y del datos.json anterior.
Si un banco falla o trae muchos menos descuentos que antes, se conservan sus descuentos anteriores."""
import json, os, re, sys, html, calendar
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from comun import *  # nz, slug, CMAP, comuna_of, parse_days, days_text, parse_date, parse_tope, cat_of, add, items, TODAY, DAYS, EXCLUDE
import comun

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRUDO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crudo")
FIN_MES = f"{TODAY.year}-{TODAY.month:02d}-{calendar.monthrange(TODAY.year, TODAY.month)[1]:02d}"

def raw(k):
    p = os.path.join(CRUDO, f"{k}.json")
    if not os.path.exists(p): return None
    try: return json.load(open(p))
    except Exception: return None

def cm_exact(c):
    c = (c or '').strip(' .')
    if not c: return None
    k = nz(c)
    if k in CMAP and k not in {'florida','los lagos','maule','o higgins','arauco','cisnes'}: return CMAP[k]
    return comuna_of(c)

def antiguos():
    # ---------- Banco de Chile
    BCH = "https://sitiospublicos.bancochile.cl/personas/beneficios/sabores"
    for line in (raw('bch') or {}).get('lines', []):
        p = line.split('|')
        if len(p) < 9: continue
        name, pct, ds, vence, card, cat, seg, tope, br = p[:9]
        tarj = {"V": "Solo Visa Banco de Chile (promoción del mes)", "VI": "Solo Visa Infinite Banco de Chile"}.get(card, "Visa y Mastercard Banco de Chile")
        dias = [DAYS[int(c)-1] for c in ds if c.isdigit() and 1 <= int(c) <= 7]
        t = tope.strip()
        if 'abono' in t: tope_s = "Hasta $" + re.search(r'[\d.]+', t).group(0) + " (abono)" if re.search(r'[\d.]+', t) else "—"
        elif re.search(r'\$\s?[\d.]+', t): tope_s = "$" + re.search(r'\$\s?([\d.]+)', t).group(1).rstrip('.') + (" por mesa" if 'mesa' in t else "")
        else: tope_s = "—"
        cond = "Presencial. Pide el descuento al pagar." + (" Beneficio segmentado: puede no aplicar a todos los planes." if seg == 'S' else "")
        seen = set()
        for b in [x for x in br.split('^') if x]:
            q = b.split('~') + ['', '', '']
            cm = comuna_of(q[0], q[2], q[1])
            if not cm: continue
            key = (cm[0], q[2][:20])
            if key in seen: continue
            seen.add(key)
            addr = q[2] if q[2] and not re.match(r'^(local|regi)', q[2], re.I) else cm[0]
            add(cm[0], cm[1], restaurante=name.strip(), direccion=addr.strip(), categoria="Café" if cat == 'C' else cat_of(name), dias=dias, banco="Banco de Chile",
                tarjetas=tarj, dcto=int(pct), tope=tope_s, vence=vence or None, condiciones=cond, fuente=BCH)

    # ---------- Santander
    for p in (raw('san') or []):
        m = re.search(r'(\d+)\s*%', p['b'])
        if not m: continue
        d = p['d']
        if re.search(r'app |online|delivery|despacho', d, re.I) and not re.search(r'local|presencial', d, re.I): continue
        tm = re.search(r'Exclusivo con tus ([^.]+)\.', d)
        tarj = tm.group(1) if tm else "Tarjetas Santander"
        tarj = tarj.replace("Tarjetas de Crédito", "tarjetas de crédito")
        comunas = [c.strip(' .') for c in re.split(r',| y ', p['c']) if c.strip(' .')]
        if not comunas:
            cm = comuna_of(d)
            comunas = [cm[0]] if cm else []
        for c in comunas:
            cm = comuna_of(c)
            if not cm: continue
            am = re.search(r'([A-ZÁÉÍÓÚÑ][^.]{2,60}\d{2,5}[^.]{0,25}),\s*' + re.escape(cm[0].split()[0]), d)
            addr = am.group(1).strip() if am else cm[0]
            add(cm[0], cm[1], restaurante=p['t'].strip(), direccion=addr, categoria=cat_of(p['t'], d[:80]), dias=parse_days(p['b']) or parse_days(p['tags']),
                banco="Santander", tarjetas=tarj[0].upper() + tarj[1:], dcto=int(m.group(1)), tope=parse_tope(d), vence=parse_date(p['v']),
                condiciones="Válido en local. No acumulable con otras promociones.", fuente=p['u'])

    # ---------- Scotiabank
    SCO = "https://www.scotiarewards.cl/scclubfront/categoria/platosycomida/rutagourmet"
    for s in (raw('sco') or {}).get('sitios', []):
        d = html.unescape(s['d']); parts = [x.strip() for x in d.split('|')]
        m = re.search(r'(\d+)\s*%', d)
        if not m: continue
        cm = comuna_of(parts[2] if len(parts) > 2 else '', html.unescape(s['a']))
        if not cm: continue
        tm = re.search(r'Pagando con tus (Tarjetas[^.]*?)(?: en el Restaurante|\.)', d)
        tarj = tm.group(1) if tm else "Tarjetas de crédito Scotiabank seleccionadas"
        tarj = re.sub(r'^Tarjetas de Cr[eé]dito ', 'Tarjetas de crédito ', tarj)
        pet = " Pet friendly." if 'Pet Friendly' in d else ""
        add(cm[0], cm[1], restaurante=html.unescape(s['n']).strip(), direccion=html.unescape(s['a']).strip() or cm[0], categoria=cat_of(s['n']),
            dias=parse_days(s['e'] + ' ' + d[:400]), banco="Scotiabank", tarjetas=tarj, dcto=int(m.group(1)), tope=parse_tope(d), vence=parse_date(parts[0]),
            condiciones="Solo consumo presencial, con boleta. No válido en feriados." + pet, fuente=SCO)

    # ---------- Banco Falabella
    for f in (raw('fal') or []):
        if f.get('expired'): continue
        det = f.get('det') or ''
        if re.search(r'exclusivo online', (f.get('desc') or ''), re.I): continue
        m = re.search(r'(\d+)\s*%', det) or re.search(r'(\d+)\s*%', f['pct'])
        if not m: continue
        pct = max(int(x) for x in re.findall(r'(\d+)\s*%\s*(?:de )?dcto[^.]{0,30}CMR', det)) if re.search(r'(\d+)\s*%\s*(?:de )?dcto[^.]{0,30}CMR', det) else int(m.group(1))
        loc = re.search(r'(?:locales?|Direcci[oó]n(?:es)?)\s*:\s*(.+?)(?:Condiciones|¿Sabes|Todos los|$)', det, re.I)
        addrs = []
        if loc:
            for a in re.split(r',\s*Chile|;|\s{2,}|(?<=\d)\s+(?=[A-ZÁÉÍÓÚ][a-záéíóú]+ )', loc.group(1)):
                a = re.sub(r'^[^:]{1,40}:\s*', '', a.strip(' .,'))
                a = re.sub(r',?\s*Regi[oó]n Metropolitana.*$', '', a).strip(' .,')
                if 'solo delivery' in a.lower(): continue
                for a2 in re.split(r'\s+y\s+(?=[A-ZÁÉÍÓÚ])', a):
                    if len(a2) > 4 and not a2.startswith('Región'): addrs.append(a2.strip(' .,'))
        places = []
        for a in addrs:
            cm = comuna_of(a)
            if cm: places.append((cm, a))
        if not places:
            cm = comuna_of(f.get('desc') or '', f['t'], det[det.find('Descuento'):det.find('¿Sabes')] if '¿Sabes' in det else det[:600])
            if cm: places = [(cm, cm[0])]
        debit = re.search(r'(\d+)\s*%[^.]{0,30}d[eé]bito', det)
        tarj = "CMR Mastercard, Premium y Elite" + (f" ({debit.group(1)}% con débito Banco Falabella)" if debit else "")
        dias = parse_days(' '.join(f['days'])) or parse_days(det)
        seen = set()
        for cm, a in places:
            if (cm[0], a[:15]) in seen: continue
            seen.add((cm[0], a[:15]))
            add(cm[0], cm[1], restaurante=f['t'].replace(' ' + cm[0], '').strip() or f['t'], direccion=a.replace(', ' + cm[0], ''), categoria=cat_of(f['t'], det[300:500]),
                dias=dias, banco="Banco Falabella", tarjetas=tarj, dcto=pct, tope=parse_tope(det) if 'Sin Tope' not in f['pct'] else "Sin tope",
                vence=(f.get('end') or '')[:10] or parse_date(det), condiciones="Presencial. No acumulable con otras promociones.", fuente="https://www.bancofalabella.cl" + f['url'])

    # ---------- Security
    for s in (raw('sec') or []):
        t = s['txt']
        nm = t.split(' Visitar página')[0].strip()
        if re.search(r'rappi|app |online|delivery|despacho|pedidosya|uber', t[:400], re.I) and not re.search(r'tienda f[ií]sica|presencial|local', t[:300], re.I): continue
        m = re.search(r'(\d+)\s*%\s*de dcto\.?\s*([^,.]*)', t)
        if not m: continue
        am = re.search(r'([^.]{3,90}?),\s*([A-ZÁÉÍÓÚÑ][\wáéíóúñ ]{2,30})\.\s+(?:Todas|Todos)', t)
        cm = comuna_of(am.group(2)) if am else None
        if not cm:
            tail = t[max(0, t.find('Visitar página', 30) - 250): t.find('Visitar página', 30)]
            cm = comuna_of(tail)
        if not cm: continue
        addr = (am.group(1).split('. ')[-1].strip() if am else cm[0])
        tj = re.search(r'con tus? (Tarjeta[s]? [^.]*?)(?: en tienda| para|\.)', t)
        add(cm[0], cm[1], restaurante=nm, direccion=addr, categoria=cat_of(nm), dias=parse_days(m.group(2) + ' ' + t[t.find('Visitar página', 30)-60:t.find('Visitar página', 30)]),
            banco="Security", tarjetas=(tj.group(1) if tj else "Tarjeta One"), dcto=int(m.group(1)), tope=parse_tope(t), vence=parse_date(t[t.find('Promoción válida'):]),
            condiciones="En tienda física. No acumulable con otras promociones.", fuente=s['u'])

    # ---------- Ripley
    CUIS = ["Comida de Autor Italiana","Carnes angus ,sangucheria. Tablas y otros.","Tablas, sandwichs, burgers.","Sandwich, Tablas y Cafeterías","Cafetería y Comida Mediterranea",
     "Almuerzos y comidas de picoteos","Fusión Chilena, Peruana y Mexicana","Mexicana, Chilena y Peruana","Carnes a la parrilla","Carnes y Parrilladas","Pescados y Mariscos","Francesa y de autor",
     "Pizzas y sandiwch","Korean Street Food","Sandwich Gourmet","Burgers - Pizza","Robata fusión Food","Criolla Peruana","Fusion peruana","Fusion Chilena","Platillos de autor","Gastronomia Nikkei",
     "Cocina de autor","Bar Restaurante","Carnes Premium","Carne Premium","Comida Peruana","Comida Rapida","Social Food","Bar, pizzas","Hamburguesas","Internacional","Mediterranea","Parrilladas",
     "Tailandesa","Pokebowls","Restobar","Saludable","Cafeteria","Pizzería","Italiana","Italiano","Mexicana","Nikkei","Ramen","Carnes","Carne","Sushi","Bar"]
    RIP = "https://www.bancoripley.cl/beneficios-y-promociones"
    for r in (raw('rip') or []):
        t = r['t'].replace(' Más información', '')
        black = t.startswith('EXCLUSIVO BLACK')
        t = t.replace('EXCLUSIVO BLACK ', '')
        m = re.match(r'(TODOS LOS DÍAS|[A-ZÁÉÍÓÚ]+) (.+?) (\d+)% dcto (.+?) \((.+)\)$', t)
        if not m: continue
        dayw, rest, pct, _, places = m.groups()
        name, cui = rest, "Restaurante"
        for c in CUIS:
            if rest.endswith(' ' + c): name, cui = rest[:-len(c)-1], c; break
        for pl in places.split('/'):
            cm = comuna_of(pl.strip())
            if not cm: continue
            add(cm[0], cm[1], restaurante=name.strip(), direccion=cm[0], categoria=cui.strip(' .'), dias=parse_days(dayw.lower()), banco="Ripley",
                tarjetas="Solo Ripley Mastercard Black" if black else "Tarjetas Banco Ripley Mastercard", dcto=int(pct), tope="—", vence=FIN_MES,
                condiciones="Presencial. Revisa la dirección del local en el sitio de Ripley.", fuente=RIP + "?id=restofans&idItem=" + r['id'])


# ---------- BCI
def bci():
    URL = "https://www.bci.cl/beneficios/beneficios-del-mes"
    DMAP = {"lun":"lun","mar":"mar","mie":"mie","jue":"jue","vie":"vie","sab":"sab","dom":"dom"}
    for r in (raw('bci') or []):
        try: pct = int(r['pct'])
        except Exception: continue
        dias = [DMAP[d] for d in r['day'].split('|') if d in DMAP] or parse_days(r['dia'])
        dias = [d for d in DAYS if d in dias]
        card = r['card']
        tj = ("Crédito o débito Bci" if 'debito' in card else
              "Tarjetas de crédito Bci premium" if 'premium' in card else "Solo tarjeta de crédito Bci")
        cond = r['cond'] or ''
        tope = "Sin tope" if re.search(r'sin tope', cond, re.I) else ("$" + re.search(r'\$\s*([\d.]+)', cond).group(1) if re.search(r'\$\s*([\d.]+)', cond) else "—")
        vm = re.search(r'(\d{1,2}) de (\w+)(?: de (\d{4}))?', nz(r['vig']).replace('hasta el ', ''))
        vence = None
        if vm and vm.group(2) in comun.MES:
            y = int(vm.group(3) or TODAY.year); mo = comun.MES[vm.group(2)]
            if not vm.group(3) and mo < TODAY.month - 1: y += 1
            vence = f"{y}-{mo:02d}-{int(vm.group(1)):02d}"
        for c in (r['com'] or '').split('|'):
            cm = cm_exact(c)
            if not cm: continue
            add(cm[0], cm[1], restaurante=r['name'], direccion=cm[0], categoria=cat_of(r['name']), dias=dias, banco="BCI", tarjetas=tj,
                dcto=pct, tope=tope, vence=vence or FIN_MES, condiciones="Presencial. Excluye tarjetas Lider Bci y MACH. Revisa la dirección del local en bci.cl.", fuente=r.get('href') or URL)

# ---------- Itaú
def itau():
    URL = "https://itaubeneficios.cl/beneficios/beneficios-y-descuentos/ruta-gourmet/"
    for it in (raw('ita') or []):
        t = [x.strip() for x in it.get('t', '').split('|') if x.strip()]
        if len(t) < 3 or any(re.search(r'delivery|online', x, re.I) for x in t): continue
        name = t[0]
        loc = t[1]
        pm = next((x for x in t if re.match(r'^\d+\s*%$', x)), None)
        if not pm: continue
        pct = int(pm.rstrip('%').strip())
        com = loc.split(',')[0].strip()
        if re.search(r'^(rm|regi|rm y)', com, re.I): continue
        cm = cm_exact(com)
        if not cm: continue
        d = it.get('d') or ''
        if 'Enable JavaScript' in d or d.startswith('ERR'): d = ''
        hm = re.search(r'hasta el (\d{2})-(\d{2})-(\d{4})', d)
        vence = f"{hm.group(3)}-{hm.group(2)}-{hm.group(1)}" if hm else None
        bm = re.search(r'Beneficio\|([^|]+)', d)
        ben = bm.group(1) if bm else ''
        dias = parse_days(ben) or parse_days(' '.join(t))
        if not dias: continue
        if not d: vence = FIN_MES
        if re.search(r'Black', ben) and not re.search(r'Legend', ben): tj = "Solo tarjeta de crédito Black Itaú (Mastercard Black / Visa Signature)"
        elif re.search(r'd[eé]bito', ben, re.I): tj = "Tarjetas de crédito y débito Itaú"
        elif re.search(r'Legend', ben) and re.search(r'Black', ben): tj = "Tarjetas de crédito Legend y Black Itaú"
        elif re.search(r'Legend', ben): tj = "Solo tarjeta de crédito Legend Itaú"
        else: tj = "Tarjetas de crédito Itaú" if d else "Tarjeta de crédito Legend Itaú (revisa la ficha del local)"
        tm = re.search(r'(?:Tope de descuento:?|M[aá]ximo descuento mensual[^$|]{0,120})\s*\$\s?([\d.]+)', d)
        if tm:
            v = int(tm.group(1).replace('.', ''))
            if v < 1000: v *= 1000
            tope = "$" + format(v, ',').replace(',', '.') + (" al mes" if 'ensual' in tm.group(0) else "")
        else: tope = "—"
        add(cm[0], cm[1], restaurante=name, direccion=cm[0], categoria=cat_of(name), dias=dias, banco="Itaú", tarjetas=tj, dcto=pct, tope=tope, vence=vence,
            condiciones="Presencial; avisa al pedir la cuenta que pagas con tu tarjeta Itaú. Excluye propina.", fuente=it.get('h') or URL)

# ---------- BICE
def bice():
    URL = "https://banco.bice.cl/personas/beneficios"
    for e in (raw('bice') or []):
        big, baj, small = e.get('big', ''), e.get('baj', ''), e.get('small', '')
        m = re.match(r'\s*(\d+)\s*%', big)
        if not m or re.search(r'online|d[oó]lares', big + ' ' + small + ' ' + e.get('n', ''), re.I) and not re.search(r'presencial', small, re.I): continue
        if re.search(r'^\s*Online', e.get('ciu', '') + ' ' + e.get('dir', ''), re.I): continue
        pct = int(m.group(1))
        name = re.split(r'\s*[/|]\s*|\s+-\s+', e.get('n', ''))[0].strip()
        txt = baj + ' ' + e.get('n', '')
        dias = parse_days(baj) or parse_days(e.get('n', '')) or (DAYS[:] if re.search(r'todo el men|todos los d', baj, re.I) else [])
        if not dias: continue
        allt = baj + ' ' + e.get('cond', '') + ' ' + e.get('n', '')
        if re.search(r'Limitless', allt): tj = "Solo tarjeta de crédito Visa Limitless BICE"
        elif re.search(r'Signatur', allt): tj = "Solo tarjetas de crédito BICE Signature / Infinite (Selección del Chef)"
        elif re.search(r'Banca Joven', allt): tj = "Tarjeta de crédito BICE (clientes Banca Joven)"
        elif 'Débito' in e.get('tipo', '') and re.search(r'd[eé]bito', baj, re.I): tj = "Tarjetas de crédito y débito BICE"
        else: tj = "Solo tarjeta de crédito BICE"
        tm = re.search(r'[Tt]ope de descuento de \$\s?([\d.]+)', e.get('cond', ''))
        tope = ("$" + tm.group(1).rstrip('.') + (" (1 compra al día)" if 'diaria' in e.get('cond', '') else "")) if tm else "—"
        coms = []
        ciu = ' ' + nz(e.get('ciu', '')) + ' '
        for k in comun.KEYS:
            if (' ' + k + ' ') in ciu:
                cm = CMAP[k]; ciu = ciu.replace(' ' + k + ' ', ' | ')
                if cm not in coms: coms.append(cm)
        if not coms:
            cm = comuna_of(e.get('dir', ''))
            if cm: coms = [cm]
        for cm in coms:
            add(cm[0], cm[1], restaurante=name, direccion=cm[0], categoria=cat_of(name), dias=dias, banco="BICE", tarjetas=tj, dcto=pct, tope=tope,
                vence=(e.get('hasta') or None), condiciones="Presencial. No válido con tarjetas Visa Universal, Pago, Credivida y Empresarial. Revisa la dirección en el sitio de BICE.",
                fuente=URL + "/" + e.get('slug', ''))

# ---------- BancoEstado
ABR = {"lun":0,"mar":1,"mie":2,"jue":3,"vie":4,"sab":5,"dom":6}
def be_days(t):
    n = nz(t)
    m = re.search(r'excepto (\w{3})\w* ?(?:-|y|a) ?(\w{3})', n)
    if m and m.group(1) in ABR and m.group(2) in ABR:
        a, b = ABR[m.group(1)], ABR[m.group(2)]
        ex = set(range(a, b + 1)) if a <= b else set(range(a, 7)) | set(range(0, b + 1))
        return [DAYS[i] for i in range(7) if i not in ex]
    m = re.search(r'excepto (\w{3})', n)
    if m and m.group(1) in ABR: return [d for i, d in enumerate(DAYS) if i != ABR[m.group(1)]]
    return parse_days(t)
def bancoestado():
    URL = "https://www.bancoestado.cl/content/bancoestado-public/cl/es/home/home/todosuma---bancoestado-personas/un-mes-de-sabores---bancoestado-personas.html"
    d = raw('be') or {}
    ms = d.get('ms', []); used = set()
    cards = []
    for c in d.get('cards', []):
        f = [x.strip() for x in c.split('|') if x.strip()]
        pi = next((i for i, x in enumerate(f) if re.match(r'^\d+% dto', x)), None)
        if pi is None or pi < 2 or pi + 1 >= len(f): continue
        cards.append([f[pi - 2], f[pi - 1], int(f[pi].split('%')[0]), f[pi + 1], None])
    STOP = {'la', 'el', 'los', 'las', 'bar', 'restaurant', 'restaurante', 'cafe', 'sushi'}
    for paso in range(3):
        for cd in cards:
            if cd[4] is not None: continue
            n = nz(cd[3])
            for i, m in enumerate(ms):
                if i in used: continue
                mn = nz(m['n'])
                if paso == 0: ok = mn == n
                elif paso == 1: ok = bool(mn and n) and (mn.startswith(n) or n.startswith(mn))
                else: ok = bool(n.split() and mn.split()) and n.split()[0] == mn.split()[0] and n.split()[0] not in STOP and len(n.split()[0]) > 3
                if ok: cd[4] = i; used.add(i); break
    for reg, days, pct, name, mi in cards:
        if re.search(r'online', days, re.I) or EXCLUDE.search(name) or mi is None: continue
        m = ms[mi]
        ps = ' / '.join(m['ps'])
        dias = be_days(days)
        if not dias: continue
        tope = parse_tope(ps); vence = parse_date(ps.split(' al ')[-1]) if ' al ' in ps else parse_date(ps)
        coms = []
        for a in m['li']:
            cm = comuna_of(a)
            if cm and cm not in coms: coms.append(cm)
        for cm in coms:
            add(cm[0], cm[1], restaurante=name, direccion=cm[0], categoria=cat_of(name), dias=dias, banco="BancoEstado",
                tarjetas="Solo tarjeta de crédito Visa BancoEstado", dcto=pct, tope=tope, vence=vence,
                condiciones="Presencial; solicita el descuento al pagar. No incluye propina. Sujeto a presupuesto disponible.", fuente=URL)

BANCOS = ["Banco de Chile", "BCI", "Santander", "Scotiabank", "Banco Falabella", "Security", "Ripley", "Itaú", "BICE", "BancoEstado"]

def main():
    prev_path = os.path.join(BASE, "datos.json")
    prev = json.load(open(prev_path))
    prev_items = [dict(ciudad=c['ciudad'], region=c['region'], **i) for c in prev['ciudades'] for i in c['items']]
    for fn in (antiguos, bci, itau, bice, bancoestado):
        try: fn()
        except Exception as e:
            import traceback; traceback.print_exc()
    nuevos = Counter(i['banco'] for i in items)
    antes = Counter(i['banco'] for i in prev_items)
    final, revisados, fallidos, rep = [], [], [], {}
    hoy = TODAY.isoformat()
    for b in BANCOS:
        if nuevos[b] and nuevos[b] >= 0.5 * antes[b]:
            final += [i for i in items if i['banco'] == b]; revisados.append(b); rep[b] = {"antes": antes[b], "ahora": nuevos[b], "estado": "actualizado"}
        else:
            keep = [i for i in prev_items if i['banco'] == b and (not i.get('vence') or i['vence'] >= hoy)]
            final += keep; fallidos.append(b); rep[b] = {"antes": antes[b], "nuevos": nuevos[b], "conservados": len(keep), "estado": "sin cambios (falló la revisión)"}
    final += [i for i in prev_items if i['banco'] not in BANCOS and (not i.get('vence') or i['vence'] >= hoy)]
    uniq = {}
    for it in final:
        k = (it['ciudad'], nz(it['restaurante']), it['banco'], it['dcto'], tuple(it['dias']))
        uniq.setdefault(k, it)
    by = {}
    for it in uniq.values():
        d = by.setdefault(slug(it['ciudad']), {'ciudad': it['ciudad'], 'region': it['region'], 'actualizado': hoy, 'items': []})
        d['items'].append({k: v for k, v in it.items() if k not in ('ciudad', 'region')})
    for d in by.values(): d['items'].sort(key=lambda x: (-x['dcto'], x['restaurante']))
    prox = TODAY.replace(day=15) if TODAY.day < 15 else (TODAY.replace(year=TODAY.year + (TODAY.month == 12), month=TODAY.month % 12 + 1, day=2))
    if TODAY.day < 2: prox = TODAY.replace(day=2)
    meta = {"actualizado": hoy, "proxima": prox.isoformat(), "calendario": "Se actualiza los días 2 y 15 de cada mes", "bancos": revisados + [b for b in fallidos if antes[b]],
            "nota": ("No se pudo revisar " + ", ".join(fallidos) + " en esta actualización; se muestran sus descuentos anteriores vigentes.") if fallidos else ""}
    out = {"meta": meta, "ciudades": [by[k] for k in sorted(by)]}
    json.dump(out, open(prev_path, "w"), ensure_ascii=False, separators=(',', ':'))
    total = sum(len(c['items']) for c in out['ciudades'])
    rep["_total"] = {"descuentos": total, "ciudades": len(out['ciudades'])}
    json.dump(rep, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "reporte.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
