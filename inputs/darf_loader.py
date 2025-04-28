import pandas as pd
import pdfplumber
import re

def extrair_dados_darf(comprovante):
    regex = {
        'CNPJ_Razao': r'(?P<CNPJ>\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\s+(?P<RazaoSocial>[^\n]+)',
        'Periodo_Documento': r'(?P<PeriodoApuracao>\d{2}/\d{2}/\d{4})\s+(?P<DataVencimento>\d{2}/\d{2}/\d{4})\s+(?P<NumeroDocumento>\d{14,})',
        'Banco_Data_Arrecadacao': r'(?P<DataArrecadacao>\d{2}/\d{2}/\d{4})\s+(?P<Banco>\d{3}\s*-\s*[^\n]+)',
        'Agencia_Estabelecimento_Valor': r'(?P<Agencia>\d{4})\s+(?P<Estabelecimento>\d{4})\s+(?P<ValorReservado>[\d,.]+)',
        'Totais': r'Totais\s+(?P<Principal>[\d,.]+)\s+(?P<Juros>[\d,.]+)\s+(?P<Multa>[\d,.]+)\s+(?P<Total>[\d,.]+)'
    }

    dados = {}
    for chave, padrao in regex.items():
        match = re.search(padrao, comprovante)
        if match:
            dados.update(match.groupdict())

    linhas = comprovante.splitlines()
    dados_com_itens = []
    i = 0
    while i < len(linhas) - 1:
        linha = linhas[i]
        linha_seguinte = linhas[i + 1]
        pattern_item = re.match(
            r'(\d{4})\s+([A-ZÀ-ÿa-z0-9\-./\s]+?)\s+(\d{1,3}(?:\.\d{3})*,\d{2})\s+(\d{1,3}(?:\.\d{3})*,\d{2}|-)\s+(\d{1,3}(?:\.\d{3})*,\d{2}|-)\s+(\d{1,3}(?:\.\d{3})*,\d{2})',
            linha)
        pattern_subdesc = re.match(r'(\d{2})\s*-\s*(.+)', linha_seguinte)

        if pattern_item and pattern_subdesc:
            item = pattern_item.groups()
            subcodigo = pattern_subdesc.group(1)
            descricao_complementar = pattern_subdesc.group(2).strip()
            linha_dados = dados.copy()
            linha_dados.update({
                'Codigo': f"{item[0]}-{subcodigo}",
                'DescricaoPrincipal': item[1].strip(),
                'DescricaoComplementar': descricao_complementar,
                'PrincipalItem': item[2],
                'MultaItem': item[3],
                'JurosItem': item[4],
                'TotalItem': item[5]
            })
            dados_com_itens.append(linha_dados)
            i += 2
        else:
            i += 1
    return dados_com_itens

def carregar_darfs(uploaded_pdfs):
    if not uploaded_pdfs:
        return None
    dados_expandidos = []
    for pdf_file in uploaded_pdfs:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                texto = page.extract_text()
                linhas = extrair_dados_darf(texto)
                dados_expandidos.extend(linhas)
    df = pd.DataFrame(dados_expandidos)
    if 'Codigo' in df.columns:
        df['Codigo'] = df['Codigo'].str.replace('-', '', regex=False)
    if 'PeriodoApuracao' in df.columns:
        df['Período Ajustado'] = df['PeriodoApuracao'].apply(lambda x: x if pd.isna(x) else x.strip())
    return df