# calculos/resumo.py

import pandas as pd

def gerar_df_resumo(
    df_efd: pd.DataFrame,
    df_dctf: pd.DataFrame,
    df_darf: pd.DataFrame,
    df_perdcomp: pd.DataFrame
) -> pd.DataFrame:
    """
    Gera o DataFrame de resumo contendo:
      - PERIODO: valor da coluna 5 do registro '0000'
      - [EFD] PIS/Cofins: somatórios dos valores da coluna 12 em registros 'M200' e 'M600' por PERIODO
      - [DCTF] PIS: somatório de 'ValorDebito' em registros 'R10' para códigos 8109,6912
      - [DCTF] COFINS: somatório de 'ValorDebito' em registros 'R10' para códigos 2172,5856
      - [DARF] PIS: somatório de 'PrincipalItem' em registros DARF para códigos 8109,6912
      - [DARF] COFINS: somatório de 'PrincipalItem' em registros DARF para códigos 2172,5856
      - [SUSPENSÃO] PIS/COFINS: colunas zeradas
      - [PERDCOMP] PIS: somatório de 'ValorCompensado' em df_perdcomp para códigos 8109,6912
      - [PERDCOMP] COFINS: somatório de 'ValorCompensado' em df_perdcomp para códigos 2172,5856
      - [PARCELAMENTOS] PIS/COFINS: colunas zeradas
      - [DIVERGÊNCIA EFD] PIS/COFINS: diferenças entre EFD e somatórios de pag. equivalentes
      - [DIVERGÊNCIA DCTF] PIS/COFINS: diferenças entre DCTF e somatórios de pag. equivalentes
    """
    # --- EFD ---
    if df_efd is None or df_efd.empty:
        resumo = pd.DataFrame(columns=["PERIODO", "[EFD] PIS", "[EFD] COFINS"])
    else:
        efd = df_efd.copy()
        # converter valor (coluna 12) para float
        efd[12] = pd.to_numeric(
            efd[12].astype(str).str.replace('.', '').str.replace(',', '.'),
            errors='coerce'
        )
        pis = (
            efd[efd[0] == 'M200']
            .groupby('PERIODO')[12].sum()
            .reset_index().rename(columns={12: '[EFD] PIS'})
        )
        cof = (
            efd[efd[0] == 'M600']
            .groupby('PERIODO')[12].sum()
            .reset_index().rename(columns={12: '[EFD] COFINS'})
        )
        resumo = pd.merge(pis, cof, on='PERIODO', how='outer').fillna(0)

    # --- DCTF ---
    dctf_pis = pd.DataFrame(columns=['PERIODO', '[DCTF] PIS'])
    dctf_cof = pd.DataFrame(columns=['PERIODO', '[DCTF] COFINS'])
    if df_dctf is not None and not df_dctf.empty:
        dctf = df_dctf.copy()
        # construir PERIODO = '01' + MM + YYYY a partir de MOFG (formato YYYYMM)
        def fmt_periodo(mofg):
            try:
                x = int(mofg)
                ano = x // 100
                mes = x % 100
                return f"01{mes:02d}{ano}"
            except:
                return None
        dctf['PERIODO'] = dctf['MOFG'].apply(fmt_periodo)

        # converter ValorDebito para float
        def parse_debito(v):
            s = ''.join(filter(str.isdigit, str(v)))
            return int(s) / 100 if s.isdigit() else 0.0
        dctf['ValorDebito'] = dctf['ValorDebito'].apply(parse_debito)

        mask_r10_pis = (
            (dctf['Tipo'] == 'R10') &
            dctf['CodReceita'].astype(str).str[:4].isin(['8109', '6912'])
        )
        dctf_pis = (
            dctf.loc[mask_r10_pis]
            .groupby('PERIODO')['ValorDebito'].sum()
            .reset_index().rename(columns={'ValorDebito': '[DCTF] PIS'})
        )

        mask_r10_cof = (
            (dctf['Tipo'] == 'R10') &
            dctf['CodReceita'].astype(str).str[:4].isin(['2172', '5856'])
        )
        dctf_cof = (
            dctf.loc[mask_r10_cof]
            .groupby('PERIODO')['ValorDebito'].sum()
            .reset_index().rename(columns={'ValorDebito': '[DCTF] COFINS'})
        )

    resumo = pd.merge(resumo, dctf_pis, on='PERIODO', how='left').fillna({'[DCTF] PIS': 0})
    resumo = pd.merge(resumo, dctf_cof, on='PERIODO', how='left').fillna({'[DCTF] COFINS': 0})

    # --- DARF ---
    darf_pis = pd.DataFrame(columns=['PERIODO', '[DARF] PIS'])
    darf_cof = pd.DataFrame(columns=['PERIODO', '[DARF] COFINS'])
    if df_darf is not None and not df_darf.empty:
        darf = df_darf.copy()
        # renomear colunas se vierem com acentos ou espaços
        if 'Período Apuração' in darf.columns:
            darf = darf.rename(columns={'Período Apuração': 'PeriodoApuracao'})
        if 'Código' in darf.columns:
            darf = darf.rename(columns={'Código': 'Codigo'})
        # converter para datetime
        darf['Periodo_dt'] = pd.to_datetime(darf['PeriodoApuracao'], dayfirst=True, errors='coerce')
        # gerar PERIODO sempre no dia 01 do mês para casar com os outros dataframes
        darf['PERIODO'] = '01' + darf['Periodo_dt'].dt.strftime('%m%Y')

        # converter PrincipalItem para float
        def parse_principal(v):
            t = str(v).replace('.', '').replace(',', '.')
            try:
                return float(t)
            except:
                return 0.0
        darf['PrincipalItem'] = darf['PrincipalItem'].apply(parse_principal)

        mask_darf_pis = darf['Codigo'].astype(str).str[:4].isin(['8109', '6912'])
        darf_pis = (
            darf.loc[mask_darf_pis]
            .groupby('PERIODO')['PrincipalItem'].sum()
            .reset_index().rename(columns={'PrincipalItem': '[DARF] PIS'})
        )

        mask_darf_cof = darf['Codigo'].astype(str).str[:4].isin(['2172', '5856'])
        darf_cof = (
            darf.loc[mask_darf_cof]
            .groupby('PERIODO')['PrincipalItem'].sum()
            .reset_index().rename(columns={'PrincipalItem': '[DARF] COFINS'})
        )

    resumo = pd.merge(resumo, darf_pis, on='PERIODO', how='left').fillna({'[DARF] PIS': 0})
    resumo = pd.merge(resumo, darf_cof, on='PERIODO', how='left').fillna({'[DARF] COFINS': 0})

    # --- SUSPENSÃO e PARCELAMENTOS ---
    resumo['[SUSPENSÃO] PIS'] = 0.0
    resumo['[SUSPENSÃO] COFINS'] = 0.0
    resumo['[PARCELAMENTOS] PIS'] = 0.0
    resumo['[PARCELAMENTOS] COFINS'] = 0.0

    # --- PERDCOMP (usa df_dctf para registros R12) ---
    perd_pis = pd.DataFrame(columns=['PERIODO','[PERDCOMP] PIS'])
    perd_cof = pd.DataFrame(columns=['PERIODO','[PERDCOMP] COFINS'])
    if df_dctf is not None and not df_dctf.empty:
        pc = df_dctf.copy()

        # normaliza e gera PERIODO igual ao restante do código
        pc['Tipo'] = pc['Tipo'].astype(str).str.strip().str.upper().str.replace('-', '')
        pc['CodReceita'] = pc['CodReceita'].astype(str).str.strip()
        pc['PERIODO'] = pc['MOFG'].apply(fmt_periodo)

        # parse do campo de valor compensado (supondo que exista uma coluna 'ValorCompensado')
        def parse_comp(v):
            s = ''.join(filter(str.isdigit, str(v)))
            return int(s) / 100 if s.isdigit() else 0.0
        pc['ValorCompensado'] = pc['ValorCompensado'].apply(parse_comp)

        # máscaras R12 + prefixos de PIS/COFINS
        mask_pc_pis = (
            (pc['Tipo'] == 'R12') &
            pc['CodReceita'].str[:4].isin(['8109','6912'])
        )
        mask_pc_cof = (
            (pc['Tipo'] == 'R12') &
            pc['CodReceita'].str[:4].isin(['2172','5856'])
        )

        # agregação
        perd_pis = (
            pc.loc[mask_pc_pis]
              .groupby('PERIODO')['ValorCompensado']
              .sum()
              .reset_index()
              .rename(columns={'ValorCompensado':'[PERDCOMP] PIS'})
        )

        perd_cof = (
            pc.loc[mask_pc_cof]
              .groupby('PERIODO')['ValorCompensado']
              .sum()
              .reset_index()
              .rename(columns={'ValorCompensado':'[PERDCOMP] COFINS'})
        )

    resumo = pd.merge(resumo, perd_pis, on='PERIODO', how='left').fillna({'[PERDCOMP] PIS': 0})
    resumo = pd.merge(resumo, perd_cof, on='PERIODO', how='left').fillna({'[PERDCOMP] COFINS': 0})

    # --- DIVERGÊNCIAS ---
    resumo['[DIVERGÊNCIA EFD] PIS'] = (
        resumo['[EFD] PIS'] - (resumo['[DARF] PIS'] + resumo['[PERDCOMP] PIS'] + resumo['[PARCELAMENTOS] PIS'])
    )
    resumo['[DIVERGÊNCIA EFD] COFINS'] = (
        resumo['[EFD] COFINS'] - (resumo['[DARF] COFINS'] + resumo['[PERDCOMP] COFINS'] + resumo['[PARCELAMENTOS] COFINS'])
    )
    resumo['[DIVERGÊNCIA DCTF] PIS'] = (
        resumo['[DCTF] PIS'] - (resumo['[DARF] PIS'] + resumo['[PERDCOMP] PIS'] + resumo['[PARCELAMENTOS] PIS'])
    )
    resumo['[DIVERGÊNCIA DCTF] COFINS'] = (
        resumo['[DCTF] COFINS'] - (resumo['[DARF] COFINS'] + resumo['[PERDCOMP] COFINS'] + resumo['[PARCELAMENTOS] COFINS'])
    )

    # ordenar cronologicamente por PERIODO
    resumo['Periodo_dt'] = pd.to_datetime(resumo['PERIODO'], format='%d%m%Y', errors='coerce')
    resumo = resumo.sort_values('Periodo_dt').drop(columns=['Periodo_dt']).reset_index(drop=True)

    return resumo
