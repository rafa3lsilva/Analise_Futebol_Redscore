import streamlit as st
import pandas as pd
#import re
import data as dt
import sidebar as sb


def drop_reset_index(df):
    df = df.dropna()
    df = df.reset_index(drop=True)
    df.index += 1
    return df

# Função para configurar a página Streamlit
st.set_page_config(
    page_title="Análise Futebol",
    page_icon=":soccer:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <h1 style='display: flex; align-items: center; justify-content: center; text-align: center;'>
        📊 Análise de Jogos de Futebol
    </h1>
    """,
    unsafe_allow_html=True
)

# Importa a barra lateral
sb.sidebar()

# Inicializa o estado
if "dados_jogos" not in st.session_state:
    st.session_state.dados_jogos = None
if "df_jogos" not in st.session_state:
    st.session_state.df_jogos = pd.DataFrame()

df = dt.extrair_dados(st.session_state.dados_jogos)

# Upload do arquivo (só aparece se ainda não foi carregado)
if not st.session_state.dados_jogos:
    uploaded_file = st.file_uploader(
        "📁 Escolha o arquivo .txt com os dados dos jogos", type="txt")
    if uploaded_file:
        linhas = uploaded_file.read().decode("utf-8").splitlines()
        linhas = [linha.strip() for linha in linhas if linha.strip()]
        st.session_state.dados_jogos = linhas
        st.session_state.df_jogos = dt.extrair_dados(linhas)
        st.rerun()


# Só chama extrair_dados se houver dados válidos
if st.session_state.dados_jogos:
    df = dt.extrair_dados(st.session_state.dados_jogos)
else:
    df = pd.DataFrame()

if st.session_state.dados_jogos:
       if st.sidebar.button("🔄 Novo Arquivo"):
            st.session_state.dados_jogos = None
            st.session_state.df_jogos = pd.DataFrame()
            st.rerun()

# Exibe os dados apenas se o DataFrame não estiver vazio
if not df.empty:
    #st.subheader("📊 Dados Extraídos")
    #st.dataframe(df)

    # Seleção do intervalo de jogos
    intervalo = st.radio("Selecione o intervalo de jogos:",
                            options=["Últimos 5 jogos", "Últimos 8 jogos",
                                    "Últimos 10 jogos", "Últimos 12 jogos"],
                            index=0,
                            horizontal=True)

    # Extrai o número do texto selecionado
    num_jogos = int(intervalo.split()[1])  # pega o número após "Últimos"

    # Aplica o intervalo nos DataFrames
    df_home = df.iloc[0:num_jogos]
    df_away = df.iloc[12:12 + num_jogos]

    home_team = df_home["Home"].unique()[0] if not df_home.empty else 'Home'
    # Pega o primeiro valor único da coluna "Away" que seja diferente do "Home"
    away_team = df_away["Away"].unique()[0] if not df_away.empty else 'Away'

    # Exibe o confronto atual
    sb.confronto_atual(home_team, away_team)

    # Exibe as médias de gols
    media_home_gols_marcados = dt.media_home_gols_feitos(df_home)
    media_home_gols_sofridos = dt.media_home_gols_sofridos(df_home)
    media_away_gols_marcados = dt.media_away_gols_feitos(df_away)
    media_away_gols_sofridos = dt.media_away_gols_sofridos(df_away)

    #exibe as médias de gols
    st.markdown("### 📋 Médias de Gols Home e Away", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display: flex; justify-content: space-around;">
        <div style="background-color:#1f77b4; padding:15px; border-radius:8px; width:45%; text-align:center; color:white;">
            <h3>🏠 {home_team}</h3>
            <p style="font-size:18px;">⚽ Média de Gols Marcados: <strong>{media_home_gols_marcados:.2f}</strong></p>
            <p style="font-size:18px;">🛡️ Média de Gols Sofridos: <strong>{media_home_gols_sofridos:.2f}</strong></p>
        </div>
        <div style="background-color:#d62728; padding:15px; border-radius:8px; width:45%; text-align:center; color:white;">
            <h3>✈️ {away_team}</h3>
            <p style="font-size:18px;">⚽ Média de Gols Marcados: <strong>{media_away_gols_marcados:.2f}</strong></p>
            <p style="font-size:18px;">🛡️ Média de Gols Sofridos: <strong>{media_away_gols_sofridos:.2f}</strong></p>
        </div>
    </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Taxa de Vitórias home
    df_home['resultado'] = df_home['H_Gols_FT'] > df_home['A_Gols_FT']
    vitoria = df_home[df_home['resultado'] == 1].shape[0]
    tx_vitoria = (vitoria / num_jogos) * 100

    # Taxa de Vitórias away
    df_away['resultado'] = df_away['A_Gols_FT'] > df_away['H_Gols_FT']
    vitoria_away = df_away[df_away['resultado'] == 1].shape[0]
    tx_vitoria_away = (vitoria_away / num_jogos) * 100
    

    # filtro para exibir os últimos jogos (Home)
    df_home = df.iloc[0:num_jogos]
    st.write(f"### Últimos {num_jogos} jogos do {home_team}:")
    st.dataframe(drop_reset_index(df_home))

    # filtro para exibir os últimos jogos (Away)
    df_away = df.iloc[12:12 + num_jogos]
    st.write(f"### Últimos {num_jogos} jogos do {away_team}:")
    st.dataframe(drop_reset_index(df_away))