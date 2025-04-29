import pandas as pd
from utils.formatadores import mes_extenso_para_mes_ano

def carregar_xlsx(uploaded_xlsx):
    if not uploaded_xlsx:
        return None
    try:
        df = pd.read_excel(uploaded_xlsx)
        col_periodos = [col for col in df.columns if col.lower().startswith("periodo_apuracao")]
        col_valores = [col for col in df.columns if col.lower().startswith("valor_principal_tributo")]
        if col_periodos and col_valores:
            df["_periodos_convertidos"] = df[col_periodos[0]].apply(mes_extenso_para_mes_ano)
            df[col_valores] = df[col_valores].replace(',', '.', regex=True)
            df[col_valores] = df[col_valores].apply(pd.to_numeric, errors='coerce')
        return df
    except Exception as e:
        return None