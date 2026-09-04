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

# FLG_SPEED faz a Swiss Ephemeris calcular a velocidade do planeta,
# necessária para saber se ele está retrógrado (velocidade negativa).
FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED


def signo_da_posicao(grau_absoluto):
    indice_signo = int(grau_absoluto // 30)
    grau_no_signo = grau_absoluto % 30
    return SIGNOS[indice_signo], round(grau_no_signo, 2)


def calcular_jd_ut(data, hora, fuso):
    ano, mes, dia = [int(x) for x in data.split("-")]
    h, m = [int(x) for x in hora.split(":")]
    hora_decimal = h + (m / 60.0)
    hora_ut = hora_decimal - fuso
    jd_ut = swe.julday(ano, mes, dia, hora_ut)
    return jd_ut, ano, mes, dia


def planetas_e_casas(jd_ut, lat, lon):
    planetas_resultado = {}
    for nome, codigo in PLANETAS.items():
        posicao, _ = swe.calc_ut(jd_ut, codigo, FLAGS)
        grau_absoluto = posicao[0]
        velocidade = posicao[3]
        signo, grau_no_signo = signo_da_posicao(grau_absoluto)
        planetas_resultado[nome] = {
            "grau_absoluto": round(grau_absoluto, 2),
            "signo": signo,
            "grau_no_signo": grau_no_signo,
            "retrogrado": velocidade < 0
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

    return (
        planetas_resultado,
        casas_resultado,
        {"signo": ascendente_signo, "grau": ascendente_grau},
        {"signo": meio_ceu_signo, "grau": meio_ceu_grau}
    )


def longitude_corpo(jd_ut, corpo):
    posicao, _ = swe.calc_ut(jd_ut, corpo, swe.FLG_MOSEPH)
    return posicao[0]


def sizigia_pre_natal(jd_nascimento):
    """Encontra a última Lua Nova ou Lua Cheia antes do nascimento."""
    sol_nasc = longitude_corpo(jd_nascimento, swe.SUN)
    lua_nasc = longitude_corpo(jd_nascimento, swe.MOON)
    fase = (lua_nasc - sol_nasc) % 360
    alvo = 0.0 if fase < 180 else 180.0
    tipo = "Lua Nova" if alvo == 0.0 else "Lua Cheia"

    def diferenca_sinalizada(jd):
        sol = longitude_corpo(jd, swe.SUN)
        lua = longitude_corpo(jd, swe.MOON)
        diff = (lua - sol) % 360
        return ((diff - alvo + 180) % 360) - 180

    lo = jd_nascimento - 20
    hi = jd_nascimento
    if diferenca_sinalizada(lo) > 0:
        lo = jd_nascimento - 32

    for _ in range(60):
        meio = (lo + hi) / 2
        if diferenca_sinalizada(meio) > 0:
            hi = meio
        else:
            lo = meio

    jd_sizigia = (lo + hi) / 2
    grau_absoluto = longitude_corpo(jd_sizigia, swe.MOON)
    signo, grau_no_signo = signo_da_posicao(grau_absoluto)

    return {
        "tipo": tipo,
        "grau_absoluto": round(grau_absoluto, 2),
        "signo": signo,
        "grau_no_signo": grau_no_signo,
        "jd_ut": round(jd_sizigia, 5)
    }


def calcular_mapa_natal(data, hora, lat, lon, fuso):
    jd_ut, ano, mes, dia = calcular_jd_ut(data, hora, fuso)
    planetas_resultado, casas_resultado, ascendente, meio_ceu = planetas_e_casas(jd_ut, lat, lon)
    sizigia = sizigia_pre_natal(jd_ut)

    return {
        "sucesso": True,
        "planetas": planetas_resultado,
        "casas": casas_resultado,
        "ascendente": ascendente,
        "meio_ceu": meio_ceu,
        "sizigia": sizigia
    }


def calcular_revolucao_solar(data_nasc, hora_nasc, lat_nasc, lon_nasc, fuso_nasc,
                              ano_alvo, lat_sr, lon_sr, fuso_sr):
    jd_natal, ano_nasc, mes_nasc, dia_nasc = calcular_jd_ut(data_nasc, hora_nasc, fuso_nasc)
    sol_natal = longitude_corpo(jd_natal, swe.SUN)
    sizigia = sizigia_pre_natal(jd_natal)

    jd_inicio_busca = swe.julday(ano_alvo, mes_nasc, dia_nasc, 0) - 2
    jd_retorno = swe.solcross_ut(sol_natal, jd_inicio_busca, swe.FLG_MOSEPH)

    planetas_resultado, casas_resultado, ascendente, meio_ceu = planetas_e_casas(jd_retorno, lat_sr, lon_sr)

    ano_r, mes_r, dia_r, hora_ut_decimal = swe.revjul(jd_retorno)
    hora_local_decimal = hora_ut_decimal + fuso_sr
    h_local = int(hora_local_decimal) % 24
    m_local = int(round((hora_local_decimal - int(hora_local_decimal)) * 60))

    return {
        "sucesso": True,
        "momento_exato": {
            "data_utc": f"{ano_r:04d}-{mes_r:02d}-{dia_r:02d}",
            "hora_utc": round(hora_ut_decimal, 4),
            "hora_local": f"{h_local:02d}:{m_local:02d}"
        },
        "planetas": planetas_resultado,
        "casas": casas_resultado,
        "ascendente": ascendente,
        "meio_ceu": meio_ceu,
        "sizigia": sizigia
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

        resultado = calcular_mapa_natal(data, hora, lat, lon, fuso)
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 400


@app.route('/api/revolucao', methods=['GET', 'OPTIONS'])
def revolucao():
    if request.method == 'OPTIONS':
        return '', 204
    try:
        data = request.args.get('data', '')
        hora = request.args.get('hora', '')
        lat = float(request.args.get('lat', '0'))
        lon = float(request.args.get('lon', '0'))
        fuso = float(request.args.get('fuso', '0'))
        ano = int(request.args.get('ano', '0'))

        # Coordenadas do local do aniversário (se não vierem, usa as de nascimento)
        lat_sr = float(request.args.get('lat_sr', lat))
        lon_sr = float(request.args.get('lon_sr', lon))
        fuso_sr = float(request.args.get('fuso_sr', fuso))

        resultado = calcular_revolucao_solar(
            data, hora, lat, lon, fuso, ano, lat_sr, lon_sr, fuso_sr
        )
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 400
