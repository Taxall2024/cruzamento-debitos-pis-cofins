import streamlit as st
import pandas as pd
import re
from inputs.efd_loader import carregar_e_processar_arquivos
from inputs.dctf_loader import carregar_arquivos as carregar_dctf
from inputs.darf_loader import carregar_darfs
from inputs.perdcomp_loader import carregar_xlsx
from calculos.resumo import gerar_df_resumo
from calculos.dctf_dataframe import gerar_dataframes as gerar_dctf_dfs

st.title("Cruzamento de Débitos de PIS e COFINS")

# Função para remover caracteres ilegais

def remove_illegal_chars(val):
    if isinstance(val, str):
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', val)
    return val

# 1) EFD (SPED txt)
uploaded_efd_files, df_efd = carregar_e_processar_arquivos()
if df_efd is not None:
    df_efd = df_efd.applymap(remove_illegal_chars)
    st.subheader("Dados EFD")
    st.dataframe(df_efd)

# 2) DCTF (.dec)
uploaded_dctf = st.file_uploader(
    "Escolha arquivos DCTF (.dec)",
    type="dec",
    accept_multiple_files=True
)
df_dctf = pd.DataFrame()
if uploaded_dctf:
    raw_dctf = carregar_dctf(uploaded_dctf)
    dfs = gerar_dctf_dfs(raw_dctf)
    df_dctf = pd.concat(dfs.values(), ignore_index=True)
    df_dctf = df_dctf.applymap(remove_illegal_chars)
    st.subheader("Dados DCTF")
    st.dataframe(df_dctf)

# 3) DARF (PDF)
uploaded_pdfs = st.file_uploader(
    "Escolha arquivos PDF de DARF",
    type="pdf",
    accept_multiple_files=True
)
df_darf = carregar_darfs(uploaded_pdfs) if uploaded_pdfs else None
if df_darf is not None:
    df_darf = df_darf.applymap(remove_illegal_chars)
    st.subheader("Dados DARF")
    st.dataframe(df_darf)

# 4) PER/DCOMP (XLSX)
uploaded_xlsx = st.file_uploader(
    "Escolha planilha XLSX de PER/DCOMP",
    type="xlsx",
    accept_multiple_files=False
)
df_perdcomp = carregar_xlsx(uploaded_xlsx) if uploaded_xlsx else None
if df_perdcomp is not None:
    df_perdcomp = df_perdcomp.applymap(remove_illegal_chars)
    st.subheader("Dados PER/DCOMP")
    st.dataframe(df_perdcomp)

# 5) Gerar e exibir resumo consolidado
# Resumo roda com EFD, DCTF e DARF; PER/DCOMP continua opcional
if df_efd is None or df_dctf is None or df_darf is None:
    st.info("Carregue EFD, DCTF e DARF para gerar o resumo.")
else:
    df_resumo = gerar_df_resumo(df_efd, df_dctf, df_darf, df_perdcomp)
    if df_resumo is None or df_resumo.empty:
        st.warning("Resumo consolidado vazio.")
    else:
        st.subheader("Resumo Consolidado")
        st.dataframe(df_resumo)

        # Exibir total de divergência EFD (PIS + COFINS)
        total_pis = df_resumo.loc[df_resumo['PERIODO'] == 'TOTAL', '[DIVERGÊNCIA EFD] PIS'].iloc[0]
        total_cof = df_resumo.loc[df_resumo['PERIODO'] == 'TOTAL', '[DIVERGÊNCIA EFD] COFINS'].iloc[0]
        total_divergencia = total_pis + total_cof
        st.metric("Divergência EFD Total (PIS + COFINS)", f"R$ {total_divergencia:,.2f}")

        # Botão para download do Excel com abas completas
        excel_filename = "resumo_cruzamento.xlsx"
        with pd.ExcelWriter(excel_filename) as writer:
            df_efd.to_excel(writer, sheet_name='Dados EFD', index=False)
            df_dctf.to_excel(writer, sheet_name='Dados DCTF', index=False)
            df_darf.to_excel(writer, sheet_name='Dados DARF', index=False)
            if df_perdcomp is not None:
                df_perdcomp.to_excel(writer, sheet_name='Dados PERDCOMP', index=False)
            df_resumo.to_excel(writer, sheet_name='Resumo Consolidado', index=False)

        with open(excel_filename, "rb") as file:
            st.download_button(
                label="Baixar Excel",
                data=file,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
