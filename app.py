import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="📊 Análise de Jogos de Futebol", layout="centered")

st.markdown(
    "<h1 style='display: flex; align-items: center;'>"
    "<img src='https://img.icons8.com/color/48/bar-chart.png' style='margin-right:10px'/>"
    "Análise de Jogos de Futebol</h1>",
    unsafe_allow_html=True
)

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
# Exibe os dados
st.subheader("📊 Dados Extraídos")
st.write(df)
