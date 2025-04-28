import re
import pandas as pd
from utils.texto import limpar_texto

def formatar_periodo(periodo):
    if pd.isna(periodo):
        return None
    periodo = str(periodo).strip()
    if re.match(r"^\d{6}$", periodo):
        return f"{periodo[:2]}/{periodo[2:]}"
    elif re.match(r"^\d{2}/\d{2}/\d{4}$", periodo):
        partes = periodo.split("/")
        return f"{partes[1]}/{partes[2]}"
    elif re.match(r"^\d{4}$", periodo):
        return periodo
    return periodo

def mes_extenso_para_mes_ano(texto):
    mapa_meses = {
        "janeiro": "01", "fevereiro": "02", "marco": "03", "abril": "04",
        "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
        "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
    }
    texto = limpar_texto(texto)
    for nome, numero in mapa_meses.items():
        if nome in texto:
            ano = re.search(r"\d{4}", texto)
            if ano:
                return f"{numero}/{ano.group(0)}"
    return None

def extrair_chave_ordenacao(periodo):
    if pd.isna(periodo):
        return (9999, 99)
    match = re.match(r"^(\d{2})/(\d{4})$", str(periodo))
    if match:
        mes, ano = match.groups()
        return (int(ano), int(mes))
    elif re.match(r"^\d{4}$", str(periodo)):
        return (int(periodo), 1)
    return (9999, 99)