import pandas as pd
import streamlit as st
import re
from scipy.stats import poisson
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def drop_reset_index(df):
    df = df.dropna()
    df = df.reset_index(drop=True)
    df.index += 1
    return df

# Função para extrair os dados

def extrair_dados(linhas):
    if not linhas:
        return pd.DataFrame()

    jogos = []
    i = 0

    # Define o padrão de data (DD.M ou D.M no início da linha)
    padrao_data_liga = r'^\d{1,2}\.\d{1,2}\s+'

    while i < len(linhas) - 5:
        try:
            # A CONDIÇÃO FOI ALTERADA PARA USAR O PADRÃO DE DATA
            if re.match(padrao_data_liga, linhas[i]):

                # A lógica de extração da liga continua a mesma e funciona perfeitamente
                liga = re.sub(padrao_data_liga, '', linhas[i]).strip()

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
                        "Liga": liga,
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
        except (ValueError, IndexError, TypeError) as e:
            i += 1
    return pd.DataFrame(jogos)

# Adicionado um limite padrão de 41 jogos
def raspar_dados_time(url, limite_jogos=41):
    """
    Função de web scraping que usa Selenium e para de carregar mais jogos
    quando atinge um limite especificado.
    """
    jogos_raspados = []

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    try:
        servico = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=servico, options=chrome_options)
    except Exception as e:
        st.error(f"Erro ao iniciar o WebDriver para o Chrome: {e}")
        return []

    try:
        driver.get(url)
        time.sleep(5)

        # --- Laço para listar os jogos ---
        while True:
            try:
                # Verificando quantos jogos visiveis
                jogos_atuais = driver.find_elements(
                    By.CSS_SELECTOR, "div.match-grid__bottom tbody tr")
                print(f"Jogos carregados até agora: {len(jogos_atuais)}")

                # Verificando se já atingiu o limite
                if len(jogos_atuais) >= limite_jogos:
                    print(
                        f"Limite de {limite_jogos} jogos atingido. A parar de carregar mais.")
                    break

                # Se não atingido o limite, procura e clica no botão
                see_more_button = driver.find_element(
                    By.CLASS_NAME, "link-see-more")
                driver.execute_script("arguments[0].click();", see_more_button)

                print("Clicou em 'see more', a aguardar mais jogos...")
                time.sleep(3)
            except Exception:
                print(
                    "Botão 'see more' não encontrado. Todos os jogos foram carregados.")
                break

        print("Loop de carregamento terminado. A iniciar extração final...")
        html_completo = driver.page_source
        soup = BeautifulSoup(html_completo, 'html.parser')

        match_grid = soup.find('div', class_='match-grid__bottom')
        if match_grid:
            # Seleciona apenas as linhas do corpo da tabela (tbody) para evitar cabeçalhos
            linhas_de_jogo = match_grid.select('tbody tr')

            for linha in linhas_de_jogo[:limite_jogos]:
                try:
                    # Encontra todas as células (td) da linha
                    celulas = linha.find_all('td')

                    # Verifica se a linha tem o número mínimo de células para ser um jogo válido
                    if len(celulas) > 10:
                        data = celulas[0].text.strip()
                        liga_img = celulas[1].find('img')
                        liga = liga_img['alt'] if liga_img else 'N/A'
                        time_casa = celulas[2].text.strip()
                        placar_texto = celulas[3].text.strip()
                        time_fora = celulas[4].text.strip()
                        placar_ht = celulas[5].text.strip()

                        # Adiciona a extração das estatísticas detalhadas
                        chutes = celulas[6].text.strip()
                        chutes_gol = celulas[7].text.strip()
                        ataques = celulas[8].text.strip()
                        escanteios = celulas[9].text.strip()

                        # Extração das odds
                        odd_h = celulas[11].text.strip()
                        odd_d = celulas[12].text.strip()
                        odd_a = celulas[13].text.strip()

                        # Cria um dicionário com os dados extraídos (como texto)
                        jogos_raspados.append({
                            "Liga": liga,
                            "Data": data,
                            "Home": time_casa,
                            "Away": time_fora,
                            "Placar_FT": placar_texto,
                            "Placar_HT": placar_ht,
                            "Chutes": chutes,
                            "Chutes_Gol": chutes_gol,
                            "Ataques": ataques,
                            "Escanteios": escanteios,
                            "Odd_H_str": odd_h,
                            "Odd_D_str": odd_d,
                            "Odd_A_str": odd_a
                        })

                except Exception as e:
                    # Se uma linha específica falhar, ignora e continua
                    continue
        else:
            print("Não foi possível encontrar a grelha de jogos na página.")

    except Exception as e:
        print(f"Ocorreu um erro geral com o Selenium: {e}")
    finally:
        driver.quit()

    return jogos_raspados

def processar_dados_raspados(lista_de_jogos):
    """
    Converte os dados raspados (que são strings) para o formato final do DataFrame,
    pronto para ser usado pelas funções de análise.
    """
    jogos_processados = []
    for jogo in lista_de_jogos:
        try:
            # Separa os placares e estatísticas que estão em formato "X - Y"
            placar_ft = [int(p.strip()) for p in jogo['Placar_FT'].split('-')]
            placar_ht = [int(p.strip()) for p in jogo['Placar_HT'].split('-')]
            chutes = [int(p.strip()) for p in jogo['Chutes'].split('-')]
            chutes_gol = [int(p.strip())
                          for p in jogo['Chutes_Gol'].split('-')]
            ataques = [int(p.strip()) for p in jogo['Ataques'].split('-')]
            escanteios = [int(p.strip())
                          for p in jogo['Escanteios'].split('-')]

            # Converte as odds para float, tratando o caso de não existirem
            odd_h = float(jogo['Odd_H_str']) if jogo['Odd_H_str'].replace(
                '.', '', 1).isdigit() else 0.0
            odd_d = float(jogo['Odd_D_str']) if jogo['Odd_D_str'].replace(
                '.', '', 1).isdigit() else 0.0
            odd_a = float(jogo['Odd_A_str']) if jogo['Odd_A_str'].replace(
                '.', '', 1).isdigit() else 0.0

            jogos_processados.append({
                "Liga": jogo['Liga'],
                "Home": jogo['Home'],
                "Away": jogo['Away'],
                "H_Gols_FT": placar_ft[0],
                "A_Gols_FT": placar_ft[1],
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
                "Odd_H": odd_h,
                "Odd_D": odd_d,
                "Odd_A": odd_a
            })
        except (ValueError, IndexError):
            # Ignora jogos que não tenham todas as estatísticas completas
            continue

    return pd.DataFrame(jogos_processados)

def media_gols_marcados(df, team_name):
    """Calcula a média de gols MARCADOS por um time específico,
    independentemente de ser mandante ou visitante."""
    if df.empty:
        return 0.0

    # Soma os gols marcados em casa (H_Gols_FT) e fora (A_Gols_FT)
    gols_marcados = pd.concat([
        df.loc[df['Home'] == team_name, 'H_Gols_FT'],
        df.loc[df['Away'] == team_name, 'A_Gols_FT']
    ])

    return gols_marcados.mean()


def media_gols_sofridos(df, team_name):
    """Calcula a média de gols SOFRIDOS por um time específico,
    independentemente de ser mandante ou visitante."""
    if df.empty:
        return 0.0

    # Soma os gols sofridos em casa (A_Gols_FT) e fora (H_Gols_FT)
    gols_sofridos = pd.concat([
        df.loc[df['Home'] == team_name, 'A_Gols_FT'],
        df.loc[df['Away'] == team_name, 'H_Gols_FT']
    ])

    return gols_sofridos.mean()

#estimar vencedor da partida


def estimar_vencedor(df_home, df_away, pesos, home_team_name, away_team_name):
    home_jogos = df_home.shape[0]
    away_jogos = df_away.shape[0]

    home_ataques = df_home["H_Ataques"].mean() if home_jogos > 0 else 0
    away_ataques = df_away["A_Ataques"].mean() if away_jogos > 0 else 0

    home_chutes = df_home["H_Chute"].mean() if home_jogos > 0 else 0
    away_chutes = df_away["A_Chute"].mean() if away_jogos > 0 else 0

    home_chutes_gol = df_home["H_Chute_Gol"].mean() if home_jogos > 0 else 0
    away_chutes_gol = df_away["A_Chute_Gol"].mean() if away_jogos > 0 else 0

    media_home_gols_marcados = media_gols_marcados(df_home, home_team_name)
    media_away_gols_marcados = media_gols_marcados(df_away, away_team_name)
    
    home_eficiencia = (home_chutes_gol / home_chutes * 100) if home_chutes > 0 else 0
    away_eficiencia = (away_chutes_gol / away_chutes * 100) if away_chutes > 0 else 0

    # Pesos recebidos por parâmetro
    score_home = (home_ataques * pesos['ataques'] +
                  home_chutes * pesos['chutes'] +
                  home_chutes_gol * pesos['chutes_gol'] +
                  media_home_gols_marcados * pesos['gols'] +
                  home_eficiencia * pesos['eficiencia'])
    
    score_away = (away_ataques * pesos['ataques'] +
                  away_chutes * pesos['chutes'] +
                  away_chutes_gol * pesos['chutes_gol'] +
                  media_away_gols_marcados * pesos['gols'] +
                  away_eficiencia * pesos['eficiencia'])
    
    # Fator casa recebido por parâmetro
    score_home *= pesos['fator_casa']

    empates_home = (df_home["H_Gols_FT"] == df_home["A_Gols_FT"]).sum()
    empates_away = (df_away["H_Gols_FT"] == df_away["A_Gols_FT"]).sum()

    total_jogos = df_home.shape[0] + df_away.shape[0]
    total_empates = empates_home + empates_away

    prob_draw = (total_empates / total_jogos * 100) if total_jogos > 0 else 0

    # Probabilidade de vitória
    restante = 100 - prob_draw
    prob_home = (score_home / (score_home + score_away)) * \
        restante if (score_home + score_away) > 0 else 0
    prob_away = restante - prob_home
   
    total_score = score_home + score_away
    if total_score > 0:
        prob_home = (score_home / total_score) * (100 - prob_draw)
        prob_away = (score_away / total_score) * (100 - prob_draw)
    else:
        prob_home = prob_away = (100 - prob_draw) / 2

    # Odds Justas
    min_prob = 1e-6  # evita divisão por zero ou odds absurdas

    odd_home = 100 / max(prob_home, min_prob)
    odd_away = 100 / max(prob_away, min_prob)
    odd_draw = 100 / max(prob_draw, min_prob)

    if score_home > score_away:
        vencedor = 'home'
    elif score_away > score_home:
        vencedor = 'away'
    else:
        vencedor = 'Empate'

    return vencedor, round(score_home, 2), round(score_away, 2), round(prob_home, 2), round(prob_away, 2), round(prob_draw, 2), round(odd_home, 2), round(odd_away, 2), round(odd_draw, 2)

def contar_frequencia_gols_HT_home(df):
    total_jogos = df.shape[0]
    if total_jogos == 0:
        return 0.0
    jogos_com_gols = df[df["H_Gols_HT"] > 0].shape[0]
    return jogos_com_gols / total_jogos

def contar_frequencia_gols_HT_away(df):
    total_jogos = df.shape[0]
    if total_jogos == 0:
        return 0.0
    jogos_com_gols = df[df["A_Gols_HT"] > 0].shape[0]
    return jogos_com_gols / total_jogos

def analisar_gol_ht_home_away(df_home, df_away):
    # 1. Calcula todas as frequências
    freq_home_marca = contar_frequencia_gols_HT_home(df_home)
    freq_away_sofre = contar_frequencia_gols_HT_away(df_away)
    freq_home_sofre = contar_frequencia_gols_HT_away(df_home)
    freq_away_marca = contar_frequencia_gols_HT_home(df_away)    

    return {
        "home_marca": freq_home_marca * 100,
        "home_sofre": freq_home_sofre * 100,
        "away_marca": freq_away_marca * 100,
        "away_sofre": freq_away_sofre * 100,
    }

def analise_gol_ht(df_home, df_away, suavizar=True):
    """
    Calcula a probabilidade de gol no HT usando o método padronizado 
    (dados combinados + suavização).
    """
    # 1. Unifica os DataFrames, assim como no Painel de Mercados
    df_total = pd.concat([df_home, df_away], ignore_index=True)
    total_jogos = df_total.shape[0]

    # Função de suavização (a mesma do Painel de Mercados)
    def contar_prob(sucessos, total):
        if total == 0:
            return 0.0
        return (sucessos + 1) / (total + 2) if suavizar else sucessos / total

    # 2. Conta os eventos (sucessos) para cada mercado no DataFrame unificado
    over_05ht_sucessos = df_total[(
        df_total['H_Gols_HT'] + df_total['A_Gols_HT']) > 0].shape[0]
    over_15ft_sucessos = df_total[(
        df_total['H_Gols_FT'] + df_total['A_Gols_FT']) > 1].shape[0]
    over_25ft_sucessos = df_total[(
        df_total['H_Gols_FT'] + df_total['A_Gols_FT']) > 2].shape[0]

    # 3. Calcula a probabilidade de cada mercado usando o método de suavização
    prob_05ht = contar_prob(over_05ht_sucessos, total_jogos)
    prob_15ft = contar_prob(over_15ft_sucessos, total_jogos)
    prob_25ft = contar_prob(over_25ft_sucessos, total_jogos)

    # 4. Calcula a média final das probabilidades, como na regra original
    prob_final_estimada = (prob_05ht + prob_15ft + prob_25ft) / 3

    # 5. Define a conclusão e a odd justa
    conclusao = ""
    odd_justa = 0

    if prob_final_estimada >= 0.70:
        conclusao = "✅ Probabilidade Alta de Gol HT"
    elif prob_final_estimada <= 0.60:
        conclusao = "⚠️ Probabilidade Baixa de Gol HT"
    else:
        conclusao = "🔎 Probabilidade Moderada de Gol HT"

    if prob_final_estimada > 0:
        odd_justa = 1 / prob_final_estimada

    # 6. Retorna o dicionário com todos os resultados
    return {
        "conclusao": conclusao,
        "probabilidade": prob_final_estimada * 100,
        "odd_justa": odd_justa,
        "media_05ht": prob_05ht * 100,
        "media_15ft": prob_15ft * 100,
        "media_25ft": prob_25ft * 100,
    }

def analisar_mercados(df_home, df_away, suavizar=True):
    df_total = pd.concat([df_home, df_away], ignore_index=True)
    total_jogos = df_total.shape[0]

    # Funções auxiliares
    def contar_prob(sucessos, total):
        return (sucessos + 1) / (total + 2) if suavizar else sucessos / total if total > 0 else 0.0

    def odd_justa(prob):
        return round(1 / prob, 2) if prob > 0 else 0.0

    # Contagem de eventos
    over_1_5 = df_total[(df_total["H_Gols_FT"] +
                         df_total["A_Gols_FT"]) > 1].shape[0]
    over_2_5 = df_total[(df_total["H_Gols_FT"] +
                         df_total["A_Gols_FT"]) > 2].shape[0]
    btts = df_total[(df_total["H_Gols_FT"] > 0) & (
        df_total["A_Gols_FT"] > 0)].shape[0]

    # Cálculo
    mercados = {
        "Over 1.5": over_1_5,
        "Over 2.5": over_2_5,
        "BTTS": btts
    }

    painel = []
    for nome, sucessos in mercados.items():
        prob = contar_prob(sucessos, total_jogos)
        odd = odd_justa(prob)
        painel.append({
            "Mercado": nome,
            "Jogos com evento": sucessos,
            "Total analisado": total_jogos,
            "Probabilidade (%)": round(prob * 100, 1),
            "Odd Justa": odd
        })

    return drop_reset_index(pd.DataFrame(painel))

# Função para calcular média segura
def safe_mean(df, col):
    return df[col].mean() if col in df.columns else 0.0

# Função para calcular estatísticas dos times
def calc_stats_team(df, team_name):
    """Calcula as estatísticas para um time específico dentro de um DataFrame."""
    # Escanteios feitos pelo time
    esc_feitos = pd.concat([
        df.loc[df['Home'] == team_name, 'H_Escanteios'],
        df.loc[df['Away'] == team_name, 'A_Escanteios']
    ])
    # Escanteios sofridos pelo time
    esc_sofridos = pd.concat([
        df.loc[df['Home'] == team_name, 'A_Escanteios'],
        df.loc[df['Away'] == team_name, 'H_Escanteios']
    ])

    # Finalizações feitas pelo time
    finalizacoes = pd.concat([
        df.loc[df['Home'] == team_name, 'H_Chute'],
        df.loc[df['Away'] == team_name, 'A_Chute']
    ])

    # Ataques feitos pelo time
    ataques = pd.concat([
        df.loc[df['Home'] == team_name, 'H_Ataques'],
        df.loc[df['Away'] == team_name, 'A_Ataques']
    ])

    return {
        'esc_feitos_mean': esc_feitos.mean(),
        'esc_sofridos_mean': esc_sofridos.mean(),
        'esc_feitos_std': esc_feitos.std(),
        'finalizacoes_mean': finalizacoes.mean(),
        'ataques_mean': ataques.mean()
    }

# Função para calcular probabilidade de bater o over usando Poisson
def probabilidade_poisson_over(media_esperada, linha_str):
    try:
        # 1. Separa o tipo (Over/Under) e o número da linha
        parts = linha_str.split()
        # Converte para minúsculas ('over' ou 'under')
        tipo_linha = parts[0].lower()
        linha_num = float(parts[1])   # Ex: 9.5

        # 2. Aplica a fórmula correta para cada cenário
        if tipo_linha == 'over':
            # Probabilidade de ser MAIOR OU IGUAL ao próximo inteiro
            # Ex: Over 9.5 significa P(X >= 10)
            linha_int = int(linha_num) + 1
            prob = 1 - poisson.cdf(linha_int - 1, media_esperada)

        elif tipo_linha == 'under':
            # Probabilidade de ser MENOR OU IGUAL ao inteiro anterior
            # Ex: Under 9.5 significa P(X <= 9)
            linha_int = int(linha_num)
            prob = poisson.cdf(linha_int, media_esperada)

        else:
            return 0.0  # Retorna 0 se a linha não for 'Over' ou 'Under'

        return round(prob, 4)
    except:
        return 0.0

# Função principal
def estimar_linha_escanteios(df_home, df_away, home_team_name, away_team_name):
    stats_home = calc_stats_team(df_home, home_team_name)
    stats_away = calc_stats_team(df_away, away_team_name)

    # 1. Calcula a média de escanteios esperada (lógica mantida)
    esc_home = (stats_home['esc_feitos_mean'] +
                stats_away['esc_sofridos_mean']) / 2
    esc_away = (stats_away['esc_feitos_mean'] +
                stats_home['esc_sofridos_mean']) / 2
    fator_ofensivo = (stats_home['finalizacoes_mean'] + stats_away['finalizacoes_mean'] +
                      stats_home['ataques_mean'] + stats_away['ataques_mean']) / 600
    esc_total_ajustado = (esc_home + esc_away) * (1 + fator_ofensivo)

    # 2. Define uma lista de linhas de mercado padrão para analisar
    linhas_de_mercado = ['Over 8.5', 'Over 9.5', 'Over 10.5', 'Over 11.5',
                         'Under 8.5',  'Under 9.5', 'Under 10.5', 'Under 11.5']

    # 3. Calcula a probabilidade para CADA linha de mercado
    resultados_mercado = []
    for linha in linhas_de_mercado:
        prob = probabilidade_poisson_over(esc_total_ajustado, linha)
        odd_justa = round(1 / prob, 2) if prob > 0 else None
        resultados_mercado.append({
            'Mercado': linha,
            'Probabilidade (%)': round(prob * 100, 2),
            'Odd Justa': odd_justa
        })

    # 4. Retorna um dicionário com a média e a lista de probabilidades
    return {
        'Escanteios Mandante': round(esc_home, 2),
        'Escanteios Visitante': round(esc_away, 2),
        'Escanteios Totais Ajustados': round(esc_total_ajustado, 2),
        'Probabilidades por Mercado': resultados_mercado
    }
