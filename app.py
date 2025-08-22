import streamlit as st
import pandas as pd
import altair as alt
import data as dt
import sidebar as sb
import logging
from datetime import datetime, timedelta, date
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO (UMA SÓ VEZ, NO INÍCIO) ---
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

# Função auxiliar para separar a liga de forma segura
def separar_pais_liga(nome_completo):
    if " - " in nome_completo:
        # Divide e retorna o país e a liga
        partes = nome_completo.split(" - ", 1)
        return pd.Series([partes[0], partes[1]])
    else:
        # Se não encontrar o separador, retorna 'N/A' para o país
        # e mantém o nome original para a liga
        return pd.Series(["N/A", nome_completo])
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

st.sidebar.markdown("### 🔎 Filtros da Análise")
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
    except Exception as e:
        st.warning(f"Erro ao carregar jogos de {data_br}: {e}")

    return df_historicos, df_futuros, data_br, data_iso


# --- Uso no app ---
dia = sb.calendario()  # datetime.date
with st.spinner("⏳ Carregando dados do GitHub..."):
    df_jogos, df_proximos_jogos, dia_br, dia_iso = carregar_dados(dia)

# Guarda no estado
st.session_state.df_jogos = df_jogos
st.session_state.df_proximos_jogos = df_proximos_jogos

# --- Mensagens automáticas ---
hoje_iso = datetime.today().strftime("%Y-%m-%d")
ontem_iso = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

if df_proximos_jogos.empty:
    if dia_iso > hoje_iso:
        st.info(f"Jogos do dia {dia_br} ainda não estão disponíveis, aguarde a atualização. ⏳")
    elif dia_iso < hoje_iso:
        st.info(f"Não existem dados para os jogos de {dia_br}. ℹ️")
    else:
        st.info(f"Nenhum jogo disponível para hoje ({dia_br}).")
else:
    if dia_iso == hoje_iso:
        st.toast(
            f"Jogos de hoje ({dia_br}) carregados com sucesso! ✅", icon="✅")
    else:
        st.success(f"Jogos de {dia_br} carregados com sucesso! ✅")

df_jogos = pd.DataFrame()
df_proximos_jogos = pd.DataFrame()

df_jogos = pd.read_csv(URL_DADOS)

# Guarda o número de linhas antes de qualquer alteração
num_linhas_original = len(df_jogos)
try:
    df_jogos = pd.read_csv(URL_DADOS)

    # Guarda o número de linhas antes de qualquer alteração
    num_linhas_original = len(df_jogos)

    # Converte a coluna 'Data'
    df_jogos['Data'] = pd.to_datetime(
        df_jogos['Data'], format="%d-%m-%Y", errors="coerce"
    )

    # Verifica se alguma data falhou na conversão (tornou-se NaT/null)
    jogos_com_data_invalida = df_jogos['Data'].isnull().sum()

    if jogos_com_data_invalida > 0:
        # Mostra um aviso ao utilizador na interface
        st.warning(
            f"Atenção: {jogos_com_data_invalida} jogo(s) foram ignorados porque a data "
            f"não estava no formato esperado (DD-MM-AAAA)."
        )
        # Remove as linhas com datas inválidas para não afetar as análises
        df_jogos.dropna(subset=['Data'], inplace=True)

    df_jogos['Data'] = df_jogos['Data'].dt.date
    df_jogos = df_jogos.sort_values(
        by="Data", ascending=False
    ).reset_index(drop=True)

    # ✅ Atualiza session_state
    st.session_state.df_jogos = df_jogos

    # Verifica se os dados ainda não foram carregados com sucesso nesta sessão
    if not st.session_state.data_loaded_successfully:
        # Mostra uma notificação temporária
        st.toast(
            f"Base de dados carregada com {len(df_jogos)} jogos!",
            icon="✅"
        )
        # Marca que os dados foram carregados com sucesso.
        st.session_state.data_loaded_successfully = True

except Exception as e:
    st.error(f"Erro ao carregar a base de dados do GitHub: {e}")
    st.stop()

# Exibe os dados apenas se o DataFrame não estiver vazio
df = st.session_state.df_jogos
if not df.empty:
    st.markdown("""
    <style>
    div[role='radiogroup'] > label {
        background-color: #262730;
        color: white;
        margin-top: 5px;
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

df = st.session_state.df_jogos
df_proximos = st.session_state.df_proximos_jogos

if not df.empty and not df_proximos.empty:
    # --- NOVO FLUXO DE FILTROS NA SIDEBAR (BASEADO NOS PRÓXIMOS JOGOS) ---
    
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

    # --- A LÓGICA QUE VOCÊ QUERIA MANTER COMEÇA AQUI ---

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
                            1.0, 1.5, 1.05) 

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
    media_home_gols_marcados = dt.media_gols_marcados(df_home, home_team)
    media_home_gols_sofridos = dt.media_gols_sofridos(df_home, home_team)
    media_away_gols_marcados = dt.media_gols_marcados(df_away, away_team)
    media_away_gols_sofridos = dt.media_gols_sofridos(df_away, away_team)

    # Exibe as médias de gols
    st.markdown("### 📋 Médias de Gols Home e Away", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="background-color:#1f77b4; padding:15px; border-radius:8px; text-align:center; color:white;margin-bottom: 15px;">
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
        df_home, df_away, pesos_modelo, home_team, away_team)

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
    # Exibindo mais dados sobre os times
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
        st.caption("A probabilidade final é a média simples das três métricas acima.")

    # --- Painel de Apoio
    st.markdown(f"#### Estatísticas Individuais HT de {home_team} e {away_team}")

    # Chama a função antiga para obter os dados de apoio
    analise_ht_antiga = dt.analisar_gol_ht_home_away(df_home, df_away)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Análise de {home_team}:**")
        st.info(
            f"Marcou gol no HT em **{analise_ht_antiga['home_marca']:.1f}%** dos seus jogos.")
        st.warning(
            f"Sofreu gol no HT em **{analise_ht_antiga['home_sofre']:.1f}%** dos seus jogos.")

    with col2:
        st.markdown(f"**Análise de {away_team}:**")
        st.info(
            f"Marcou gol no HT em **{analise_ht_antiga['away_marca']:.1f}%** dos seus jogos.")
        st.warning(
            f"Sofreu gol no HT em **{analise_ht_antiga['away_sofre']:.1f}%** dos seus jogos.")

    st.markdown("---")
    
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

    # Gráfico de barras
    st.subheader("📈 Visualização Gráfica")
    chart = alt.Chart(df_resultado_mercados).mark_bar().encode(
        x=alt.X('Mercado', sort=None),
        y='Probabilidade (%)',
        color='Mercado',
        tooltip=['Mercado', 'Probabilidade (%)', 'Odd Justa']
    )
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

    # Transforma a lista de resultados em um DataFrame
    df_escanteios = pd.DataFrame(resultado_escanteios['Probabilidades por Mercado'])

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
            st.metric(label=row['Mercado'], value=f"{row['Probabilidade (%)']}%", delta=f"Odd Justa: {row['Odd Justa']}")
        
        # Se chegamos na última coluna da linha atual (e não é o último item), cria uma nova linha de colunas
        if col_index == num_colunas - 1 and i < len(df_escanteios) - 1:
            cols = st.columns(num_colunas)
    st.markdown("---")

    def auto_height(df, base=35, header=40, max_height=500):
        # Calcula altura automática da tabela
        return min(len(df) * base + header, max_height)

    # remove colunas indesejadas
    cols_to_show = [c for c in df_home.columns if c not in ["Pais", "resultado"]]

    # filtro para exibir os últimos jogos (Home)
    st.markdown(
        f"### 🏠 Últimos {len(df_home)} jogos do **{home_team}**")
    st.dataframe(df_home[cols_to_show].reset_index(drop=True),
                 use_container_width=True,
                 height=auto_height(df_home),
                 hide_index=True)

    # filtro para exibir os últimos jogos (Away)
    st.markdown(
        f"### ✈️ Últimos {len(df_away)} jogos do **{away_team}**")
    st.dataframe(df_away[cols_to_show].reset_index(drop=True),
                 use_container_width=True,
                 height=auto_height(df_away),
                 hide_index=True)

    # --- Botão para salvar análise atual ---
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

    df_escanteios = pd.DataFrame(resultado_escanteios['Probabilidades por Mercado'])
    linha_mais_provavel = df_escanteios.loc[df_escanteios['Probabilidade (%)'].idxmax()]
    linha_escanteio_str = f"{linha_mais_provavel['Mercado']} ({linha_mais_provavel['Probabilidade (%)']:.1f}%)"

    # 2. Monta dicionário da análise
    current_analysis = {
        #"País": selected_country,
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
