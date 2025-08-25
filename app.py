from services import carregar_dados
import streamlit as st
import pandas as pd
import data as dt
import sidebar as sb
import logging
import services as sv
import views as vw

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if "saved_analyses" not in st.session_state:
    st.session_state.saved_analyses = []
if "dados_jogos" not in st.session_state:
    st.session_state.dados_jogos = None
if "df_jogos" not in st.session_state:
    st.session_state.df_jogos = pd.DataFrame()
# Adicione esta linha se a sua lógica de toast a utilizar
if "data_loaded_successfully" not in st.session_state:
    st.session_state.data_loaded_successfully = False

# Função para configurar a página Streamlit
st.set_page_config(
    page_title="Análise Futebol",
    page_icon=":soccer:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título principal
vw.titulo_principal()

# Importa a barra lateral
sb.sidebar()

# Filtros da Análise
st.sidebar.markdown("### 🔎 Filtros da Análise")
dia = sb.calendario()
with st.spinner("⏳ Carregando dados do GitHub..."):
    df_jogos, df_proximos_jogos, dia_br, dia_iso = carregar_dados(dia)

# Base histórica e próximo jogos
st.session_state.df_proximos_jogos = df_proximos_jogos
df_historico = sv.carregar_base_historica()
st.session_state.df_jogos = df_historico

# Mensagens automáticas
vw.mostrar_status_carregamento(df_proximos_jogos, dia_br, dia_iso)

# Dados em df e df_proximos session state
df = st.session_state.df_jogos
df_proximos = st.session_state.df_proximos_jogos

# Configura o estilo dos intervalos de jogos
vw.configurar_estilo_intervalo_jogos()

# Filtros na sidebar
if not df.empty and not df_proximos.empty:
    # Filtro 1: Hora
    horarios_disponiveis = sorted(df_proximos['hora'].unique())
    selected_time = st.sidebar.selectbox(
        "Selecione o Horário:", horarios_disponiveis)

    # Filtra os dados com base na hora selecionada
    jogos_filtrado_hora = df_proximos[df_proximos['hora'] == selected_time]

    # Filtro 2: Liga (as opções dependem da hora escolhida)
    ligas_disponiveis = sorted(jogos_filtrado_hora['liga'].unique())
    selected_league = st.sidebar.selectbox(
        "Selecione a Liga:", ligas_disponiveis)

    # Filtra novamente com base na liga
    jogos_filtrado_liga = jogos_filtrado_hora[jogos_filtrado_hora['liga']
                                              == selected_league]

    # Filtro 3: Confronto (as opções dependem da hora e da liga)
    confrontos_disponiveis = sorted(jogos_filtrado_liga['confronto'].unique())
    selected_game = st.sidebar.selectbox(
        "Escolha o Jogo:", confrontos_disponiveis)

    # Com base na seleção, extrai os nomes das equipas para a análise
    selected_game_data = jogos_filtrado_liga[jogos_filtrado_liga['confronto'] == selected_game]

    if selected_game_data.empty:
        st.warning("Por favor, selecione um jogo válido para iniciar a análise.")
        st.stop()

    home_team = selected_game_data['home'].iloc[0]
    away_team = selected_game_data['away'].iloc[0]

    # ✅ Filtro de Cenário
    selected_scenario = st.sidebar.selectbox(
        "Cenário de Análise:",
        ["Geral", "Casa/Fora"],
        help="Geral: analisa todos os jogos de cada time. Casa/Fora: analisa apenas jogos em casa do mandante e fora do visitante."
    )

    # Cria os DataFrames de dados históricos com base no cenário escolhido
    if selected_scenario == 'Geral':
        df_home_base = df[(df['Home'].str.lower() == home_team.lower()) | (
            df['Away'].str.lower() == home_team.lower())].copy().reset_index(drop=True)
        df_away_base = df[(df['Home'].str.lower() == away_team.lower()) | (
            df['Away'].str.lower() == away_team.lower())].copy().reset_index(drop=True)
    else:  # Cenário 'Casa/Fora'
        df_home_base = df[df['Home'].str.lower(
        ) == home_team.lower()].copy().reset_index(drop=True)
        df_away_base = df[df['Away'].str.lower(
        ) == away_team.lower()].copy().reset_index(drop=True)

    # Ordena os DataFrames pela data
    df_home_base = df_home_base.sort_values(
        by='Data', ascending=False).reset_index(drop=True)
    df_away_base = df_away_base.sort_values(
        by='Data', ascending=False).reset_index(drop=True)

    # --- Filtro de Intervalo de jogos ---
    with st.container():
        st.markdown("### 📅 Intervalo de Jogos")
        intervalo = st.radio(
            "",
            options=["Últimos 5 jogos", "Últimos 6 jogos",
                     "Últimos 8 jogos", "Últimos 10 jogos"],
            index=1,
            horizontal=True
        )
    num_jogos_selecionado = int(intervalo.split()[1])

    # Ajusta o número de jogos se o usuário pedir mais do que o disponível
    num_jogos_home = min(num_jogos_selecionado, len(df_home_base))
    num_jogos_away = min(num_jogos_selecionado, len(df_away_base))

    # Pega os N primeiros jogos (os mais recentes, pois já ordenámos no início) para a análise final
    df_home = df_home_base.head(num_jogos_home)
    df_away = df_away_base.head(num_jogos_away)

    # Ajustes com base em pesos
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    with st.sidebar.expander("⚙️ Ajustar Pesos do Modelo"):
        limite_consistente = st.slider(
            "Nível 'Consistente' (DP ≤)",
            min_value=0.1, max_value=2.0, value=0.8, step=0.1,
            help="Qual o valor máximo do Desvio Padrão para considerar um cenário como consistente."
        )
        limite_imprevisivel = st.slider(
            "Nível 'Imprevisível' (DP >)",
            min_value=0.1, max_value=2.0, value=1.2, step=0.1,
            help="A partir de qual valor de Desvio Padrão um cenário deve ser considerado imprevisível."
        )

    analise = dt.analisar_cenario_partida(
    home_team,
    away_team,
    df_jogos,
    num_jogos=num_jogos_selecionado,
    scenario=selected_scenario,
    linha_gols=2.5
    )

    if "erro" in analise:
        # Se sim, exibe o aviso e para a execução
        st.warning(f"⚠️ {analise['erro']}")
        st.stop()
        
    # Título principal
    st.markdown(f"#### 📊 Cenário da Partida ({analise['cenario_usado']})")
    # Probabilidades de resultado em colunas
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"### 🏠 {home_team} \n Probabilidade de vitória: **{analise['prob_home']}%**")
    col2.markdown(f"### 🤝 Empate\n Probabilidade de empate: **{analise['prob_draw']}%**")
    col3.markdown(f"### ✈️ {away_team} \n Probabilidade de vitória: **{analise['prob_away']}%**")

    # Over/Under
    st.markdown("#### 📊 Cenário da Partida Over/Under")
    col4, col5 = st.columns(2)
    col4.markdown(
        f"🔼 Over {analise['over_under']['linha']} gols\n**{analise['over_under']['p_over']}%**")
    col5.markdown(
        f"🔽 Under {analise['over_under']['linha']} gols\n**{analise['over_under']['p_under']}%**")
    
    # BTTS (Ambos marcam)
    st.markdown("#### ⚽ Cenário da Partida BTTS")
    col6, col7 = st.columns(2)
    col6.markdown(f"✅ BTTS: Sim\n**{analise['btts']['p_btts_sim']}%**")
    col7.markdown(f"❌ BTTS: Não\n**{analise['btts']['p_btts_nao']}%**")

    st.markdown("### 🔮 Top 5 Placares Mais Prováveis")
    cols = st.columns(5)
    for idx, p in enumerate(analise['placares_top']):
        with cols[idx]:
            st.markdown(f"""
            <div style="background-color:#1f2937; padding:15px; border-radius:8px; text-align:center; color:white;">
                <h3 style="margin:0;">{p['placar']}</h3>
                <p style="font-size:18px; margin:0;">{p['prob']}%</p>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("---")

    # Exibe as médias de gols
    media_home_gols_marcados = dt.media_gols_marcados(df_home, home_team)
    media_home_gols_sofridos = dt.media_gols_sofridos(df_home, home_team)
    media_away_gols_marcados = dt.media_gols_marcados(df_away, away_team)
    media_away_gols_sofridos = dt.media_gols_sofridos(df_away, away_team)

    # Exibe as médias de gols
    st.markdown("### 📋 Médias de Gols Home e Away", unsafe_allow_html=True)
    vw.mostrar_cards_media_gols(
        home_team,
        away_team,
        media_home_gols_marcados,
        media_home_gols_sofridos,
        media_away_gols_marcados,
        media_away_gols_sofridos
    )

    # Taxa de Vitórias home
    df_home['resultado'] = df_home['H_Gols_FT'] > df_home['A_Gols_FT']
    vitoria = df_home[df_home['resultado'] == 1].shape[0]
    tx_vitoria = (vitoria / num_jogos_selecionado) * 100

    # Taxa de Vitórias away
    df_away['resultado'] = df_away['A_Gols_FT'] > df_away['H_Gols_FT']
    vitoria_away = df_away[df_away['resultado'] == 1].shape[0]
    tx_vitoria_away = (vitoria_away / num_jogos_selecionado) * 100

    # Calcula previsões
    resultados = dt.prever_gols(home_team, away_team, df_jogos,
                             num_jogos=num_jogos_selecionado,
                             min_jogos=3,
                             scenario=selected_scenario)

    # converte para %
    prob_home = round(resultados["p_home"] * 100, 2)
    prob_draw = round(resultados["p_draw"] * 100, 2)
    prob_away = round(resultados["p_away"] * 100, 2)

    # odds justas (sem margem de bookmaker)
    odd_home = round(1 / max(resultados["p_home"], 1e-6), 2)
    odd_draw = round(1 / max(resultados["p_draw"], 1e-6), 2)
    odd_away = round(1 / max(resultados["p_away"], 1e-6), 2)

    # define provável vencedor
    if prob_home > prob_away and prob_home > prob_draw:
        vencedor = home_team
    elif prob_away > prob_home and prob_away > prob_draw:
        vencedor = away_team
    else:
        vencedor = "Empate"

    cor = "#4CAF50" if vencedor == home_team else "#F44336" if vencedor == away_team else "#607D8B"

    st.markdown(
        f"""
        <div style='background-color:{cor};padding:10px;border-radius:8px'>
            <h3 style='color:white;text-align:center'>🏆 Vencedor Estimado: {vencedor}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Exibindo mais dados sobre os times
    st.markdown("---")
    with st.expander("## ⚙️ Detalhes Adicionais e Comparador de Valor"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"### 🏠 {home_team}")
            st.metric("Probabilidade de Vitória", f"{prob_home}%")
            st.metric("Odds Justas", f"{odd_home:.2f}")
            st.write("Taxa de Vitórias", f"{tx_vitoria:.2f}%")
            st.write(f"Gols esperados: {home_team}: {resultados['lambda_home']:.2f}")
        with col2:
            st.markdown("### ⚖️ Empate")
            st.metric("Probabilidade de Empate", f"{prob_draw}%")
            st.metric("Odds Justas", f"{odd_draw:.2f}")
        with col3:
            st.markdown(f"### ✈️ {away_team}")
            st.metric("Probabilidade de Vitória", f"{prob_away}%")
            st.metric("Odds Justas", f"{odd_away:.2f}")
            st.write("Taxa de Vitórias", f"{tx_vitoria_away:.2f}%")
            st.write(f"Gols esperados: {away_team}: {resultados['lambda_away']:.2f}")
        
        st.markdown("---")
        st.subheader("🔍 Comparador de Valor (Value Bet)")
        st.write(
            "Insira as odds do mercado para comparar com as odds justas calculadas pelo modelo.")

        # Criar colunas para os inputs
        col_val1, col_val2, col_val3 = st.columns(3)
        with col_val1:
            odd_mercado_home = st.number_input(
                f"Odd Mercado para {home_team}", min_value=1.00, value=odd_home, step=0.01)
        with col_val2:
            odd_mercado_draw = st.number_input(
                "Odd Mercado para Empate", min_value=1.00, value=odd_draw, step=0.01)
        with col_val3:
            odd_mercado_away = st.number_input(
                f"Odd Mercado para {away_team}", min_value=1.00, value=odd_away, step=0.01)

        # Lógica para exibir se há valor
        with col_val1:
            if odd_mercado_home > odd_home:
                valor_home = (odd_mercado_home / odd_home - 1) * 100
                st.success(f"✅ Valor Encontrado: +{valor_home:.2f}%")
            else:
                st.warning("Sem valor aparente.")

        with col_val2:
            if odd_mercado_draw > odd_draw:
                valor_draw = (odd_mercado_draw / odd_draw - 1) * 100
                st.success(f"✅ Valor Encontrado: +{valor_draw:.2f}%")
            else:
                st.warning("Sem valor aparente.")

        with col_val3:
            if odd_mercado_away > odd_away:
                valor_away = (odd_mercado_away / odd_away - 1) * 100
                st.success(f"✅ Valor Encontrado: +{valor_away:.2f}%")
            else:
                st.warning("Sem valor aparente.")

    st.markdown("---")
    # Analise de gol HT
    st.markdown("## 🕐 Gol no 1º Tempo")
    # 🎯 Modelo probabilístico (Poisson)
    ht = dt.prever_gol_ht(
        home_team, away_team, df_jogos,
        num_jogos=num_jogos_selecionado,
        scenario=selected_scenario
    )
    st.markdown(f"### Probabilidades com base no Modelo Poisson")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"- Over 0.5 HT: **{ht['p_gol_ht']}%**")
    with col2:
        st.markdown(f"- Exatamente 1 gol no HT: **{ht['p_exato1_ht']}%**")

    # Histórico de apoio
    analise_ht_hist = dt.analise_gol_ht(df_home, df_away)
    with st.expander("📋 Estatística de apoio para gols no 1º tempo, usando médias históricas com base nos últimos jogos"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Média Over 0.5 HT", f"{analise_ht_hist['media_05ht']:.1f}%")
        with col2:
            st.metric("Média Over 1.5 FT", f"{analise_ht_hist['media_15ft']:.1f}%")
        with col3:
            st.metric("Média Over 2.5 FT", f"{analise_ht_hist['media_25ft']:.1f}%")

        # 1. Junta os dataframes de casa e fora para uma análise combinada
        df_total_ht = pd.concat([df_home, df_away], ignore_index=True)

        # 2. Chama a nova função que criámos em data.py
        desvio_padrao_ht = dt.analisar_consistencia_gols_ht(df_total_ht)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Desvio Padrão dos Gols HT", f"{desvio_padrao_ht:.2f}")

        with col2:
            if desvio_padrao_ht == 0.0:
                interpretacao = "ℹ️ Dados insuficientes."
            elif desvio_padrao_ht <= limite_consistente: 
                interpretacao = "✅ **Cenário Consistente:** A quantidade de gols no HT nos jogos destas equipas tende a ser muito previsível."
            elif desvio_padrao_ht <= limite_imprevisivel:
                interpretacao = "⚠️ **Cenário Moderado:** Há alguma variação na quantidade de gols no HT, mas ainda com alguma previsibilidade."
            else:
                interpretacao = "🚨 **Cenário Imprevisível:** A quantidade de gols no HT varia muito de jogo para jogo. É um cenário de 'altos e baixos'."

            st.info(interpretacao)

        # Análise de Gol no Primeiro Tempo (HT)
        analise_ht = dt.analisar_gol_ht_home_away(df_home, df_away)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Análise de {home_team}:**")
            st.info(
                f"Marcou gol no HT em **{analise_ht['home_marca']:.1f}%** dos seus jogos.")
            st.warning(
                f"Sofreu gol no HT em **{analise_ht['home_sofre']:.1f}%** dos seus jogos.")

        with col2:
            st.markdown(f"**Análise de {away_team}:**")
            st.info(
                f"Marcou gol no HT em **{analise_ht['away_marca']:.1f}%** dos seus jogos.")
            st.warning(
                f"Sofreu gol no HT em **{analise_ht['away_sofre']:.1f}%** dos seus jogos.")

    # Filtra os DataFrames para os últimos jogos
    df_home_final = df_home.head(num_jogos_home)
    df_away_final = df_away.head(num_jogos_away)

    # --- MERCADO DE GOLS ---
    st.markdown("## 🎯 Mercado de Gols (FT)")

    # 🎯 Probabilidades principais (Poisson)
    linha_gols = st.sidebar.selectbox(
        "Linha de Gols (Over/Under)",
        [1.5, 2.5, 3.5],
        index=1
    )
    over_under = dt.calcular_over_under(resultados, linha=linha_gols)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"- 🔼 Over {linha_gols}: **{over_under['p_over']}%**")
    with col2:
        st.markdown(f"- 🔽 Under {linha_gols}: **{over_under['p_under']}%**")

    # --- Probabilidades por Mercado (Poisson) ---
    linha_over15 = dt.calcular_over_under(resultados, linha=1.5)
    linha_over25 = dt.calcular_over_under(resultados, linha=2.5)
    linha_over35 = dt.calcular_over_under(resultados, linha=3.5)
    btts = dt.calcular_btts(resultados)

    # Monta DataFrame direto do modelo Poisson
    df_resultado_mercados = pd.DataFrame([
        {"Mercado": "Over 1.5", "Probabilidade (%)": linha_over15['p_over'], "Odd Justa": round(
            100/linha_over15['p_over'], 2)},
        {"Mercado": "Over 2.5", "Probabilidade (%)": linha_over25['p_over'], "Odd Justa": round(
            100/linha_over25['p_over'], 2)},
        {"Mercado": "Over 3.5", "Probabilidade (%)": linha_over35['p_over'], "Odd Justa": round(
            100/linha_over35['p_over'], 2)},
        {"Mercado": "BTTS", "Probabilidade (%)": btts['p_btts_sim'], "Odd Justa": round(
            100/btts['p_btts_sim'], 2)},
    ])

    st.subheader(
        "🎯 Probabilidades por Mercado (Poisson) 🔎 Comparador de Valor")

    cols = st.columns(len(df_resultado_mercados))
    for i, col in enumerate(cols):
        with col:
            mercado = df_resultado_mercados.iloc[i]
            st.metric(
                label=mercado["Mercado"],
                value=f'{mercado["Probabilidade (%)"]}%',
                delta=f'Odd Justa: {mercado["Odd Justa"]}'
            )

            odd_mercado = st.number_input(
                f"Odd Mercado para {mercado['Mercado']}",
                min_value=1.00,
                value=float(mercado['Odd Justa']),
                step=0.01,
                format="%.2f",
                key=f"odd_mercado_{mercado['Mercado']}"
            )

            if odd_mercado > mercado['Odd Justa']:
                valor_ev = (odd_mercado / mercado['Odd Justa'] - 1) * 100
                st.success(f"✅ Valor Encontrado: +{valor_ev:.2f}%")
            else:
                st.warning("Sem valor aparente.")
    st.markdown("---")
    # Gráfico de barras para as probabilidades por mercado
    with st.expander("📊 Gráfico de Probabilidades por Mercado"):
        vw.grafico_mercados(df_resultado_mercados,
                         titulo="Probabilidades (Poisson + BTTS)")

    # --- Linha Over/Under de Escanteios ---
    st.sidebar.markdown("### 📊 Linha de Escanteios (Over/Under)")
    linha_escanteios = st.sidebar.selectbox(
        "Selecione a linha de escanteios:",
        [6.5, 7.5, 8.5, 9.5, 10.5, 11.5],
        index=3
    )
    st.session_state.linha_escanteios = linha_escanteios

    # Calcula probabilidades de escanteios
    cantos = dt.prever_escanteios_nb(home_team, away_team, df_jogos,
                                num_jogos=num_jogos_selecionado, scenario=selected_scenario)

    # Probabilidades Over/Under
    st.session_state.over_under_cantos = dt.calcular_over_under_cantos(
        cantos, st.session_state.linha_escanteios)

    # Quem tem mais cantos
    mais_cantos = dt.prob_home_mais_cantos(cantos)

    # --- ESCANTEIOS ---
    st.markdown("## 🟦 Estimativa de Escanteios")

    # 🎯 Modelo principal (NegBin)
    cantos = dt.prever_escanteios_nb(
        home_team, away_team, df_jogos,
        num_jogos=num_jogos_selecionado,
        scenario=selected_scenario
    )
    st.session_state.over_under_cantos = dt.calcular_over_under_cantos(
        cantos, st.session_state.linha_escanteios
    )
    mais_cantos = dt.prob_home_mais_cantos(cantos)

    st.markdown("### Probabilidades (Modelo NegBin)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"- Over {st.session_state.linha_escanteios}: **{st.session_state.over_under_cantos['p_over']}%**")
    with col2:
        st.markdown(
            f"- Under {st.session_state.linha_escanteios}: **{st.session_state.over_under_cantos['p_under']}%**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"- 🏠 Home mais cantos: **{mais_cantos['home_mais']}%**")
    with col2:
        st.markdown(f"- 🤝 Empate em cantos: **{mais_cantos['empate']}%**")
    with col3:
        st.markdown(f"- ✈️ Away mais cantos: **{mais_cantos['away_mais']}%**")

    # 📊 Apoio: médias históricas
    resultado_escanteios = dt.estimar_linha_escanteios(
        df_home, df_away, home_team, away_team)
    with st.expander("📋 Estatísticas Históricas de Escanteios"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Média Cantos Mandante",
                    f"{resultado_escanteios['Escanteios Mandante']:.2f}")
        with col2:
            st.metric("Média Cantos Visitante",
                    f"{resultado_escanteios['Escanteios Visitante']:.2f}")
        with col3:
            st.metric("Média Total de Cantos",
                f"{resultado_escanteios['Escanteios Totais Ajustados']:.2f}")


    # Tabela de Jogos home e away
    with st.expander("📋 Ver Últimos Jogos Analisados"):
        vw.mostrar_tabela_jogos(df_home, home_team, "🏠")
        vw.mostrar_tabela_jogos(df_away, away_team, "✈️")

    # Botão para salvar análise atual
if st.sidebar.button("💾 Salvar Análise Atual"):
    # 1. Extrai os dados dos mercados e escanteios
    prob_over_1_5 = df_resultado_mercados.loc[
        df_resultado_mercados['Mercado'] == 'Over 1.5', 'Probabilidade (%)'
    ].iloc[0]
    prob_over_2_5 = df_resultado_mercados.loc[
        df_resultado_mercados['Mercado'] == 'Over 2.5', 'Probabilidade (%)'
    ].iloc[0]
    prob_btts = df_resultado_mercados.loc[
        df_resultado_mercados['Mercado'] == 'BTTS', 'Probabilidade (%)'
    ].iloc[0]

    df_escanteios = pd.DataFrame(
        resultado_escanteios['Probabilidades por Mercado'])
    linha_mais_provavel = df_escanteios.loc[df_escanteios['Probabilidade (%)'].idxmax(
    )]
    linha_escanteio_str = f"{linha_mais_provavel['Mercado']} ({linha_mais_provavel['Probabilidade (%)']:.1f}%)"

    # 2. Monta dicionário da análise
    current_analysis = {
        # "País": selected_country,
        "Liga": selected_league,
        "Home": home_team,
        "Away": away_team,
        "Cenário": selected_scenario,
        "Jogos Analisados": f"{len(df_home)} vs {len(df_away)}",
        "Prob. Casa (%)": prob_home,
        "Prob. Empate (%)": prob_draw,
        "Prob. Visitante (%)": prob_away,
        "Prob. Gol HT (%)": round(ht['p_gol_ht'], 2),
        "Prob. Over 1.5 (%)": prob_over_1_5,
        "Prob. Over 2.5 (%)": prob_over_2_5,
        "Prob. BTTS (%)": prob_btts,
        "Linha Escanteios": linha_escanteio_str,
    }

    # 3. Salva no relatório
    st.session_state.saved_analyses.append(current_analysis)
    st.toast(f"✅ Análise de '{home_team} vs {away_team}' salva no relatório!")

# --- Relatório de análises salvas ---
if st.session_state.saved_analyses:
    st.sidebar.markdown("---")
    st.sidebar.header("📋 Relatório de Análises")

    num_saved = len(st.session_state.saved_analyses)
    st.sidebar.info(f"Você tem **{num_saved}** análise(s) salva(s).")

    df_report = pd.DataFrame(st.session_state.saved_analyses)

    # Função para converter para Excel
    @st.cache_data
    def to_excel(df):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Analises')
        return output.getvalue()

    excel_data = to_excel(df_report)

    # Botão de download
    st.sidebar.download_button(
        label="📥 Baixar Relatório (Excel)",
        data=excel_data,
        file_name="relatorio_analises.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Botão para limpar
    if st.sidebar.button("🗑️ Limpar Análises Salvas"):
        st.session_state.saved_analyses = []
        st.rerun()

    # Expansor para ver as análises
    with st.sidebar.expander("Ver análises salvas"):
        st.dataframe(df_report)
