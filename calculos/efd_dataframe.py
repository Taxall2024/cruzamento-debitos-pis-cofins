import streamlit as st
from modulos.processador import carregar_e_processar_arquivos

st.set_page_config(page_title="Tabulador Consolidado TXT", layout="wide")
st.title("Consolidador de Arquivos .TXT com separador |")

uploaded_files, df_consolidado = carregar_e_processar_arquivos()

if uploaded_files and df_consolidado is not None:
    st.success(f"{df_consolidado['arquivo_origem'].nunique()} arquivos consolidados com sucesso.")
    st.subheader("Tabela Consolidada")
    st.dataframe(df_consolidado.head(200))

    from io import BytesIO
    buffer = BytesIO()
    df_consolidado.to_excel(buffer, index=False, sheet_name="Consolidado")
    buffer.seek(0)

    st.download_button(
        label="Baixar Tabela Consolidada em Excel",
        data=buffer,
        file_name="tabela_consolidada.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Carregue um ou mais arquivos .txt com separador | para gerar a tabela consolidada.")
