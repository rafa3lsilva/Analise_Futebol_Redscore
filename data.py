import pandas as pd
import re

# Função para extrair os dados
def extrair_dados(linhas):
    if not linhas:
        return pd.DataFrame()  # Retorna DataFrame vazio se linhas for None ou lista vazia

    jogos = []
    i = 0

    while i < len(linhas) - 5:
        try:
            if "League" in linhas[i] or "Championship" in linhas[i] or "Serie" in linhas[i]:
                liga = linhas[i]
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
        except:
            i += 1

    return pd.DataFrame(jogos)

def home(home_team):
    return home_team

def away(away_team):
    return away_team

#funções para calcular as médias de gols
def media_home_gols_feitos(df_home):
    media_gols_feitos = df_home["H_Gols_FT"].mean() if not df_home.empty else 0
    return media_gols_feitos

def media_home_gols_sofridos(df_home):
    media_gols_sofridos = df_home["A_Gols_FT"].mean() if not df_home.empty else 0
    return media_gols_sofridos

def media_away_gols_feitos(df_away):
    media_gols_feitos = df_away["A_Gols_FT"].mean() if not df_away.empty else 0
    return media_gols_feitos

def media_away_gols_sofridos(df_away):
    media_gols_sofridos = df_away["H_Gols_FT"].mean() if not df_away.empty else 0
    return media_gols_sofridos

#estimar vencedor da partida
def estimar_vencedor(df_home, df_away):
    home_jogos = df_home.shape[0]
    away_jogos = df_away.shape[0]

    home_ataques = df_home["H_Ataques"].mean() if home_jogos > 0 else 0
    away_ataques = df_away["A_Ataques"].mean() if away_jogos > 0 else 0

    home_chutes = df_home["H_Chute"].mean() if home_jogos > 0 else 0
    away_chutes = df_away["A_Chute"].mean() if away_jogos > 0 else 0

    home_chutes_gol = df_home["H_Chute_Gol"].mean() if home_jogos > 0 else 0
    away_chutes_gol = df_away["A_Chute_Gol"].mean() if away_jogos > 0 else 0

    media_home_gols = media_home_gols_feitos(df_home)
    media_away_gols = media_away_gols_feitos(df_away)

    home_eficiencia = (home_chutes_gol / home_chutes * 100) if home_chutes > 0 else 0
    away_eficiencia = (away_chutes_gol / away_chutes * 100) if away_chutes > 0 else 0

    score_home = (home_ataques * 0.2 + home_chutes * 0.3 + home_chutes_gol * 0.5 + media_home_gols * 1.5 + home_eficiencia * 2)
    score_away = (away_ataques * 0.2 + away_chutes * 0.3 + away_chutes_gol * 0.5 + media_away_gols * 1.5 + away_eficiencia * 2)
    score_home += 1

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