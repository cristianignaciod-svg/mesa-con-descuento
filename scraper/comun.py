import json, re, unicodedata, html, datetime
from zoneinfo import ZoneInfo
TODAY = datetime.datetime.now(ZoneInfo("America/Santiago")).date()

def nz(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9 ]+', ' ', s).strip()

def slug(s): return re.sub(r'\s+', '-', nz(s))

R = {"AP":"Arica y Parinacota","TA":"Tarapacá","AN":"Antofagasta","AT":"Atacama","CO":"Coquimbo","VA":"Valparaíso","RM":"Metropolitana",
     "OH":"O'Higgins","MA":"Maule","NU":"Ñuble","BI":"Biobío","AR":"La Araucanía","LR":"Los Ríos","LL":"Los Lagos","AY":"Aysén","MG":"Magallanes"}
COM = {
"AP":"Arica,Putre",
"TA":"Iquique,Alto Hospicio,Pozo Almonte,Pica",
"AN":"Antofagasta,Calama,Mejillones,Tocopilla,Taltal,San Pedro de Atacama",
"AT":"Copiapó,Caldera,Vallenar,Chañaral,Diego de Almagro",
"CO":"La Serena,Coquimbo,Ovalle,Illapel,Vicuña,Los Vilos,Salamanca,Andacollo",
"VA":"Valparaíso,Viña del Mar,Concón,Quilpué,Villa Alemana,Quillota,La Calera,Limache,Olmué,San Antonio,Cartagena,El Quisco,Algarrobo,El Tabo,Casablanca,Los Andes,San Felipe,Puchuncaví,Zapallar,Papudo,La Ligua,Isla de Pascua,Llay-Llay,Rinconada,Santo Domingo,Nogales,La Cruz,Hijuelas,Quintero,Cabildo",
"RM":"Santiago,Providencia,Las Condes,Vitacura,Lo Barnechea,Ñuñoa,La Reina,Peñalolén,Macul,La Florida,Puente Alto,San Miguel,San Joaquín,La Cisterna,El Bosque,San Bernardo,Maipú,Cerrillos,Estación Central,Pudahuel,Quinta Normal,Lo Prado,Cerro Navia,Renca,Quilicura,Huechuraba,Conchalí,Recoleta,Independencia,Colina,Lampa,Buin,Paine,Pirque,San José de Maipo,Talagante,Peñaflor,Padre Hurtado,Melipilla,Curacaví,La Granja,La Pintana,Lo Espejo,Pedro Aguirre Cerda,San Ramón,Calera de Tango,El Monte,Isla de Maipo,Tiltil",
"OH":"Rancagua,Machalí,San Fernando,Santa Cruz,Pichilemu,Rengo,San Vicente,Graneros,Navidad,Chimbarongo,Peumo,Codegua,Doñihue,Las Cabras,Marchigüe,Nancagua,Palmilla,Litueche,Requínoa,Olivar",
"MA":"Talca,Curicó,Linares,Constitución,Cauquenes,Molina,Parral,San Javier,Pelluhue,Romeral,Teno,Maule,San Clemente,Licantén,Vichuquén,Rauco",
"NU":"Chillán,Chillán Viejo,San Carlos,Bulnes,Quirihue,Cobquecura,Pinto,Yungay,Coelemu",
"BI":"Concepción,Talcahuano,Hualpén,San Pedro de la Paz,Chiguayante,Penco,Tomé,Coronel,Lota,Los Ángeles,Arauco,Cañete,Lebu,Mulchén,Nacimiento,Curanilahue,Cabrero,Hualqui,Santa Juana,Florida,Contulmo,Laja,Yumbel",
"AR":"Temuco,Padre Las Casas,Villarrica,Pucón,Angol,Victoria,Lautaro,Pitrufquén,Nueva Imperial,Curacautín,Lonquimay,Freire,Gorbea,Loncoche,Carahue,Puerto Saavedra,Melipeuco,Cunco,Traiguén,Collipulli,Curarrehue",
"LR":"Valdivia,La Unión,Río Bueno,Panguipulli,Los Lagos,Futrono,Lanco,Paillaco,Mariquina,Corral,Máfil,Lago Ranco",
"LL":"Puerto Montt,Puerto Varas,Osorno,Castro,Ancud,Frutillar,Llanquihue,Calbuco,Maullín,Quellón,Dalcahue,Chonchi,Puerto Octay,Fresia,Los Muermos,Purranque,Río Negro,Cochamó,Chaitén,Futaleufú,Hualaihué,Curaco de Vélez,Quinchao,Puqueldón,Queilén,Quemchi,San Pablo,Puyehue,San Juan de la Costa",
"AY":"Coyhaique,Puerto Aysén,Chile Chico,Cochrane,Río Ibáñez,Cisnes,Guaitecas,Lago Verde,O'Higgins,Tortel",
"MG":"Punta Arenas,Puerto Natales,Porvenir,Puerto Williams,Torres del Paine,Cabo de Hornos"}
CMAP = {}
for r, cs in COM.items():
    for c in cs.split(','): CMAP[nz(c)] = (c, R[r])
ALIAS = {"santiago centro":"Santiago","stgo":"Santiago","renaca":"Viña del Mar","vina":"Viña del Mar","curauma":"Valparaíso","cerro alegre":"Valparaíso","chicureo":"Colina",
 "los dominicos":"Las Condes","maitencillo":"Puchuncaví","ensenada":"Puerto Varas","concon":"Concón","hualpen":"Hualpén","machali":"Machalí","pte alto":"Puente Alto",
 "sn bernardo":"San Bernardo","poblacion vergara":"Viña del Mar","olmue":"Olmué","quilpue":"Quilpué","calera":"La Calera","sector chamiza":"Puerto Montt","chamiza":"Puerto Montt",
 "coihaique":"Coyhaique","los angeles":"Los Ángeles","san pedro":"San Pedro de la Paz","chillan":"Chillán","copiapo":"Copiapó","curico":"Curicó","penalolen":"Peñalolén",
 "nunoa":"Ñuñoa","maipu":"Maipú","estacion central":"Estación Central","pudahuel":"Pudahuel","pucon":"Pucón","valparaiso":"Valparaíso","vina del mar":"Viña del Mar",
 "punta arenas":"Punta Arenas","barrio italia":"Providencia","el molle":"Vicuña","lenga":"Hualpén","placilla":"Valparaíso","la dehesa":"Lo Barnechea","pichidangui":"Los Vilos","la dehesa":"Lo Barnechea","el arrayan":"Lo Barnechea","huechuraba":"Huechuraba","providencia":"Providencia"}
for a, c in ALIAS.items():
    if nz(c) in CMAP: CMAP[a] = CMAP[nz(c)]
AMBIG={'florida','los lagos','maule','o higgins','arauco','cisnes','florida'}
KEYS = sorted([k for k in CMAP if k not in AMBIG], key=len, reverse=True)
EXCLUDE = re.compile(r"domino|dunkin|doggis|juan maestro|barrio chick|\bmamut\b|lovdo|\bkfc\b|wendy|mcdonald|burger king|china wok|tommy beans|starbucks|oakberry|rappi|pedidosya|uber eats|justo|club de restaurantes|cuponera|dolares|carl.?s jr|burger king|papa john", re.I)

def comuna_of(*texts):
    for t in texts:
        if not t: continue
        if nz(t) in CMAP and nz(t) not in AMBIG: return CMAP[nz(t)]
        t = re.sub(r'(?i)(mall|parque|outlet|premium outlet)\s+arauco|arauco\s+(premium|outlet|maip[uú]|chillan|quilicura|el bosque|estaci[oó]n)', lambda m: m.group(0).replace('Arauco','').replace('arauco',''), t)
        segs = [x for x in re.split(r',|–|\s-\s|\(|\)|\.\s', t) if x.strip()]
        order = [x for x in reversed(segs) if not re.search(r'\d', x)] + [x for x in reversed(segs) if re.search(r'\d', x)]
        hits = []
        for seg in order:
            n = ' ' + nz(seg) + ' '
            if nz(seg) in CMAP and nz(seg) not in AMBIG: hits.append(CMAP[nz(seg)]); continue
            for k in KEYS:
                if (' ' + k + ' ') in n: hits.append(CMAP[k]); break
        if hits:
            for h in hits:
                if h[0] != 'Santiago': return h
            return hits[0]
    return None

DAYS = ["lun","mar","mie","jue","vie","sab","dom"]
DN = {"lunes":0,"martes":1,"miercoles":2,"jueves":3,"viernes":4,"sabado":5,"domingo":6}
def parse_days(t):
    n = nz(t)
    if re.search(r'todos los dias|todos los d as|lunes a domingo|diario', n): return DAYS[:]
    m = re.search(r'(lunes|martes|miercoles|jueves|viernes|sabado|domingo)s? a (lunes|martes|miercoles|jueves|viernes|sabado|domingo)', n)
    if m:
        a, b = DN[m.group(1)], DN[m.group(2)]
        return DAYS[a:b+1] if a <= b else DAYS[a:] + DAYS[:b+1]
    found = sorted({DN[w] for w in re.findall(r'(lunes|martes|miercoles|jueves|viernes|sabado|domingo)', n)})
    return [DAYS[i] for i in found]
def days_text(ds):
    names = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    if len(ds) == 7: return "Todos los días"
    idx = [DAYS.index(d) for d in ds]
    if len(idx) > 2 and idx == list(range(idx[0], idx[-1]+1)): return f"{names[idx[0]]} a {names[idx[-1]].lower()}"
    if not idx: return "Consultar días"
    if len(idx) == 1: return names[idx[0]]
    parts = [names[idx[0]]] + [names[i].lower() for i in idx[1:]]
    return ", ".join(parts[:-1]) + " y " + parts[-1]
MES = {m: i+1 for i, m in enumerate(["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"])}
def parse_date(t):
    n = nz(t)
    m = re.search(r'(\d{1,2}) de (\w+) (?:de |del )?(\d{4})', n)
    if m and m.group(2) in MES: return f"{int(m.group(3)):04d}-{MES[m.group(2)]:02d}-{int(m.group(1)):02d}"
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', t or '')
    if m: return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', t or '')
    if m: return m.group(0)
    return None
def parse_tope(t):
    if re.search(r'sin tope', t or '', re.I): return "Sin tope"
    m = re.search(r'(?:tope|m[aá]ximo)[^$]{0,40}\$\s?([\d.]+)([^.;|]{0,22})', t or '', re.I)
    if not m: return "—"
    extra = m.group(2)
    suf = " por mesa" if 'mesa' in extra else (" al mes" if 'mens' in (t or '').lower()[m.start():m.end()+10] else "")
    return f"${m.group(1).rstrip('.')}{suf}"
def cat_of(name, hint=''):
    t = nz(name + ' ' + hint)
    for k, v in [("sushi","Sushi"),("nikkei","Nikkei"),("thai","Tailandesa"),("pizz","Pizzería"),("burger","Hamburguesas"),("hamburg","Hamburguesas"),("cafe","Café"),("coffee","Café"),
                 ("pastel","Pastelería"),("helad","Heladería"),("bar","Bar"),("brasa","Parrilla"),("parrill","Parrilla"),("asado","Parrilla"),("carne","Parrilla"),("steak","Parrilla"),
                 ("peru","Peruana"),("cevich","Peruana"),("mexic","Mexicana"),("taco","Mexicana"),("trattor","Italiana"),("pasta","Italiana"),("ital","Italiana"),("bistro","Bistró"),
                 ("marisc","Pescados y mariscos"),("pescad","Pescados y mariscos"),("mar ","Pescados y mariscos")]:
        if k in t: return v
    return "Restaurante"

items = []  # dicts with ciudad, region + item fields
def add(ciudad, region, **kw):
    if kw.get('vence') and kw['vence'] < TODAY.isoformat(): return
    if not kw.get('dcto'): return
    if EXCLUDE.search(kw['restaurante']): return
    kw['dias'] = kw.get('dias') or []
    kw.setdefault('diasTexto', days_text(kw['dias']))
    kw['id'] = slug(f"{kw['restaurante']}-{kw['banco']}-{kw['dcto']}-{''.join(kw['dias'])}-{ciudad}")[:120]
    kw.setdefault('verificado', True)
    items.append(dict(ciudad=ciudad, region=region, **kw))

