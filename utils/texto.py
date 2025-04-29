import unicodedata

def limpar_texto(texto):
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8")
    return texto