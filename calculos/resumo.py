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
      - [EFD] PIS/COFINS: somatórios da EFD por PERIODO
      - [DCTF] PIS/COFINS: somatórios da DCTF por PERIODO
      - [DARF] PIS/COFINS: somatórios da DARF por PERIODO
      - [PERDCOMP] PIS/COFINS: somatórios da planilha PER/DCOMP por PERIODO
      - [SUSPENSÃO] e [PARCELAMENTOS]: colunas zeradas
      - [DIVERGÊNCIA EFD] e [DIVERGÊNCIA DCTF]: cálculos de diferenças
    """
    # Funções auxiliares
    def fmt_periodo_txt(texto):
        # transforma 'MM/YYYY' em '01MMYYYY'
        return f"01{texto.replace('/', '')}" if isinstance(texto, str) else None

    def parse_num(v):
        s = str(v).replace('.', '').replace(',', '.')
        try:
            return float(s)
        except:
            return 0.0

    # --- EFD ---
    if df_efd is None or df_efd.empty:
        resumo = pd.DataFrame(columns=["PERIODO", "[EFD] PIS", "[EFD] COFINS"])
    else:
        efd = df_efd.copy()
        efd[12] = pd.to_numeric(
            efd[12].astype(str).str.replace('.', '').str.replace(',', '.'),
            errors='coerce'
        ).fillna(0.0)
        pis = (
            efd[efd[0] == 'M200'].groupby('PERIODO')[12].sum()
            .reset_index().rename(columns={12: '[EFD] PIS'})
        )
        cof = (
            efd[efd[0] == 'M600'].groupby('PERIODO')[12].sum()
            .reset_index().rename(columns={12: '[EFD] COFINS'})
        )
        resumo = pd.merge(pis, cof, on='PERIODO', how='outer').fillna(0)

    # --- DCTF ---
    def fmt_periodo(mofg):
        try:
            x = int(mofg)
            ano, mes = divmod(x, 100)
            return f"01{mes:02d}{ano}"
        except:
            return None

    dctf_pis = pd.DataFrame(columns=['PERIODO', '[DCTF] PIS'])
    dctf_cof = pd.DataFrame(columns=['PERIODO', '[DCTF] COFINS'])
    if df_dctf is not None and not df_dctf.empty:
        dctf = df_dctf.copy()
        dctf['PERIODO'] = dctf['MOFG'].apply(fmt_periodo)
        dctf['ValorDebito'] = dctf['ValorDebito'].apply(parse_num)
        mask_r10_pis = (dctf['Tipo']=='R10') & dctf['CodReceita'].astype(str).str[:4].isin(['8109','6912'])
        mask_r10_cof = (dctf['Tipo']=='R10') & dctf['CodReceita'].astype(str).str[:4].isin(['2172','5856'])
        dctf_pis = dctf[mask_r10_pis].groupby('PERIODO')['ValorDebito'].sum().reset_index().rename(columns={'ValorDebito':'[DCTF] PIS'})
        dctf_cof = dctf[mask_r10_cof].groupby('PERIODO')['ValorDebito'].sum().reset_index().rename(columns={'ValorDebito':'[DCTF] COFINS'})
    resumo = resumo.merge(dctf_pis, on='PERIODO', how='left').fillna({'[DCTF] PIS':0})
    resumo = resumo.merge(dctf_cof, on='PERIODO', how='left').fillna({'[DCTF] COFINS':0})

    # --- DARF ---
    darf_pis = pd.DataFrame(columns=['PERIODO', '[DARF] PIS'])
    darf_cof = pd.DataFrame(columns=['PERIODO', '[DARF] COFINS'])
    if df_darf is not None and not df_darf.empty:
        darf = df_darf.copy()
        if 'Período Apuração' in darf.columns:
            darf = darf.rename(columns={'Período Apuração':'PeriodoApuracao'})
        if 'Código' in darf.columns:
            darf = darf.rename(columns={'Código':'Codigo'})
        darf['Periodo_dt'] = pd.to_datetime(darf['PeriodoApuracao'], dayfirst=True, errors='coerce')
        darf['PERIODO'] = '01' + darf['Periodo_dt'].dt.strftime('%m%Y')
        darf['PrincipalItem'] = darf['PrincipalItem'].apply(parse_num)
        mask_darf_pis = darf['Codigo'].astype(str).str[:4].isin(['8109','6912'])
        mask_darf_cof = darf['Codigo'].astype(str).str[:4].isin(['2172','5856'])
        darf_pis = darf[mask_darf_pis].groupby('PERIODO')['PrincipalItem'].sum().reset_index().rename(columns={'PrincipalItem':'[DARF] PIS'})
        darf_cof = darf[mask_darf_cof].groupby('PERIODO')['PrincipalItem'].sum().reset_index().rename(columns={'PrincipalItem':'[DARF] COFINS'})
    resumo = resumo.merge(darf_pis, on='PERIODO', how='left').fillna({'[DARF] PIS':0})
    resumo = resumo.merge(darf_cof, on='PERIODO', how='left').fillna({'[DARF] COFINS':0})

    # --- SUSPENSÃO e PARCELAMENTOS ---
    for col in ['[SUSPENSÃO] PIS','[SUSPENSÃO] COFINS','[PARCELAMENTOS] PIS','[PARCELAMENTOS] COFINS']:
        resumo[col] = 0.0

    # --- PERDCOMP (planilha) ---
    perd_pis = pd.DataFrame(columns=['PERIODO','[PERDCOMP] PIS'])
    perd_cof = pd.DataFrame(columns=['PERIODO','[PERDCOMP] COFINS'])
    if df_perdcomp is not None and not df_perdcomp.empty:
        pc = df_perdcomp.copy()
        if '_periodos_convertidos' in pc.columns:
            pc['PERIODO'] = pc['_periodos_convertidos'].apply(fmt_periodo_txt)
        # detectar código e valor na planilha
        code_cols = [c for c in pc.columns if c.lower().startswith('cod')]
        val_cols = [c for c in pc.columns if 'valor_principal' in c.lower()]
        if val_cols:
            pc[val_cols[0]] = pc[val_cols[0]].apply(parse_num)
            if code_cols:
                codigo = code_cols[0]
                mask_pc_pis = pc[codigo].astype(str).str[:4].isin(['8109','6912'])
                mask_pc_cof = pc[codigo].astype(str).str[:4].isin(['2172','5856'])
                perd_pis = pc[mask_pc_pis].groupby('PERIODO')[val_cols[0]].sum().reset_index().rename(columns={val_cols[0]:'[PERDCOMP] PIS'})
                perd_cof = pc[mask_pc_cof].groupby('PERIODO')[val_cols[0]].sum().reset_index().rename(columns={val_cols[0]:'[PERDCOMP] COFINS'})
            else:
                # sem coluna de código, soma geral em ambos
                tot = pc.groupby('PERIODO')[val_cols[0]].sum().reset_index()
                perd_pis = tot.rename(columns={val_cols[0]:'[PERDCOMP] PIS'})
                perd_cof = tot.rename(columns={val_cols[0]:'[PERDCOMP] COFINS'})
    resumo = resumo.merge(perd_pis, on='PERIODO', how='left').fillna({'[PERDCOMP] PIS':0})
    resumo = resumo.merge(perd_cof, on='PERIODO', how='left').fillna({'[PERDCOMP] COFINS':0})

    # --- DIVERGÊNCIAS ---
    resumo['[DIVERGÊNCIA EFD] PIS'] = resumo['[EFD] PIS'] - (resumo['[DARF] PIS'] + resumo['[PERDCOMP] PIS'] + resumo['[PARCELAMENTOS] PIS'])
    resumo['[DIVERGÊNCIA EFD] COFINS'] = resumo['[EFD] COFINS'] - (resumo['[DARF] COFINS'] + resumo['[PERDCOMP] COFINS'] + resumo['[PARCELAMENTOS] COFINS'])
    resumo['[DIVERGÊNCIA DCTF] PIS'] = resumo['[DCTF] PIS'] - (resumo['[DARF] PIS'] + resumo['[PERDCOMP] PIS'] + resumo['[PARCELAMENTOS] PIS'])
    resumo['[DIVERGÊNCIA DCTF] COFINS'] = resumo['[DCTF] COFINS'] - (resumo['[DARF] COFINS'] + resumo['[PERDCOMP] COFINS'] + resumo['[PARCELAMENTOS] COFINS'])

    # ordenação e totais
    resumo['Periodo_dt'] = pd.to_datetime(resumo['PERIODO'], format='%d%m%Y', errors='coerce')
    resumo = resumo.sort_values('Periodo_dt').drop(columns=['Periodo_dt']).reset_index(drop=True)
    # linha de totais
    num_cols = [c for c in resumo.columns if c!='PERIODO']
    tot = resumo[num_cols].sum().to_frame().T
    tot.insert(0,'PERIODO','TOTAL')
    resumo = pd.concat([resumo, tot], ignore_index=True)

    return resumo
