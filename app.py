import streamlit as st
import pandas as pd
#import re
import data as dt


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

st.sidebar.header("📊 Análise de Jogos de Futebol"
                    )
# Tutorial
tutorial_url = "https://www.notion.so/Tutorial-Flashscore-2484bab1283b80f4b051e65d782a19d5?source=copy_link"

st.sidebar.markdown(f"""
    <div style="text-align: center; font-size: 16px;">
        <a href="{tutorial_url}" target="_blank" style="text-decoration: none;">
            <div style="margin-bottom: 10px; background-color:#1f77b4; padding:8px; border-radius:6px; color:white;">
                📚 Tutorial
            </div>
        </a>
    </div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Inicializa o estado
if "dados_jogos" not in st.session_state:
    st.session_state.dados_jogos = None
if "df_jogos" not in st.session_state:
    st.session_state.df_jogos = pd.DataFrame()

df = dt.extrair_dados(st.session_state.dados_jogos)
# Botão para reiniciar
if st.session_state.dados_jogos:
    if st.button("🔄 Novo Arquivo"):
        st.session_state.dados_jogos = None
        st.session_state.df_jogos = pd.DataFrame()
        st.rerun()

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

# Exibe os dados apenas se o DataFrame não estiver vazio
if not df.empty:
    #st.subheader("📊 Dados Extraídos")
    st.dataframe(df)

    home_team = df["Home"].unique()[0] if not df.empty else 'Home'
    away_team = df["Away"].unique()[0] if not df.empty else 'Away'

    st.sidebar.write("### Confronto:")

    # Layout vertical centralizado
    st.sidebar.markdown(f"""
            <div style="text-align: center; font-size: 16px;">
                <div style="margin-bottom: 10px; background-color:#1f77b4; padding:8px; border-radius:6px; color:white;">
                    🏠 {home_team}
                </div>
                <div style="margin-bottom: 5px;">⚔️ vs</div>
                <div style="background-color:#d62728; padding:8px; border-radius:6px; color:white;">
                    ✈️ {away_team}
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # Seleção do intervalo de jogos
    intervalo = st.radio("Selecione o intervalo de jogos:",
                            options=["Últimos 5 jogos", "Últimos 8 jogos",
                                    "Últimos 10 jogos", "Últimos 12 jogos"],
                            index=0,
                            horizontal=True)

    # Extrai o número do texto selecionado
    num_jogos = int(intervalo.split()[1])  # pega o número após "Últimos"

    # Aplica o intervalo nos DataFrames
    df_home_media = df.iloc[0:num_jogos]
    df_away_media = df.iloc[12:12 + num_jogos]

    # filtro para exibir os últimos jogos (Home)
    df_home = df.iloc[0:num_jogos]
    st.write(f"### Últimos {num_jogos} jogos do {home_team}:")
    st.dataframe(drop_reset_index(df_home))

    df_away = df.iloc[12:12 + num_jogos]
    st.write(f"### Últimos {num_jogos} jogos do {away_team}:")
    st.dataframe(drop_reset_index(df_away))