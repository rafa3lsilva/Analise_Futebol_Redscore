import streamlit as st
import datetime

# Função para a barra lateral
def sidebar():
    st.sidebar.markdown(
        "<h3 style='text-align: center;'>⚽ Análise Futebol RedScore</h3>", unsafe_allow_html=True)
    # Tutorial
    tutorial_url = "https://www.notion.so/Tutorial-Redscore-2504bab1283b80f1af08fca804deb248"

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

def calendario():    
    # 1. Obtém a data e hora universal (UTC) de forma "consciente" do fuso horário
    utc_now = datetime.datetime.now(datetime.timezone.utc)

    # 2. Define o fuso horário desejado (ex: UTC-3 para o Brasil)
    brasil_tz = datetime.timezone(datetime.timedelta(hours=-3))

    # 3. Converte a hora UTC para o fuso horário do Brasil
    brasil_time = utc_now.astimezone(brasil_tz)

    # 4. Define a data de "hoje" com base nesse ajuste
    hoje_ajustado = brasil_time.date()

    # 5. Usa a data ajustada como valor padrão para o calendário
    dia = st.sidebar.date_input(
        "Selecione a data:", value=hoje_ajustado, key='date_input')

    st.markdown("""<style>
        div[data-testid="stDateInput"] > div:first-child {
        width: 50px;
    }
</style>""", unsafe_allow_html=True)

    return dia
