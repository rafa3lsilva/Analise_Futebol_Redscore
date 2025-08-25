# app.py
from services import carregar_dados
import streamlit as st
import pandas as pd
import data as dt
import sidebar as sb
import services as sv
import views as vw
import logging

# ----------------------------
# CONFIGURAÇÕES INICIAIS
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Análise Futebol",
    page_icon=":soccer:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicialização de estados
for key, default in {
    "saved_analyses": [],
    "dados_jogos": None,
    "df_jogos": pd.DataFrame(),
    "data_loaded_successfully": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ----------------------------
# FUNÇÃO AUXILIAR → Value Bet
# ----------------------------


def mostrar_value_bet(label, prob, odd_justa, col):
    """
    Exibe probabilidade, odd justa e permite inserir odd do mercado para detectar valor.
    """
    with col:
        st.metric(label=label, value=f"{prob}%",
                  delta=f"Odd Justa: {odd_justa}")
        odd_mercado = st.number_input(
            f"Odd Mercado para {label}",
            min_value=1.00,
            value=float(odd_justa),
            step=0.01,
            format="%.2f",
            key=f"odd_mercado_{label}"
        )
        if odd_mercado > odd_justa:
            valor_ev = (odd_mercado / odd_justa - 1) * 100
            st.success(f"✅ Valor Encontrado: +{valor_ev:.2f}%")
        else:
            st.warning("Sem valor aparente.")


# ----------------------------
# INTERFACE
# ----------------------------
vw.titulo_principal()
sb.sidebar()

# ----------------------------
# CARREGAMENTO DE DADOS
# ----------------------------
st.sidebar.markdown("### 🔎 Filtros da Análise")
dia = sb.calendario()
with st.spinner("⏳ Carregando dados do GitHub..."):
    df_jogos, df_proximos_jogos, dia_br, dia_iso = carregar_dados(dia)

st.session_state.df_proximos_jogos = df_proximos_jogos
st.session_state.df_jogos = sv.carregar_base_historica()
df, df_proximos = st.session_state.df_jogos, st.session_state.df_proximos_jogos

vw.mostrar_status_carregamento(df_proximos_jogos, dia_br, dia_iso)
vw.configurar_estilo_intervalo_jogos()

# ----------------------------
# SELEÇÃO DE JOGO
# ----------------------------
if not df.empty and not df_proximos.empty:
    # Filtros sequenciais (hora → liga → confronto)
    selected_time = st.sidebar.selectbox(
        "Selecione o Horário:", sorted(df_proximos['hora'].unique()))
    jogos_filtrado_hora = df_proximos[df_proximos['hora'] == selected_time]

    selected_league = st.sidebar.selectbox(
        "Selecione a Liga:", sorted(jogos_filtrado_hora['liga'].unique()))
    jogos_filtrado_liga = jogos_filtrado_hora[jogos_filtrado_hora['liga']
                                              == selected_league]

    selected_game = st.sidebar.selectbox(
        "Escolha o Jogo:", sorted(jogos_filtrado_liga['confronto'].unique()))
    selected_game_data = jogos_filtrado_liga[jogos_filtrado_liga['confronto'] == selected_game]

    if selected_game_data.empty:
        st.warning("Por favor, selecione um jogo válido para iniciar a análise.")
        st.stop()

    home_team, away_team = selected_game_data[['home', 'away']].iloc[0]

    # Cenário
    selected_scenario = st.sidebar.selectbox(
        "Cenário de Análise:",
        ["Geral", "Casa/Fora"],
        help="Geral: todos os jogos. Casa/Fora: só casa do mandante e fora do visitante."
    )

    # Define bases de dados de acordo com cenário
    if selected_scenario == 'Geral':
        df_home_base = df[(df['Home'].str.lower() == home_team.lower()) |
                          (df['Away'].str.lower() == home_team.lower())].copy()
        df_away_base = df[(df['Home'].str.lower() == away_team.lower()) |
                          (df['Away'].str.lower() == away_team.lower())].copy()
    else:
        df_home_base = df[df['Home'].str.lower() == home_team.lower()].copy()
        df_away_base = df[df['Away'].str.lower() == away_team.lower()].copy()

    # Ordenar jogos mais recentes
    df_home_base, df_away_base = df_home_base.sort_values(
        by='Data', ascending=False), df_away_base.sort_values(by='Data', ascending=False)

    # ----------------------------
    # INTERVALO DE JOGOS
    # ----------------------------
    st.markdown("### 📅 Intervalo de Jogos")
    intervalo = st.radio("", options=["Últimos 5 jogos", "Últimos 6 jogos",
                         "Últimos 8 jogos", "Últimos 10 jogos"], index=1, horizontal=True)
    num_jogos_selecionado = int(intervalo.split()[1])
    df_home, df_away = df_home_base.head(
        num_jogos_selecionado), df_away_base.head(num_jogos_selecionado)

    # ----------------------------
    # AJUSTE DE PESOS
    # ----------------------------
    with st.sidebar.expander("⚙️ Ajustar Pesos do Modelo"):
        limite_consistente = st.slider(
            "Nível 'Consistente' (DP ≤)", 0.1, 2.0, 0.8, 0.1)
        limite_imprevisivel = st.slider(
            "Nível 'Imprevisível' (DP >)", 0.1, 2.0, 1.2, 0.1)

    # ----------------------------
    # ANÁLISE PRINCIPAL DO CENÁRIO
    # ----------------------------
    analise = dt.analisar_cenario_partida(
        home_team, away_team, df_jogos, num_jogos=num_jogos_selecionado, scenario=selected_scenario, linha_gols=2.5)

    # Resultado 1X2
    st.markdown(f"#### 📊 Cenário da Partida ({analise['cenario_usado']})")
    col1, col2, col3 = st.columns(3)
    col1.metric("🏠 Vitória " + home_team, f"{analise['prob_home']}%")
    col2.metric("🤝 Empate", f"{analise['prob_draw']}%")
    col3.metric("✈️ Vitória " + away_team, f"{analise['prob_away']}%")

    # Over/Under + BTTS
    col1, col2 = st.columns(2)
    col1.markdown(
        f"🔼 Over {analise['over_under']['linha']} gols: **{analise['over_under']['p_over']}%**")
    col2.markdown(
        f"🔽 Under {analise['over_under']['linha']} gols: **{analise['over_under']['p_under']}%**")
    col1, col2 = st.columns(2)
    col1.markdown(f"✅ BTTS Sim: **{analise['btts']['p_btts_sim']}%**")
    col2.markdown(f"❌ BTTS Não: **{analise['btts']['p_btts_nao']}%**")

    # Placares prováveis
    st.markdown("### 🔮 Top 5 Placares Mais Prováveis")
    cols = st.columns(5)
    for idx, p in enumerate(analise['placares_top']):
        with cols[idx]:
            vw.card_placar(p["placar"], p["prob"])

    # ----------------------------
    # MERCADOS (Poisson + BTTS)
    # ----------------------------
    st.markdown("## 🎯 Mercado de Gols (FT)")
    resultados = dt.prever_gols(home_team, away_team, df_jogos,
                                num_jogos=num_jogos_selecionado, min_jogos=3, scenario=selected_scenario)

    linha_over15 = dt.calcular_over_under(resultados, 1.5)
    linha_over25 = dt.calcular_over_under(resultados, 2.5)
    linha_over35 = dt.calcular_over_under(resultados, 3.5)
    btts = dt.calcular_btts(resultados)

    df_resultado_mercados = pd.DataFrame([
        {"Mercado": "Over 1.5", "Probabilidade (%)": linha_over15['p_over'], "Odd Justa": round(
            100/linha_over15['p_over'], 2)},
        {"Mercado": "Over 2.5", "Probabilidade (%)": linha_over25['p_over'], "Odd Justa": round(
            100/linha_over25['p_over'], 2)},
        {"Mercado": "Over 3.5", "Probabilidade (%)": linha_over35['p_over'], "Odd Justa": round(
            100/linha_over35['p_over'], 2)},
        {"Mercado": "BTTS", "Probabilidade (%)": btts['p_btts_sim'], "Odd Justa": round(
            100/btts['p_btts_sim'], 2)}
    ])

    st.subheader(
        "🎯 Probabilidades por Mercado (Poisson) 🔎 Comparador de Valor")
    cols = st.columns(len(df_resultado_mercados))
    for i, mercado in df_resultado_mercados.iterrows():
        mostrar_value_bet(
            mercado["Mercado"], mercado["Probabilidade (%)"], mercado["Odd Justa"], cols[i])

    # Gráfico
    with st.expander("📊 Gráfico de Probabilidades por Mercado"):
        vw.grafico_mercados(df_resultado_mercados,
                            "Probabilidades (Poisson + BTTS)")

    # ----------------------------
    # ESCANTEIOS (NegBin)
    # ----------------------------
    st.markdown("## 🟦 Estimativa de Escanteios")
    linha_escanteios = st.sidebar.selectbox(
        "Linha de Escanteios (Over/Under):", [6.5, 7.5, 8.5, 9.5, 10.5, 11.5], index=3)
    st.session_state.linha_escanteios = linha_escanteios

    cantos = dt.prever_escanteios_nb(
        home_team, away_team, df_jogos, num_jogos=num_jogos_selecionado, scenario=selected_scenario)
    st.session_state.over_under_cantos = dt.calcular_over_under_cantos(
        cantos, linha_escanteios)
    mais_cantos = dt.prob_home_mais_cantos(cantos)

    col1, col2 = st.columns(2)
    col1.markdown(
        f"- Over {linha_escanteios}: **{st.session_state.over_under_cantos['p_over']}%**")
    col2.markdown(
        f"- Under {linha_escanteios}: **{st.session_state.over_under_cantos['p_under']}%**")

    col1, col2, col3 = st.columns(3)
    col1.metric("🏠 Mais Cantos", f"{mais_cantos['home_mais']}%")
    col2.metric("🤝 Empate", f"{mais_cantos['empate']}%")
    col3.metric("✈️ Mais Cantos", f"{mais_cantos['away_mais']}%")

    # Apoio histórico
    resultado_escanteios = dt.estimar_linha_escanteios(
        df_home, df_away, home_team, away_team)
    with st.expander("📋 Estatísticas Históricas de Escanteios"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Média Mandante",
                    f"{resultado_escanteios['Escanteios Mandante']:.2f}")
        col2.metric("Média Visitante",
                    f"{resultado_escanteios['Escanteios Visitante']:.2f}")
        col3.metric(
            "Média Total", f"{resultado_escanteios['Escanteios Totais Ajustados']:.2f}")

    # ----------------------------
    # ÚLTIMOS JOGOS
    # ----------------------------
    with st.expander("📋 Ver Últimos Jogos Analisados"):
        vw.mostrar_tabela_jogos(df_home, home_team, "🏠")
        vw.mostrar_tabela_jogos(df_away, away_team, "✈️")

    # ----------------------------
    # RELATÓRIO E SALVAMENTO
    # ----------------------------
    if st.sidebar.button("💾 Salvar Análise Atual"):
        current_analysis = {
            "Liga": selected_league,
            "Home": home_team,
            "Away": away_team,
            "Cenário": selected_scenario,
            "Jogos Analisados": f"{len(df_home)} vs {len(df_away)}",
            "Prob. Casa (%)": round(resultados["p_home"] * 100, 2),
            "Prob. Empate (%)": round(resultados["p_draw"] * 100, 2),
            "Prob. Visitante (%)": round(resultados["p_away"] * 100, 2),
            "Prob. Gol HT (%)": round(dt.prever_gol_ht(home_team, away_team, df_jogos, num_jogos=num_jogos_selecionado, scenario=selected_scenario)['p_gol_ht'], 2),
            "Prob. Over 1.5 (%)": df_resultado_mercados.loc[df_resultado_mercados['Mercado'] == "Over 1.5", "Probabilidade (%)"].iloc[0],
            "Prob. Over 2.5 (%)": df_resultado_mercados.loc[df_resultado_mercados['Mercado'] == "Over 2.5", "Probabilidade (%)"].iloc[0],
            "Prob. BTTS (%)": df_resultado_mercados.loc[df_resultado_mercados['Mercado'] == "BTTS", "Probabilidade (%)"].iloc[0],
            "Linha Escanteios": f"{linha_escanteios} ({st.session_state.over_under_cantos['p_over']}% over)"
        }
        st.session_state.saved_analyses.append(current_analysis)
        st.toast(
            f"✅ Análise de '{home_team} vs {away_team}' salva no relatório!")

    if st.session_state.saved_analyses:
        vw.exibir_relatorio(st.session_state.saved_analyses)
