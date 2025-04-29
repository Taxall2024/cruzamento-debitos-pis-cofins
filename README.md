# Cruzamento de Débitos PIS/Cofins

Este projeto consolida e cruza dados de EFD, DCTF, DARF e perdas/compensações para PIS e Cofins, gerando um resumo completo por período de apuração.

## Estrutura

```
seu_projeto/
├── calculos/
│   └── resumo.py       # Função principal de geração do DataFrame resumo
├── main.py             # Ponto de entrada que chama gerar_df_resumo()
├── data/               # (Opcional) arquivos de entrada .csv ou .dec
├── requirements.txt    # Dependências do projeto
└── README.md           # Este arquivo
```

## Instalação

1. Crie e ative um ambiente virtual (recomendado):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Coloque seus DataFrames de entradas (`df_efd`, `df_dctf`, `df_darf`, `df_perdcomp`) em `main.py` (ou leia de arquivos CSV/DEC).
2. Em `main.py`, importe e chame:

   ```python
   from calculos.resumo import gerar_df_resumo
   import pandas as pd

   df_efd      = pd.read_csv("data/efd.csv", dtype=str)
   df_dctf     = pd.read_csv("data/dctf.csv", dtype=str)
   df_darf     = pd.read_csv("data/darf.csv", dtype=str)
   df_perdcomp = pd.read_csv("data/perdcomp.csv", dtype=str)

   resumo = gerar_df_resumo(df_efd, df_dctf, df_darf, df_perdcomp)
   print(resumo)
   ```

3. Ajuste os caminhos de leitura/escrita conforme sua necessidade.

## Licença

MIT © Seu Nome
