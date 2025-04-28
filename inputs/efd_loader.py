import streamlit as st
import pandas as pd

def carregar_e_processar_arquivos():
    uploaded_files = st.file_uploader(
        "Selecione um ou mais arquivos .txt",
        type=["txt"],
        accept_multiple_files=True
    )

    if not uploaded_files:
        return None, None

    dataframes = []

    for arquivo in uploaded_files:
        arquivo.seek(0)
        # lê todas as linhas do TXT
        linhas = arquivo.read().decode("latin1").splitlines()
        # divide por '|' e elimina o primeiro elemento vazio
        dados = [linha.strip().split("|")[1:] for linha in linhas if linha.startswith("|")]

        df = pd.DataFrame(dados)

        # ------ Nova lógica: extrai o período do registro 0000 ------
        # máscara para linha onde coluna 0 == "0000"
        mask = df[0] == "0000"
        if mask.any():
            # pega o valor da coluna 5 nessa linha
            periodo = df.loc[mask, 5].iloc[0]
        else:
            # se não encontrar, deixa como None ou você pode lançar erro
            periodo = None

        # adiciona colunas de controle
        df["PERIODO"] = periodo
        df["arquivo_origem"] = arquivo.name
        # ------------------------------------------------------------

        dataframes.append(df)

    # concatena tudo num único DataFrame
    df_final = pd.concat(dataframes, ignore_index=True)
    return uploaded_files, df_final
