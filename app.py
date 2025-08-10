import streamlit as st
import pandas as pd
import re


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

# Função para extrair os dados


def extrair_dados(linhas):
    jogos = []
    i = 0

    while i < len(linhas) - 5:
        try:
            if "League" in linhas[i] or "Championship" in linhas[i] or "Serie" in linhas[i]:
                liga = linhas[i]
                home = linhas[i+1]
                placar_ft = re.search(r"(\d+)\s*-\s*(\d+)", linhas[i+3])
                away = linhas[i+4]

                estat_line = ""
                for j in range(i+5, len(linhas)):
                    if re.search(r"\d+\s*-\s*\d+", linhas[j]):
                        estat_line = linhas[j]
                        break

                estat = re.findall(r"\d+\s*-\s*\d+", estat_line)
                if len(estat) < 5:
                    i += 1
                    continue

                placar_ht = [int(x) for x in estat[0].split("-")]
                chutes = [int(x) for x in estat[1].split("-")]
                chutes_gol = [int(x) for x in estat[2].split("-")]
                ataques = [int(x) for x in estat[3].split("-")]
                escanteios = [int(x) for x in estat[4].split("-")]

                odds = []
                for j in range(i+5, len(linhas)):
                    odds_match = re.findall(r"\d+\.\d+", linhas[j])
                    if len(odds_match) == 3:
                        odds = [float(x) for x in odds_match]
                        break

                if placar_ft and odds:
                    jogos.append({
                        "Home": home,
                        "Away": away,
                        "H_Gols_FT": int(placar_ft.group(1)),
                        "A_Gols_FT": int(placar_ft.group(2)),
                        "H_Gols_HT": placar_ht[0],
                        "A_Gols_HT": placar_ht[1],
                        "H_Chute": chutes[0],
                        "A_Chute": chutes[1],
                        "H_Chute_Gol": chutes_gol[0],
                        "A_Chute_Gol": chutes_gol[1],
                        "H_Ataques": ataques[0],
                        "A_Ataques": ataques[1],
                        "H_Escanteios": escanteios[0],
                        "A_Escanteios": escanteios[1],
                        "Odd_H": odds[0],
                        "Odd_D": odds[1],
                        "Odd_A": odds[2]
                    })

                i += 6
            else:
                i += 1
        except:
            i += 1

    return pd.DataFrame(jogos)


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
        st.session_state.df_jogos = extrair_dados(linhas)
        st.rerun()

df = st.session_state.df_jogos

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
