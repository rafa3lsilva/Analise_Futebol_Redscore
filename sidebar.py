import streamlit as st
import pandas as pd

# Função para a barra lateral
def sidebar():
    st.sidebar.header("📊 Análise de Jogos de Futebol")
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
    st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Exibe o confronto atual
def confronto_atual(home_team, away_team):
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
st.sidebar.markdown("<br>", unsafe_allow_html=True)
