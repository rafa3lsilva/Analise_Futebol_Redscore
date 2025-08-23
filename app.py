from services import carregar_dados
import streamlit as st
import pandas as pd
import data as dt
import sidebar as sb
import logging
from services import carregar_dados, carregar_base_historica
from data import prever_gols
from views import (
    mostrar_status_carregamento,
    mostrar_tabela_jogos,
    titulo_principal,
    mostrar_cards_media_gols,
    grafico_mercados,
    configurar_estilo_intervalo_jogos
)

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
titulo_principal()

# Importa a barra lateral
sb.sidebar()

# Filtros da Análise
st.sidebar.markdown("### 🔎 Filtros da Análise")
dia = sb.calendario()
with st.spinner("⏳ Carregando dados do GitHub..."):
    df_jogos, df_proximos_jogos, dia_br, dia_iso = carregar_dados(dia)

# Base histórica e próximo jogos
st.session_state.df_proximos_jogos = df_proximos_jogos
df_historico = carregar_base_historica()
st.session_state.df_jogos = df_historico

# Mensagens automáticas
mostrar_status_carregamento(df_proximos_jogos, dia_br, dia_iso)

# Dados em df e df_proximos session state
df = st.session_state.df_jogos
df_proximos = st.session_state.df_proximos_jogos

# Configura o estilo dos intervalos de jogos
configurar_estilo_intervalo_jogos()

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

    # Exibe as médias de gols
    media_home_gols_marcados = dt.media_gols_marcados(df_home, home_team)
    media_home_gols_sofridos = dt.media_gols_sofridos(df_home, home_team)
    media_away_gols_marcados = dt.media_gols_marcados(df_away, away_team)
    media_away_gols_sofridos = dt.media_gols_sofridos(df_away, away_team)

    # Exibe as médias de gols
    st.markdown("### 📋 Médias de Gols Home e Away", unsafe_allow_html=True)
    mostrar_cards_media_gols(
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
    resultados = prever_gols(home_team, away_team, df_jogos,    
                         num_jogos=num_jogos_selecionado, min_jogos=3)

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
        vencedor = "home"
    elif prob_away > prob_home and prob_away > prob_draw:
        vencedor = "away"
    else:
        vencedor = "Empate"

    cor = "#4CAF50" if vencedor == "home" else "#F44336" if vencedor == "away" else "#607D8B"

    st.markdown(
        f"""
        <div style='background-color:{cor};padding:10px;border-radius:8px'>
            <h3 style='color:white;text-align:center'>🏆 Vencedor Estimado: {vencedor}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Exibindo mais dados sobre os times
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

    # Analise de gol HT
    st.markdown("---")
    st.markdown("#### Análise de Gol no Primeiro Tempo (HT)",
                unsafe_allow_html=True)
    analise_ht_nova = dt.analise_gol_ht(df_home, df_away)

    # 2. Exibe o resultado principal da nova análise
    st.markdown(f"##### {analise_ht_nova['conclusao']}")

    # Exibe a probabilidade e a odd justa, se aplicável
    if analise_ht_nova['odd_justa'] > 0:
        st.success(
            f"Probabilidade Estimada (baseada nas médias): **{analise_ht_nova['probabilidade']:.1f}%**. "
            f"Odd Justa Mínima: **{analise_ht_nova['odd_justa']:.2f}**"
        )

    # Adiciona um expansor para mostrar os detalhes do cálculo
    with st.expander("Ver detalhes do cálculo"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Média de Over 0.5 HT",
                      f"{analise_ht_nova['media_05ht']:.1f}%")
        with col2:
            st.metric("Média de Over 1.5 FT",
                      f"{analise_ht_nova['media_15ft']:.1f}%")
        with col3:
            st.metric("Média de Over 2.5 FT",
                      f"{analise_ht_nova['media_25ft']:.1f}%")
        st.caption(
            "A probabilidade final é a média simples das três métricas acima.")

    # --- Painel de Apoio
    st.markdown(
        f"#### Estatísticas Individuais HT de {home_team} e {away_team}")

    # 1. Junta os dataframes de casa e fora para uma análise combinada
    df_total_ht = pd.concat([df_home, df_away], ignore_index=True)

    # 2. Chama a nova função que criámos em data.py
    desvio_padrao_ht = dt.analisar_consistencia_gols_ht(df_total_ht)

    # 3. Exibe a métrica e uma interpretação para o usuário
    st.markdown("##### 🎲 Consistência do Cenário para Gols HT")

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

    st.markdown("---")
    # Filtra os DataFrames para os últimos jogos
    df_home_final = df_home.head(num_jogos_home)
    df_away_final = df_away.head(num_jogos_away)

    df_resultado_mercados = dt.analisar_mercados(df_home_final, df_away_final)

    st.subheader(
        "🎯 Probabilidades por Mercado 🔎 Comparador de Valor (Value Bet)")

    # Cria colunas para cada mercado (Over 1.5, Over 2.5, BTTS)
    cols = st.columns(len(df_resultado_mercados))

    # Itera sobre cada coluna e cada mercado correspondente
    for i, col in enumerate(cols):
        with col:
            # Pega os dados do mercado atual (Over 1.5, Over 2.5, etc.)
            mercado = df_resultado_mercados.iloc[i]

            # Exibe a métrica com a probabilidade e a odd justa, como antes
            st.metric(
                label=mercado["Mercado"],
                value=f'{mercado["Probabilidade (%)"]}%',
                delta=f'Odd Justa: {mercado["Odd Justa"]}'
            )

            # Adiciona o campo para o utilizador inserir a odd do mercado
            odd_mercado = st.number_input(
                f"Odd Mercado para {mercado['Mercado']}",
                min_value=1.00,
                # Usa a odd justa como valor inicial para facilitar
                value=float(mercado['Odd Justa']),
                step=0.01,
                format="%.2f",
                # A 'key' é essencial para que cada campo seja único
                key=f"odd_mercado_{mercado['Mercado']}"
            )

            # Lógica para comparar e exibir se há valor
            if odd_mercado > mercado['Odd Justa']:
                valor_ev = (odd_mercado / mercado['Odd Justa'] - 1) * 100
                st.success(f"✅ Valor Encontrado: +{valor_ev:.2f}%")
            else:
                st.warning("Sem valor aparente.")

    # Gráfico de barras criando em views
    st.subheader("📈 Visualização Gráfica")
    grafico_mercados(df_resultado_mercados)
    st.markdown("---")

    # Estimativa de Escanteios
    st.markdown("### 📊 Estimativa de Escanteios", unsafe_allow_html=True)
    resultado_escanteios = dt.estimar_linha_escanteios(
        df_home_final, df_away_final, home_team, away_team)

    # Exibe as médias gerais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Média Cantos Mandante",
                  f"{resultado_escanteios['Escanteios Mandante']:.2f}")
    with col2:
        st.metric("Média Cantos Visitante",
                  f"{resultado_escanteios['Escanteios Visitante']:.2f}")
    with col3:
        st.metric("Média Total Ajustada",
                  f"{resultado_escanteios['Escanteios Totais Ajustados']:.2f}")

    st.markdown("#### Probabilidades por Linha de Mercado")

    # Transforma a lista de resultados em um DataFrame
    df_escanteios = pd.DataFrame(
        resultado_escanteios['Probabilidades por Mercado'])

    # Define quantas colunas você quer por linha
    num_colunas = 4
    # Cria as colunas na primeira linha
    cols = st.columns(num_colunas)

    # Itera sobre cada mercado para exibir a métrica
    for i, row in df_escanteios.iterrows():
        # Usa o operador de módulo (%) para encontrar a coluna correta (de 0 a 3)
        col_index = i % num_colunas
        with cols[col_index]:
            # Exibe a métrica
            st.metric(
                label=row['Mercado'], value=f"{row['Probabilidade (%)']}%", delta=f"Odd Justa: {row['Odd Justa']}")

        # Se chegamos na última coluna da linha atual (e não é o último item), cria uma nova linha de colunas
        if col_index == num_colunas - 1 and i < len(df_escanteios) - 1:
            cols = st.columns(num_colunas)
    st.markdown("---")

    # Tabela de Jogos home e away
    mostrar_tabela_jogos(df_home, home_team, "🏠")
    mostrar_tabela_jogos(df_away, away_team, "✈️")

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
        "Prob. Gol HT (%)": round(analise_ht_nova['probabilidade'], 2),
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
