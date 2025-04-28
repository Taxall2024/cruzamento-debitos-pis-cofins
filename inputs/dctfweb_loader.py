import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st

def get_all_tags(xml_content):
    root = ET.fromstring(xml_content.strip())
    tags_unicas = set()
    for elem in root.iter():
        tag_name = elem.tag.split("}")[-1]
        tags_unicas.add(tag_name)
    return list(tags_unicas)

def parse_xml_to_dataframe(xml_content, filename, all_tags):
    try:
        root = ET.fromstring(xml_content.strip())
        data = {"Arquivo": filename}
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1]
            if tag_name in data:
                count = 1
                new_tag_name = f"{tag_name}_{count}"
                while new_tag_name in data:
                    count += 1
                    new_tag_name = f"{tag_name}_{count}"
                tag_name = new_tag_name
            data[tag_name] = elem.text.strip() if elem.text and elem.text.strip() else None
        for tag in all_tags:
            if tag not in data:
                data[tag] = None
        return data
    except Exception as e:
        st.error(f"Erro ao processar o arquivo {filename}: {e}")
        return None

def carregar_xmls(uploaded_files):
    if not uploaded_files:
        return None
    lista_dados = []
    all_tags = set()
    xml_contents = {}

    for uploaded_file in uploaded_files:
        xml_content = uploaded_file.read().decode("utf-8").strip()
        if xml_content:
            xml_contents[uploaded_file.name] = xml_content
            tags_xml = get_all_tags(xml_content)
            all_tags.update(tags_xml)

    all_tags = list(all_tags)
    for filename, xml_content in xml_contents.items():
        dados = parse_xml_to_dataframe(xml_content, filename, all_tags)
        if dados:
            lista_dados.append(dados)

    return pd.DataFrame(lista_dados)