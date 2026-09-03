#!/usr/bin/env python3
"""
Gera dash.png (1072x1448, 8-bit grayscale) com a previsao do tempo.
Feito para rodar no GitHub Actions e commitar a imagem no repositorio.

Resolucao alvo: Kindle Paperwhite 3 (300 ppi).
Para PW2 (212 ppi) troque LARGURA/ALTURA para 758/1024.

Requisitos: pip install pillow requests
"""

import math
import sys
import time
from datetime import datetime, timezone, timedelta

import requests
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------- CONFIGURACAO

LATITUDE = -23.0903            # Indaiatuba - SP
LONGITUDE = -47.2181
CIDADE = "INDAIATUBA - SP"
TZ_NOME = "America/Sao_Paulo"
TZ_OFFSET = -3                 # apenas para o relogio do cabecalho

LARGURA = 1072                 # PW3. Use 758 para PW2.
ALTURA = 1448                  # PW3. Use 1024 para PW2.

SAIDA = "dash.png"

# Fontes do runner ubuntu-latest do GitHub Actions
FONTE_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONTE_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

ESCALA = LARGURA / 758.0       # layout foi desenhado em 758 de largura

# ------------------------------------------------------------------- UTILIDADES


def px(v):
    """Escala um valor do layout base para a resolucao atual."""
    return int(round(v * ESCALA))


def fonte(caminho, tamanho_base):
    try:
        return ImageFont.truetype(caminho, px(tamanho_base))
    except OSError:
        return ImageFont.load_default()


CODIGOS = {
    0: "Ceu limpo", 1: "Predom. limpo", 2: "Parc. nublado", 3: "Nublado",
    45: "Nevoeiro", 48: "Nevoeiro gelado", 51: "Garoa leve", 53: "Garoa",
    55: "Garoa forte", 56: "Garoa gelada", 57: "Garoa gelada",
    61: "Chuva leve", 63: "Chuva", 65: "Chuva forte",
    66: "Chuva gelada", 67: "Chuva gelada",
    71: "Neve leve", 73: "Neve", 75: "Neve forte", 77: "Granizo fino",
    80: "Pancadas", 81: "Pancadas", 82: "Pancadas fortes",
    85: "Pancada de neve", 86: "Pancada de neve",
    95: "Tempestade", 96: "Tempestade granizo", 99: "Tempestade granizo",
}


def buscar_clima():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": ("temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "precipitation,wind_speed_10m,wind_direction_10m,weather_code"),
        "daily": ("temperature_2m_max,temperature_2m_min,"
                  "apparent_temperature_max,apparent_temperature_min,"
                  "precipitation_sum,precipitation_probability_max,"
                  "wind_speed_10m_max,wind_gusts_10m_max,"
                  "sunrise,sunset,weather_code"),
        "hourly": "temperature_2m,weather_code",
        "timezone": TZ_NOME,
        "forecast_days": 4,
    }
    # A API do Open-Meteo devolve 500 esporadicamente. Tenta algumas vezes
    # com espera crescente antes de desistir.
    esperas = [5, 15, 30, 60]
    ultimo_erro = None
    for tentativa, espera in enumerate(esperas + [None], start=1):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code >= 500:
                raise requests.HTTPError(
                    f"{r.status_code} Server Error para {r.url}", response=r)
            r.raise_for_status()
            return r.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            ultimo_erro = e
            if espera is None:
                break
            print(f"AVISO: tentativa {tentativa} falhou ({e}); "
                  f"nova tentativa em {espera}s", file=sys.stderr)
            time.sleep(espera)
    raise RuntimeError(f"Open-Meteo indisponivel apos {len(esperas) + 1} "
                       f"tentativas: {ultimo_erro}")


def rosa_dos_ventos(graus):
    pontos = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
    return pontos[int((graus + 11.25) % 360 // 22.5)]


# ---------------------------------------------------------------------- ICONES


def ic_sol(d, cx, cy, r, tom=0):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tom)
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        d.line([cx + int((r + r * 0.28) * math.cos(rad)),
                cy + int((r + r * 0.28) * math.sin(rad)),
                cx + int((r + r * 0.62) * math.cos(rad)),
                cy + int((r + r * 0.62) * math.sin(rad))],
               fill=tom, width=max(2, int(r * 0.17)))


def ic_lua(d, cx, cy, r, tom=110):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tom)
    d.ellipse([cx - r + int(r * 0.55), cy - r - int(r * 0.2),
               cx + r + int(r * 0.55), cy + r - int(r * 0.2)], fill=255)
    for dx, dy, s in ((r + r * 0.4, -r, r * 0.18),
                      (r + r * 0.8, -r + r * 0.7, r * 0.13)):
        d.ellipse([cx + dx - s, cy + dy - s, cx + dx + s, cy + dy + s], fill=tom)


def ic_nuvem(d, cx, cy, r, tom=120):
    d.ellipse([cx - r, cy, cx + int(r * 0.15), cy + int(r * 0.78)], fill=tom)
    d.ellipse([cx - int(r * 0.35), cy - int(r * 0.3), cx + r, cy + int(r * 0.78)], fill=tom)
    d.rectangle([cx - r, cy + int(r * 0.3), cx + r, cy + int(r * 0.78)], fill=tom)


def ic_chuva(d, cx, cy, r):
    ic_nuvem(d, cx, cy - int(r * 0.25), r, tom=95)
    for i in range(3):
        x = cx - int(r * 0.55) + i * int(r * 0.55)
        d.line([x, cy + int(r * 0.62), x - int(r * 0.2), cy + int(r * 1.25)],
               fill=0, width=max(2, int(r * 0.14)))


def desenhar_icone(d, cx, cy, r, codigo, noite=False):
    if codigo in (0, 1):
        ic_lua(d, cx, cy, r) if noite else ic_sol(d, cx, cy, r)
    elif codigo in (2,):
        ic_nuvem(d, cx, cy - int(r * 0.1), r, tom=140)
        if noite:
            ic_lua(d, cx + int(r * 0.5), cy - int(r * 0.7), int(r * 0.5))
        else:
            ic_sol(d, cx + int(r * 0.55), cy - int(r * 0.65), int(r * 0.42), tom=60)
    elif codigo in (3, 45, 48):
        ic_nuvem(d, cx, cy, r, tom=110)
    else:
        ic_chuva(d, cx, cy, r)


# --------------------------------------------------------------------- DESENHO


def gerar():
    dados = buscar_clima()
    atual = dados["current"]
    dia = dados["daily"]
    horas = dados["hourly"]

    img = Image.new("L", (LARGURA, ALTURA), 255)
    d = ImageDraw.Draw(img)

    f_cidade = fonte(FONTE_BOLD, 34)
    f_hdr = fonte(FONTE_REG, 18)
    f_temp = fonte(FONTE_BOLD, 150)
    f_grau = fonte(FONTE_BOLD, 46)
    f_cond = fonte(FONTE_BOLD, 30)
    f_rot = fonte(FONTE_BOLD, 22)
    f_val = fonte(FONTE_BOLD, 34)
    f_val_sm = fonte(FONTE_BOLD, 26)
    f_faixa = fonte(FONTE_REG, 20)

    # ---- cabecalho
    d.text((px(32), px(26)), CIDADE, font=f_cidade, fill=0)
    agora = datetime.now(timezone(timedelta(hours=TZ_OFFSET)))
    selo = agora.strftime("%d/%m  %H:%M")
    d.text((LARGURA - px(32) - d.textlength(selo, font=f_hdr), px(38)),
           selo, font=f_hdr, fill=100)
    d.line([px(32), px(78), LARGURA - px(32), px(78)], fill=0, width=px(3))

    # ---- bloco principal
    temp = round(atual["temperature_2m"])
    d.text((px(38), px(96)), str(temp), font=f_temp, fill=0)
    w = d.textlength(str(temp), font=f_temp)
    d.text((px(38) + w + px(8), px(122)), "o", font=f_grau, fill=0)

    cod_atual = atual["weather_code"]
    d.text((px(40), px(268)), CODIGOS.get(cod_atual, "--"), font=f_cond, fill=0)
    d.text((px(40), px(306)),
           f"Sensacao {round(atual['apparent_temperature'])}o", font=f_faixa, fill=95)

    hora_local = agora.hour
    desenhar_icone(d, LARGURA - px(140), px(190), px(58), cod_atual,
                   noite=(hora_local < 6 or hora_local >= 18))

    # ---- faixas do dia
    d.line([px(32), px(356), LARGURA - px(32), px(356)], fill=185, width=px(2))
    faixas = [("Madrugada", 3), ("Manha", 9), ("Tarde", 15), ("Noite", 21)]
    passo = (LARGURA - px(64)) // 4
    for i, (nome, h) in enumerate(faixas):
        cx = px(32) + passo * i + passo // 2
        cod = horas["weather_code"][h]
        t = horas["temperature_2m"][h]
        desenhar_icone(d, cx, px(408), px(30), cod, noite=(h < 6 or h >= 18))
        nw = d.textlength(nome, font=f_faixa)
        d.text((cx - nw / 2, px(452)), nome, font=f_faixa, fill=95)
        tt = f"{round(t)}o"
        tw = d.textlength(tt, font=f_cond)
        d.text((cx - tw / 2, px(474)), tt, font=f_cond, fill=0)

    # ---- painel de detalhes
    PY = px(520)
    PH = px(330)
    d.rounded_rectangle([px(32), PY, LARGURA - px(32), PY + PH],
                        radius=px(18), fill=246, outline=205, width=px(2))
    meio = LARGURA // 2
    d.line([meio, PY + px(22), meio, PY + PH - px(22)], fill=212, width=px(2))

    esq = px(58)
    dire = meio + px(26)
    linhas = [PY + px(20), PY + px(103), PY + px(186), PY + px(269)]
    for y in linhas[1:]:
        d.line([px(54), y - px(14), LARGURA - px(54), y - px(14)], fill=212, width=px(2))

    def campo(x, y, rotulo, v1, v2=None, f=f_val):
        d.text((x, y), rotulo, font=f_rot, fill=25)
        if v2:
            d.text((x, y + px(32)), v1, font=f, fill=95)
            wv = d.textlength(v1, font=f)
            d.text((x + wv + px(20), y + px(32)), v2, font=f, fill=0)
        else:
            d.text((x, y + px(32)), v1, font=f, fill=0)

    campo(esq, linhas[0], "Temperatura",
          f"{round(dia['temperature_2m_min'][0])}o", f"{round(dia['temperature_2m_max'][0])}o")
    campo(dire, linhas[0], "Sensacao termica",
          f"{round(dia['apparent_temperature_min'][0])}o",
          f"{round(dia['apparent_temperature_max'][0])}o")

    campo(esq, linhas[1], "Chuva",
          f"{dia['precipitation_sum'][0]:.1f} mm  ({dia['precipitation_probability_max'][0]}%)",
          None, f_val_sm)
    campo(dire, linhas[1], "Umidade do ar",
          f"{round(atual['relative_humidity_2m'])}%")

    dir_vento = rosa_dos_ventos(atual["wind_direction_10m"])
    campo(esq, linhas[2], "Vento",
          f"{dir_vento} {round(dia['wind_speed_10m_max'][0])} km/h", None, f_val_sm)
    campo(dire, linhas[2], "Rajada de vento",
          f"{round(dia['wind_gusts_10m_max'][0])} km/h", None, f_val_sm)

    campo(esq, linhas[3], "Nascer do sol", dia["sunrise"][0][-5:], None, f_val_sm)
    campo(dire, linhas[3], "Por do sol", dia["sunset"][0][-5:], None, f_val_sm)

    # ---- proximos dias
    Y1 = PY + PH + px(24)
    d.line([px(32), Y1, LARGURA - px(32), Y1], fill=185, width=px(2))
    semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
    passo3 = (LARGURA - px(64)) // 3
    for i in range(1, 4):
        cx = px(32) + passo3 * (i - 1) + passo3 // 2
        data = datetime.strptime(dia["time"][i], "%Y-%m-%d")
        nome = semana[data.weekday()]
        nw = d.textlength(nome, font=f_rot)
        d.text((cx - nw / 2, Y1 + px(6)), nome, font=f_rot, fill=90)
        desenhar_icone(d, cx, Y1 + px(64), px(23), dia["weather_code"][i])
        faixa = f"{round(dia['temperature_2m_min'][i])}o {round(dia['temperature_2m_max'][i])}o"
        fw = d.textlength(faixa, font=f_cond)
        d.text((cx - fw / 2, Y1 + px(98)), faixa, font=f_cond, fill=0)

    img.convert("L").save(SAIDA, format="PNG", optimize=True)
    print(f"{SAIDA} gerado: {LARGURA}x{ALTURA}, temp {temp}o")


if __name__ == "__main__":
    try:
        gerar()
    except RuntimeError as e:
        # API fora do ar mesmo apos as retentativas: mantem o dash.png
        # anterior e nao marca o workflow como falho.
        print(f"AVISO: {e}. Mantendo a imagem anterior.", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)
