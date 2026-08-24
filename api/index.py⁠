from flask import Flask, request, jsonify
import swisseph as swe

app = Flask(__name__)

PLANETAS = {
    "Sol": swe.SUN,
    "Lua": swe.MOON,
    "Mercurio": swe.MERCURY,
    "Venus": swe.VENUS,
    "Marte": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturno": swe.SATURN,
    "Urano": swe.URANUS,
    "Netuno": swe.NEPTUNE,
    "Plutao": swe.PLUTO,
    "NodoNorte": swe.MEAN_NODE,
}

SIGNOS = [
    "Aries", "Touro", "Gemeos", "Cancer", "Leao", "Virgem",
    "Libra", "Escorpiao", "Sagitario", "Capricornio", "Aquario", "Peixes"
]


def signo_da_posicao(grau_absoluto):
    indice_signo = int(grau_absoluto // 30)
    grau_no_signo = grau_absoluto % 30
    return SIGNOS[indice_signo], round(grau_no_signo, 2)


def calcular_mapa(data, hora, lat, lon, fuso):
    ano, mes, dia = [int(x) for x in data.split("-")]
    h, m = [int(x) for x in hora.split(":")]
    hora_decimal = h + (m / 60.0)
    hora_ut = hora_decimal - fuso

    jd_ut = swe.julday(ano, mes, dia, hora_ut)
    flags = swe.FLG_MOSEPH

    planetas_resultado = {}
    for nome, codigo in PLANETAS.items():
        posicao, _ = swe.calc_ut(jd_ut, codigo, flags)
        grau_absoluto = posicao[0]
        signo, grau_no_signo = signo_da_posicao(grau_absoluto)
        planetas_resultado[nome] = {
            "grau_absoluto": round(grau_absoluto, 2),
            "signo": signo,
            "grau_no_signo": grau_no_signo,
            "retrogrado": posicao[3] < 0
        }

    cusps, ascmc = swe.houses(jd_ut, lat, lon, b'P')
    casas_resultado = {}
    for i, grau_absoluto in enumerate(cusps, start=1):
        signo, grau_no_signo = signo_da_posicao(grau_absoluto)
        casas_resultado[f"Casa{i}"] = {
            "grau_absoluto": round(grau_absoluto, 2),
            "signo": signo,
            "grau_no_signo": grau_no_signo
        }

    ascendente_signo, ascendente_grau = signo_da_posicao(ascmc[0])
    meio_ceu_signo, meio_ceu_grau = signo_da_posicao(ascmc[1])

    return {
        "sucesso": True,
        "planetas": planetas_resultado,
        "casas": casas_resultado,
        "ascendente": {"signo": ascendente_signo, "grau": ascendente_grau},
        "meio_ceu": {"signo": meio_ceu_signo, "grau": meio_ceu_grau}
    }


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/api/index', methods=['GET', 'OPTIONS'])
def index():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.args.get('data', '')
        hora = request.args.get('hora', '')
        lat = float(request.args.get('lat', '0'))
        lon = float(request.args.get('lon', '0'))
        fuso = float(request.args.get('fuso', '0'))

        resultado = calcular_mapa(data, hora, lat, lon, fuso)
        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 400
