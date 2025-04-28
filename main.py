import streamlit as st
import pandas as pd
from inputs.efd_loader import carregar_e_processar_arquivos
from inputs.dctf_loader import carregar_arquivos as carregar_dctf
from inputs.darf_loader import carregar_darfs
from inputs.perdcomp_loader import carregar_xlsx
from calculos import gerar_df_resumo
from calculos.dctf_dataframe import gerar_dataframes as gerar_dctf_dfs

st.title("Cruzamento de Débitos de PIS e COFINS")

# 1) EFD (SPED txt)
uploaded_efd_files, df_efd = carregar_e_processar_arquivos()
if df_efd is not None:
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
    conteudos_dctf = carregar_dctf(uploaded_dctf)
    tabelas_dctf = gerar_dctf_dfs(conteudos_dctf)
    df_dctf = pd.concat(tabelas_dctf.values(), ignore_index=True)
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
    st.subheader("Dados DARF")
    st.dataframe(df_darf)

# 4) PER/DCOMP (XLSX)
uploaded_xlsx = st.file_uploader(
    "Escolha uma planilha XLSX de PER/DCOMP",
    type="xlsx",
    accept_multiple_files=False
)
df_perdcomp = carregar_xlsx(uploaded_xlsx) if uploaded_xlsx else None
if df_perdcomp is not None:
    st.subheader("Dados PER/DCOMP")
    st.dataframe(df_perdcomp)

# 5) Gerar e exibir resumo consolidado
df_resumo = gerar_df_resumo(df_efd, df_dctf, df_darf, df_perdcomp)
if df_resumo is not None and not df_resumo.empty:
    st.subheader("Resumo Consolidado")
    st.dataframe(df_resumo)

    # Exportar para Excel
    excel_filename = "resumo_cruzamento.xlsx"
    with pd.ExcelWriter(excel_filename) as writer:
        if df_efd is not None:
            df_efd.to_excel(writer, sheet_name='Dados EFD', index=False)
        if not df_dctf.empty:
            df_dctf.to_excel(writer, sheet_name='Dados DCTF', index=False)
        if df_darf is not None:
            df_darf.to_excel(writer, sheet_name='Dados DARF', index=False)
        if df_perdcomp is not None:
            df_perdcomp.to_excel(writer, sheet_name='Planilha Importada', index=False)
        df_resumo.to_excel(writer, sheet_name='Resumo', index=False)

    with open(excel_filename, "rb") as file:
        st.download_button(
            label="Baixar Excel",
            data=file,
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Carregue todos os arquivos necessários para gerar o resumo.")
