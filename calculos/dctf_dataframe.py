import pandas as pd
from .dctf_layouts import LAYOUTS_COMPLETOS

def parse_registro(linha, layout):
    return {campo: linha[ini - 1:fim].strip() for campo, ini, fim in layout}

def gerar_dataframes(conteudos):
    registros_por_tipo = {k: [] for k in LAYOUTS_COMPLETOS}
    for nome, linhas in conteudos:
        for linha in linhas:
            tipo = linha[:3].strip()
            if tipo in LAYOUTS_COMPLETOS:
                registro = parse_registro(linha, LAYOUTS_COMPLETOS[tipo])
                registro["ArquivoOrigem"] = nome
                registros_por_tipo[tipo].append(registro)

    tabelas = {}
    for tipo, layout in LAYOUTS_COMPLETOS.items():
        colunas = [campo for campo, _, _ in layout] + ["ArquivoOrigem"]
        df = pd.DataFrame(registros_por_tipo[tipo] or [{}])
        for col in colunas:
            if col not in df.columns:
                df[col] = ""
        tabelas[tipo] = df[colunas]
    return tabelas
