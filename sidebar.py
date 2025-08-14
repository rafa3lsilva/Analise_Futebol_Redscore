import streamlit as st

# Função para a barra lateral
def sidebar():
    st.sidebar.header("📊 Análise de Jogos de Futebol")
    # Tutorial
    tutorial_url = "https://redscores.com/pt-br/"

    st.sidebar.markdown(f"""
        <div style="text-align: center; font-size: 16px;">
            <a href="{tutorial_url}" target="_blank" style="text-decoration: none;">
                <div style="margin-bottom: 10px; background-color:#1f77b4; padding:8px; border-radius:6px; color:white;">
                    📚 Tutorial
                </div>
            </a>
        </div>
        <br>
    """, unsafe_allow_html=True)