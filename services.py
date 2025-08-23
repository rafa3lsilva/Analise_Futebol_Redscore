import pandas as pd
import requests
import streamlit as st
from datetime import date

URL_DADOS = "https://raw.githubusercontent.com/rafa3lsilva/webscrapping_redscore/refs/heads/main/dados_redscore.csv"


@st.cache_data
def carregar_dados(data_escolhida: date):
    """Carrega dados históricos e jogos do dia com base na data escolhida (date)."""

    # Formatos
    data_br = data_escolhida.strftime("%d/%m/%Y")   # exibição
    data_iso = data_escolhida.strftime("%Y-%m-%d")  # nome do arquivo

    # Carrega base histórica
    df_historicos = pd.read_csv(URL_DADOS)

    # Monta URL dos jogos do dia
    url_jogos = f"https://raw.githubusercontent.com/rafa3lsilva/webscrapping_redscore/refs/heads/main/jogos_do_dia/Jogos_do_Dia_RedScore_{data_iso}.csv"

    df_futuros = pd.DataFrame()
    try:
        response = requests.get(url_jogos)
        if response.status_code == 200:
            df_futuros = pd.read_csv(url_jogos)
            condicao_hora_valida = df_futuros['hora'].astype(
                str).str.match(r'^\d{2}:\d{2}$')
            df_futuros = df_futuros[condicao_hora_valida].copy()
            df_futuros['confronto'] = df_futuros['home'] + \
                ' x ' + df_futuros['away']
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ao carregar jogos de {data_br}: {e}")
    except pd.errors.ParserError as e:
        st.error(f"Erro ao ler CSV de {data_br}: {e}")

    return df_historicos, df_futuros, data_br, data_iso
