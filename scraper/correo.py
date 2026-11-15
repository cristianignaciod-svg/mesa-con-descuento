"""Genera el correo mensual (solo tablas de detalle de Puerto Varas y Puerto Montt) desde datos.json.
Salida: correo.html, correo.txt y asunto.txt en la carpeta actual."""
import json, html, os, datetime
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, "datos.json")))
hoy = datetime.datetime.now(ZoneInfo("America/Santiago")).date()
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
MES_ANO = f"{MESES[hoy.month-1]} {hoy.year}"
SITIO = "https://mesa-con-descuento.netlify.app"
CIUDADES = ["Puerto Varas", "Puerto Montt"]
COLOR = {"Banco de Chile":"#1f4e8c","Santander":"#e3001b","Scotiabank":"#ec111a","BancoEstado":"#f39200","BICE":"#2a7ab0","Ripley":"#5c2d91",
         "Banco Falabella":"#2c8a3a","BCI":"#f7a600","Security":"#6b2c91","Itaú":"#ec7000","Tarjeta Vecino Coyhaique":"#0f766e"}
DOW = ["lun","mar","mie","jue","vie","sab","dom"]
e = html.escape

def vig(v):
    if not v: return "sin fecha"
    y, m, dd = v.split("-")
    s = f"{int(dd)} {MESES[int(m)-1][:3]}"
    return s if int(y) == hoy.year else f"{s} {y}"

def filas(ciudad):
    c = next((x for x in d["ciudades"] if x["ciudad"] == ciudad), None)
    its = [i for i in (c["items"] if c else []) if not i.get("vence") or i["vence"] >= hoy.isoformat()]
    its.sort(key=lambda i: (-i["dcto"], DOW.index(i["dias"][0]) if i["dias"] else 9, i["restaurante"]))
    return its

def tabla(ciudad):
    rows = ""
    for n, x in enumerate(filas(ciudad)):
        bg = "#f7f9fb" if n % 2 else "#ffffff"
        col = COLOR.get(x["banco"], "#0f3d3e")
        pill = (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
                f'<td bgcolor="{col}" align="center" style="background-color:{col};color:#ffffff;padding:4px 10px;border-radius:10px;font-family:Arial,sans-serif;font-size:13px;font-weight:bold;white-space:nowrap">{x["dcto"]}%</td></tr></table>')
        dirn = x["direccion"] if x["direccion"] != ciudad else ""
        rows += (f'<tr bgcolor="{bg}" style="background-color:{bg}"><td style="padding:7px 8px">{pill}</td>'
                 f'<td style="padding:7px 8px;font:13px Arial;color:#111"><b>{e(x["restaurante"])}</b>' + (f'<br><span style="color:#777;font-size:11px">{e(dirn)}</span>' if dirn else '') + '</td>'
                 f'<td style="padding:7px 8px;font:13px Arial;color:#333">{e(x["diasTexto"])}</td>'
                 f'<td style="padding:7px 8px;font:13px Arial;color:#333"><b>{e(x["banco"])}</b><br><span style="color:#777;font-size:11px">{e(x["tarjetas"])}</span></td>'
                 f'<td style="padding:7px 8px;font:12px Arial;color:#333">{e(x["tope"])}<br><span style="color:#999;font-size:11px">hasta {e(vig(x.get("vence")))}</span></td></tr>')
    if not rows:
        rows = '<tr><td colspan="5" style="padding:10px;font:13px Arial;color:#777">Sin descuentos vigentes este mes.</td></tr>'
    head = ''.join(f'<th align="left" bgcolor="#0f3d3e" style="background-color:#0f3d3e;padding:7px 8px;font:bold 12px Arial;color:#fff">{h}</th>' for h in ["Dcto.", "Restaurante", "Día", "Banco / tarjeta", "Tope"])
    return f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse"><tr bgcolor="#0f3d3e" style="background-color:#0f3d3e">{head}</tr>{rows}</table>'

def seccion(t, inner):
    return (f'<tr><td style="padding:22px 24px 6px"><h2 style="margin:0;font:bold 18px Arial;color:#0f3d3e">{t}</h2></td></tr>'
            f'<tr><td style="padding:8px 24px">{inner}</td></tr>')

nota = d["meta"].get("nota") or ""
html_out = f'''<!doctype html><html><body style="margin:0;background-color:#eef3f3">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#eef3f3" style="background-color:#eef3f3"><tr><td align="center" style="padding:20px 8px">
<table role="presentation" width="680" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="max-width:680px;background-color:#ffffff;border-radius:10px;overflow:hidden">
<tr><td bgcolor="#0f3d3e" style="background-color:#0f3d3e;padding:26px 24px">
<div style="font:12px Arial;color:#9fd3cf;letter-spacing:1px">{MES_ANO.upper()}</div>
<h1 style="margin:6px 0 0;font:bold 24px Arial;color:#ffffff">Descuentos en restaurantes con tarjetas</h1>
<div style="font:14px Arial;color:#d6ecea;margin-top:6px">Puerto Varas y Puerto Montt · detalle por restaurante</div></td></tr>
{"".join(seccion("Detalle · " + c, tabla(c)) for c in CIUDADES)}
<tr><td style="padding:16px 24px 24px;font:12px Arial;color:#777">{e(nota) + "<br>" if nota else ""}Todas las ciudades de Chile en <a href="{SITIO}" style="color:#0f766e">{SITIO.replace("https://", "")}</a>. Los beneficios pueden cambiar; confirma en la app o sitio de tu banco antes de ir.</td></tr>
</table></td></tr></table></body></html>'''
open("correo.html", "w").write(html_out)
plain = [f"Descuentos en restaurantes - Puerto Varas y Puerto Montt ({MES_ANO})", ""]
for c in CIUDADES:
    plain.append(c.upper())
    for x in filas(c):
        plain.append(f"- {x['dcto']}% {x['restaurante']} | {x['diasTexto']} | {x['banco']}: {x['tarjetas']} | tope {x['tope']} | hasta {vig(x.get('vence'))}")
    plain.append("")
plain.append(f"Todas las ciudades: {SITIO}")
open("correo.txt", "w").write("\n".join(plain))
open("asunto.txt", "w").write(f"Descuentos en restaurantes · Puerto Varas y Puerto Montt · {MES_ANO}")
print("ok", len(html_out), {c: len(filas(c)) for c in CIUDADES})
