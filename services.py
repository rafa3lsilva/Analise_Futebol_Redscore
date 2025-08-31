import pandas as pd
import requests
from datetime import date
import streamlit as st
from config import URL_DADOS, URL_BASE_JOGOS


@st.cache_data
def carregar_dados(data_escolhida: date):
    """Carrega dados históricos e jogos do dia com base na data escolhida (date)."""
    data_br = data_escolhida.strftime("%d/%m/%Y")   # exibição
    data_iso = data_escolhida.strftime("%Y-%m-%d")  # nome do arquivo

    # Carrega base histórica
    df_historicos = pd.read_csv(URL_DADOS)

    # Monta URL dos jogos do dia
    url_jogos = f"{URL_BASE_JOGOS}/Jogos_do_Dia_RedScore_{data_iso}.csv"
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
    except Exception as e:
        st.warning(f"Erro ao carregar jogos de {data_br}: {e}")

    return df_historicos, df_futuros, data_br, data_iso


def carregar_base_historica() -> pd.DataFrame:
    """Carrega e valida a base histórica principal."""
    try:
        df = pd.read_csv(URL_DADOS)

        df['Data'] = pd.to_datetime(
            df['Data'], format="%Y-%m-%d", errors="coerce")
        jogos_com_data_invalida = df['Data'].isnull().sum()

        if jogos_com_data_invalida > 0:
            st.warning(
                f"{jogos_com_data_invalida} jogo(s) foram ignorados por erro na data."
            )
            df.dropna(subset=['Data'], inplace=True)

        df['Data'] = df['Data'].dt.date
        df = df.sort_values(by="Data", ascending=False).reset_index(drop=True)

        # ✅ Validação de colunas essenciais
        colunas_essenciais = [
            "Home", "Away", "Data",
            "H_Gols_FT", "A_Gols_FT",
            "H_Gols_HT", "A_Gols_HT",
            "H_Escanteios", "A_Escanteios",
            "H_Chute", "A_Chute",
            "H_Ataques", "A_Ataques"
        ]

        faltando = [c for c in colunas_essenciais if c not in df.columns]
        if faltando:
            st.error(f"⚠️ Colunas ausentes no dataset: {faltando}")
            return pd.DataFrame(columns=colunas_essenciais)

        return df

    except Exception as e:
        st.error(f"Erro ao carregar a base histórica: {e}")
        return pd.DataFrame()
