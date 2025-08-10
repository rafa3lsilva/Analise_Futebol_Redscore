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