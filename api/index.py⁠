import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

SIGNOS = [
    "Áries", "Touro", "Gêmeos", "Câncer",
    "Leão", "Virgem", "Libra", "Escorpião",
    "Sagitário", "Capricórnio", "Aquário", "Peixes"
]

def extrair_posicao(long_graus):
    pos = long_graus % 360
    idx_signo = int(pos // 30)
    resto = pos % 30
    grau = int(resto)
    minuto = int((resto - grau) * 60)
    return SIGNOS[idx_signo], grau, minuto

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)

        data_str = query.get('data', ['1989-10-09'])[0]
        hora_str = query.get('hora', ['10:59'])[0]
        fuso_str = query.get('fuso', ['-3'])[0]
        lat_str = query.get('lat', ['-23.5505'])[0]
        lon_str = query.get('lon', ['-46.6333'])[0]

        linhas_tabela = ""
        
        try:
            import swisseph as swe
            ano, mes, dia = map(int, data_str.split('-'))
            hora, minuto = map(int, hora_str.split(':'))
            fuso = float(fuso_str)
            lat = float(lat_str)
            lon = float(lon_str)

            hora_utc = (hora + (minuto / 60.0)) - fuso
            jd_ut = swe.julday(ano, mes, dia, hora_utc)

            cusps, ascmc = swe.houses(jd_ut, lat, lon, b'P')

            corpos = [
                ("Ascendente (ASC)", ascmc[0], True),
                ("Meio do Céu (MC)", ascmc[1], True),
                ("Sol", swe.SE_SUN, False),
                ("Lua", swe.SE_MOON, False),
                ("Mercúrio", swe.SE_MERCURY, False),
                ("Vênus", swe.SE_VENUS, False),
                ("Marte", swe.SE_MARS, False),
                ("Júpiter", swe.SE_JUPITER, False),
                ("Saturno", swe.SE_SATURN, False),
                ("Nodo Norte", swe.SE_TRUE_NODE, False)
            ]

            for rotulo, p_id, eh_angulo in corpos:
                if eh_angulo:
                    long_g = p_id
                    retro = False
                else:
                    res, _ = swe.calc_ut(jd_ut, p_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
                    long_g = res[0]
                    retro = res[3] < 0

                signo, grau, min_arc = extrair_posicao(long_g)
                str_retro = " (R)" if retro else ""
                linhas_tabela += f"<tr><td style='color:#103b70;'>{rotulo}</td><td>{signo}</td><td>{grau}° {min_arc}′{str_retro}</td></tr>"

        except Exception as e:
            linhas_tabela = f"<tr><td colspan='3' style='color:red;'>Erro ao calcular: {str(e)}</td></tr>"

        html_resposta = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resultado Astrológico</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; padding: 15px; background: #f8fafc; color: #0f172a; }}
        .card {{ background: #ffffff; padding: 16px; border: 2px solid #d4af37; border-radius: 10px; max-width: 650px; margin-bottom: 15px; }}
        table {{ width: 100%; max-width: 650px; border-collapse: collapse; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }}
        th {{ background: #103b70; color: #ffffff; text-align: left; padding: 8px; font-size: 11px; text-transform: uppercase; }}
        td {{ padding: 8px; border-bottom: 1px solid #e2e8f0; font-size: 12px; font-weight: 600; }}
        .btn-voltar {{ display: inline-block; margin-top: 15px; padding: 10px 15px; background: #103b70; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 12px; }}
    </style>
</head>
<body>
    <h3 style="color: #103b70;">Resultado - Swiss Ephemeris</h3>
    <div class="card">
        <p style="font-size: 12px; margin: 0;"><b>Data:</b> {data_str} | <b>Hora:</b> {hora_str} | <b>Fuso:</b> UTC {fuso_str}</p>
        <p style="font-size: 12px; margin: 5px 0 0 0;"><b>Lat:</b> {lat_str} | <b>Lon:</b> {lon_str}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>Ponto / Planeta</th>
                <th>Signo</th>
                <th>Grau / Minuto</th>
            </tr>
        </thead>
        <tbody>
            {linhas_tabela}
        </tbody>
    </table>
    <a href="javascript:history.back()" class="btn-voltar">← Voltar para a Consulta</a>
</body>
</html>"""

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_resposta.encode('utf-8'))
