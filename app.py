import streamlit as st
import pandas as pd
import altair as alt
import data as dt
import sidebar as sb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Descrição
st.markdown("""
<div  style="text-align: center; font-size: 16px;">
    <p style='text-align: center;'>Esta é uma aplicação para análise de jogos de futebol usando dados do site Redscore.</p>
    <p style='text-align: center;'>Você pode fazer upload de arquivos .txt com os dados dos jogos e obter análises detalhadas.</p>
    <p style='text-align: center;'>Para mais informações, consulte o tutorial na barra lateral.</p>
</div>
""", unsafe_allow_html=True)

# Importa a barra lateral
sb.sidebar()

# Inicializa o estado
if "dados_jogos" not in st.session_state:
    st.session_state.dados_jogos = None
if "df_jogos" not in st.session_state:
    st.session_state.df_jogos = pd.DataFrame()

# Upload do arquivo (só aparece se ainda não foi carregado)
if not st.session_state.dados_jogos:
    uploaded_file = st.file_uploader(
        "📁 Escolha o arquivo .txt com os dados dos jogos", type="txt")
    if uploaded_file:
        try:
            linhas = uploaded_file.read().decode("utf-8").splitlines()
            linhas = [linha.strip() for linha in linhas if linha.strip()]
            if len(linhas) < 20:
                st.error(
                    "Arquivo com poucos dados. Verifique se o arquivo contém informações suficientes de jogos.")
            else:
                df_temp = dt.extrair_dados(linhas)
                if df_temp.empty:
                    st.error("Não foi possível extrair dados válidos do arquivo.")
                else:
                    st.session_state.dados_jogos = linhas
                    st.session_state.df_jogos = df_temp
                    st.rerun()
        except UnicodeDecodeError:
            st.error(
                "Erro ao ler o arquivo. Certifique-se de que está em formato .txt e codificação UTF-8.")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")


# Só chama extrair_dados se houver dados válidos
df = pd.DataFrame()
if st.session_state.dados_jogos:
    df = dt.extrair_dados(st.session_state.dados_jogos)

if st.session_state.dados_jogos:
       if st.sidebar.button("🔄 Novo Arquivo"):
            st.session_state.dados_jogos = None
            st.session_state.df_jogos = pd.DataFrame()
            st.rerun()

# Exibe os dados apenas se o DataFrame não estiver vazio
if not df.empty:
    st.markdown("""
    <style>
    div[role='radiogroup'] > label {
        background-color: #262730;
        color: white;
        margin-top: -60px;
        border-radius: 12px;
        padding: 4px 12px;
        margin-right: 8px;
        cursor: pointer;
        border: 1px solid transparent;
        transition: all 0.2s ease-in-out;
    }
    div[role='radiogroup'] > label:hover {
        background-color: #ff4b4b;
    }
    div[role='radiogroup'] > label[data-selected="true"] {
        background-color: #ff4b4b;
        border-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

if not df.empty:
    # --- Bloco de Filtros da Sidebar---
    st.sidebar.markdown("### Filtros da Análise")

    # Filtros de Liga e Times
    leagues = sorted(df['Liga'].unique())
    all_teams = sorted(pd.unique(df[['Home', 'Away']].values.ravel('K')))

    selected_league = st.sidebar.selectbox(
        'Filtrar Liga:', ['Todas'] + leagues)

    home_index = 0
    away_index = 1 if len(all_teams) > 1 else 0
    selected_home_team = st.sidebar.selectbox(
        'Time da Casa:', all_teams, index=home_index)
    selected_away_team = st.sidebar.selectbox(
        'Time Visitante:', all_teams, index=away_index)

    # Filtro de Cenário
    selected_scenario = st.sidebar.selectbox(
        'Cenário de Análise:',
        ['Geral', 'Casa/Fora'],
        help="Geral: analisa todos os jogos de cada time. Casa/Fora: analisa apenas jogos em casa do mandante e fora do visitante."
    )

    # Validação para garantir que os times selecionados não sejam iguais
    if selected_home_team == selected_away_team:
        st.sidebar.error("O time da casa e o visitante não podem ser iguais.")
        st.stop()

    # Filtra o DataFrame principal pela liga selecionada
    df_filtrado_liga = df.copy()
    if selected_league != 'Todas':
        df_filtrado_liga = df_filtrado_liga[df_filtrado_liga['Liga']
                                            == selected_league]

    # Cria os DataFrames com base no cenário escolhido
    if selected_scenario == 'Geral':
        # Cenário Geral: Pega todos os jogos de cada time
        df_home_base = df_filtrado_liga[(df_filtrado_liga['Home'] == selected_home_team) | (
            df_filtrado_liga['Away'] == selected_home_team)].copy().reset_index(drop=True)
        df_away_base = df_filtrado_liga[(df_filtrado_liga['Home'] == selected_away_team) | (
            df_filtrado_liga['Away'] == selected_away_team)].copy().reset_index(drop=True)
    else:  # Cenário 'Casa/Fora'
        # Cenário Específico: Pega apenas jogos em casa do mandante e fora do visitante
        df_home_base = df_filtrado_liga[df_filtrado_liga['Home']
                                        == selected_home_team].copy().reset_index(drop=True)
        df_away_base = df_filtrado_liga[df_filtrado_liga['Away']
                                        == selected_away_team].copy().reset_index(drop=True)

    # --- 2. FILTRO DE INTERVALO DE JOGOS (ÚLTIMOS N JOGOS) ---
    with st.container():
        st.markdown("### 📅 Intervalo de Jogos")
        intervalo = st.radio(
            "",
            options=["Últimos 5 jogos", "Últimos 8 jogos",
                     "Últimos 10 jogos", "Últimos 12 jogos"],
            index=2,
            horizontal=True
        )
    num_jogos_selecionado = int(intervalo.split()[1])

    # Ajusta o número de jogos se o usuário pedir mais do que o disponível
    num_jogos_home = min(num_jogos_selecionado, len(df_home_base))
    num_jogos_away = min(num_jogos_selecionado, len(df_away_base))

    # Pega os N primeiros jogos (os mais recentes do arquivo) para a análise final
    df_home = df_home_base.head(num_jogos_home)
    df_away = df_away_base.head(num_jogos_away)

    # Define os nomes dos times para usar nos títulos das análises
    home_team = selected_home_team
    away_team = selected_away_team

    # Validação final para garantir que há dados para analisar
    if df_home.empty or df_away.empty:
        st.warning(
            "Não há dados suficientes para a análise com os filtros selecionados. Por favor, ajuste as opções.")
        st.stop()

    st.sidebar.markdown("<br>",unsafe_allow_html=True)
    with st.sidebar.expander("⚙️ Ajustar Pesos do Modelo"):
        st.markdown(
            "Ajuste a importância de cada atributo para o cálculo do vencedor.")
        peso_ataques = st.slider("Peso dos Ataques", 0.0, 1.0, 0.2)
        peso_chutes = st.slider("Peso dos Chutes", 0.0, 1.0, 0.3)
        peso_chutes_gol = st.slider("Peso dos Chutes a Gol", 0.0, 2.0, 0.5)
        peso_gols = st.slider("Peso dos Gols", 0.0, 3.0, 1.5)
        peso_eficiencia = st.slider("Peso da Eficiência (%)", 0.0, 5.0, 2.0)
        fator_casa = st.slider("Fator Casa (Multiplicador)",
                            1.0, 1.5, 1.05)  # Alterado para multiplicador

        # Crie o dicionário de pesos
        pesos_modelo = {
            'ataques': peso_ataques,
            'chutes': peso_chutes,
            'chutes_gol': peso_chutes_gol,
            'gols': peso_gols,
            'eficiencia': peso_eficiencia,
            'fator_casa': fator_casa
        }

    # Exibe as médias de gols
    media_home_gols_marcados = dt.media_home_gols_feitos(df_home)
    media_home_gols_sofridos = dt.media_home_gols_sofridos(df_home)
    media_away_gols_marcados = dt.media_away_gols_feitos(df_away)
    media_away_gols_sofridos = dt.media_away_gols_sofridos(df_away)

    #exibe as médias de gols
    st.markdown("### 📋 Médias de Gols Home e Away", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="background-color:#1f77b4; padding:15px; border-radius:8px; text-align:center; color:white;">
            <h3>🏠 {home_team}</h3>
            <p style="font-size:18px;">⚽ Média de Gols Marcados: <strong>{media_home_gols_marcados:.2f}</strong></p>
            <p style="font-size:18px;">🛡️ Média de Gols Sofridos: <strong>{media_home_gols_sofridos:.2f}</strong></p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background-color:#d62728; padding:15px; border-radius:8px; text-align:center; color:white;">
            <h3>✈️ {away_team}</h3>
            <p style="font-size:18px;">⚽ Média de Gols Marcados: <strong>{media_away_gols_marcados:.2f}</strong></p>
            <p style="font-size:18px;">🛡️ Média de Gols Sofridos: <strong>{media_away_gols_sofridos:.2f}</strong></p>
        </div>
        <br>
        """, unsafe_allow_html=True)

    # Taxa de Vitórias home
    df_home['resultado'] = df_home['H_Gols_FT'] > df_home['A_Gols_FT']
    vitoria = df_home[df_home['resultado'] == 1].shape[0]
    tx_vitoria = (vitoria / num_jogos_selecionado) * 100

    # Taxa de Vitórias away
    df_away['resultado'] = df_away['A_Gols_FT'] > df_away['H_Gols_FT']
    vitoria_away = df_away[df_away['resultado'] == 1].shape[0]
    tx_vitoria_away = (vitoria_away / num_jogos_selecionado) * 100

    # Calcula os dados
    vencedor, score_home, score_away, prob_home, prob_away, prob_draw, odd_home, odd_away, odd_draw = dt.estimar_vencedor(
        df_home, df_away, pesos_modelo)

    if vencedor == 'home':
        vencedor = home_team
    elif vencedor == 'away':
        vencedor = away_team
    else:
        vencedor = 'Empate'

    cor = "#4CAF50" if vencedor == home_team else "#F44336" if vencedor == away_team else "#607D8B"

    st.markdown(
        f"""
        <div style='background-color:{cor};padding:10px;border-radius:8px'>
            <h3 style='color:white;text-align:center'>🏆 Vencedor Estimado: {vencedor}</h3>
        </div>
        """,
        unsafe_allow_html=True
)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"### 🏠 {home_team}")
        st.metric("Probabilidade de Vitória", f"{prob_home}%")
        st.metric("Odds Justas", f"{odd_home:.2f}")
        st.write("Pontuação Ofensiva",f"{score_home}")
        st.write("Taxa de Vitórias", f"{tx_vitoria:.2f}%")
    with col2:
        st.markdown("### ⚖️ Empate")
        st.metric("Probabilidade de Empate", f"{prob_draw}%")
        st.metric("Odds Justas", f"{odd_draw:.2f}")
    with col3:
        st.markdown(f"### ✈️ {away_team}")
        st.metric("Probabilidade de Vitória", f"{prob_away}%")
        st.metric("Odds Justas", f"{odd_away:.2f}")
        st.write("Pontuação Ofensiva", f"{score_away}")
        st.write("Taxa de Vitórias", f"{tx_vitoria_away:.2f}%")
    
    st.markdown("---")
    st.subheader("🔍 Comparador de Valor (Value Bet)")
    st.write("Insira as odds do mercado para comparar com as odds justas calculadas pelo modelo.")

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
        st.caption("A probabilidade final é a média simples das três métricas acima.")

    # --- Painel de Apoio
    st.markdown(f"#### Estatísticas Individuais HT de {home_team} e {away_team}")

    # Chama a função antiga para obter os dados de apoio
    analise_ht_antiga = dt.analisar_gol_ht_home_away(df_home, df_away)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Análise de {home_team} (Casa):**")
        st.info(
            f"Marcou gol no HT em **{analise_ht_antiga['home_marca']:.1f}%** dos seus jogos em casa.")
        st.warning(
            f"Sofreu gol no HT em **{analise_ht_antiga['home_sofre']:.1f}%** dos seus jogos em casa.")

    with col2:
        st.markdown(f"**Análise de {away_team} (Fora):**")
        st.info(
            f"Marcou gol no HT em **{analise_ht_antiga['away_marca']:.1f}%** dos seus jogos fora.")
        st.warning(
            f"Sofreu gol no HT em **{analise_ht_antiga['away_sofre']:.1f}%** dos seus jogos fora.")

    st.markdown("---")
    
    df_home_final = df_home.head(num_jogos_home)
    df_away_final = df_away.head(num_jogos_away)

    df_resultado_mercados = dt.analisar_mercados(df_home_final, df_away_final)

    # Cartões separados
    st.subheader("🎯 Probabilidades por Mercado")
    cols = st.columns(len(df_resultado_mercados))

    for i, col in enumerate(cols):
        mercado = df_resultado_mercados.iloc[i]
        col.metric(
            label=mercado["Mercado"],
            value=f'{mercado["Probabilidade (%)"]}%',
            delta=f'Odd Justa: {mercado["Odd Justa"]}'
        )

    # Gráfico de barras
    st.subheader("📈 Visualização Gráfica")
    chart = alt.Chart(df_resultado_mercados).mark_bar().encode(
        x=alt.X('Mercado', sort=None),
        y='Probabilidade (%)',
        color='Mercado',
        tooltip=['Mercado', 'Probabilidade (%)', 'Odd Justa']
    ).properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)
    st.markdown("---")
    
    st.markdown("### 📊 Estimativa de Escanteios", unsafe_allow_html=True)

    # A chamada da função agora retorna um dicionário diferente
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

    # Transforma a lista de resultados em um DataFrame para fácil visualização
    df_escanteios = pd.DataFrame(
        resultado_escanteios['Probabilidades por Mercado'])

    # Opcional: Exibir como métricas
    cols = st.columns(len(df_escanteios))
    for i, row in df_escanteios.iterrows():
        with cols[i]:
            st.metric(label=row['Mercado'], value=f"{row['Probabilidade (%)']}%", delta=f"Odd Justa: {row['Odd Justa']}")
    st.markdown("---")
    
    # filtro para exibir os últimos jogos (Home)
    st.write(f"### Últimos {num_jogos_selecionado} jogos do {home_team}:")
    st.dataframe(dt.drop_reset_index(df_home))

    # filtro para exibir os últimos jogos (Away)
    st.write(f"### Últimos {num_jogos_selecionado} jogos do {away_team}:")
    st.dataframe(dt.drop_reset_index(df_away))