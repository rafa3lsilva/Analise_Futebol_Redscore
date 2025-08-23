import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

def mostrar_status_carregamento(df_proximos: pd.DataFrame, dia_br: str, dia_iso: str):
    """Mostra mensagens automáticas de acordo com a data escolhida e disponibilidade dos jogos."""
    hoje_iso = datetime.today().strftime("%Y-%m-%d")
    ontem_iso = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    if df_proximos.empty:
        if dia_iso > hoje_iso:
            st.info(f"Jogos do dia {dia_br} ainda não estão disponíveis. ⏳")
        elif dia_iso < hoje_iso:
            st.info(f"Não existem dados para os jogos de {dia_br}. ℹ️")
        else:
            st.info(f"Nenhum jogo disponível para hoje ({dia_br}).")
    else:
        if dia_iso == hoje_iso:
            if "msg_carregada" not in st.session_state or st.session_state.msg_carregada != dia_iso:
                st.toast(
                    f"Jogos de hoje ({dia_br}) carregados com sucesso! ✅", icon="✅")
                st.session_state.msg_carregada = dia_iso
        else:
            st.toast(f"Jogos de {dia_br} carregados com sucesso! ✅")

def titulo_principal():
    st.markdown(
        """
    <h1 style='display: flex; align-items: center; justify-content: center; text-align: center;'>
        📊 Análise de Jogos de Futebol
    </h1>
    """,
        unsafe_allow_html=True
    )
    # Descrição da aplicação
    st.markdown("""
    <div  style="text-align: center; font-size: 16px;">
        <p style='text-align: center;'>Esta é uma aplicação para análise de jogos de futebol usando dados do site Redscore.</p>
        <p style='text-align: center;'>Você pode fazer upload de arquivos .txt com os dados dos jogos e obter análises detalhadas.</p>
        <p style='text-align: center;'>Para mais informações, consulte o tutorial na barra lateral.</p>
    </div>
    """, unsafe_allow_html=True)


def configurar_estilo_intervalo_jogos():
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

def mostrar_cards_media_gols(
    home_team: str,
    away_team: str,
    media_home_gols_marcados: float,
    media_home_gols_sofridos: float,
    media_away_gols_marcados: float,
    media_away_gols_sofridos: float
):
    """Mostra os cards estilizados com médias de gols."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style="background-color:#1f77b4; padding:15px; border-radius:8px; 
                    text-align:center; color:white; margin-bottom:15px;">
            <h3>🏠 {home_team}</h3>
            <p style="font-size:18px;">⚽ Média de Gols Marcados: 
                <strong>{media_home_gols_marcados:.2f}</strong></p>
            <p style="font-size:18px;">🛡️ Média de Gols Sofridos: 
                <strong>{media_home_gols_sofridos:.2f}</strong></p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background-color:#d62728; padding:15px; border-radius:8px; 
                    text-align:center; color:white; margin-bottom:15px;">
            <h3>✈️ {away_team}</h3>
            <p style="font-size:18px;">⚽ Média de Gols Marcados: 
                <strong>{media_away_gols_marcados:.2f}</strong></p>
            <p style="font-size:18px;">🛡️ Média de Gols Sofridos: 
                <strong>{media_away_gols_sofridos:.2f}</strong></p>
        </div>
        """, unsafe_allow_html=True)

def grafico_mercados(df: pd.DataFrame, titulo: str = "Probabilidades por Mercado"):
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Mercado', sort=None),
        y=alt.Y('Probabilidade (%)', title='Probabilidade (%)'),
        color='Mercado',
        tooltip=['Mercado', 'Probabilidade (%)', 'Odd Justa']
    )
    st.altair_chart(chart, use_container_width=True)

def mostrar_tabela_jogos(df: pd.DataFrame, team: str, tipo: str):
    """Mostra a tabela de últimos jogos de um time (Home/Away)."""
    def auto_height(df, base=35, header=40, max_height=500):
        return min(len(df) * base + header, max_height)

    cols_to_show = [c for c in df.columns if c not in ["Pais", "resultado"]]

    st.markdown(f"### {tipo} Últimos {len(df)} jogos do **{team}**")
    st.dataframe(
        df[cols_to_show].reset_index(drop=True),
        use_container_width=True,
        height=auto_height(df),
        hide_index=True
    )
