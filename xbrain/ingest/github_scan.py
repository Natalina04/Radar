"""Radar tecnológico: busca no GitHub por repositórios com stack/abordagem
parecida com os meus projetos atuais, filtra por licença permissiva e
registra os achados como "candidatos a incorporação" na tabela sinais.

Isto NUNCA baixa ou copia código — só a metadata do repositório (nome,
descrição, licença, stars, linguagem, tópicos) para eu revisar depois.

Rode com:  python -m ingest.github_scan
"""

import requests

from config import GITHUB_TOKEN, HTTP_TIMEOUT_SECONDS, HTTP_USER_AGENT
from storage.db import init_db, insert_signal

# ---------------------------------------------------------------------------
# PARÂMETROS
# ---------------------------------------------------------------------------

# Meus projetos/ideias atuais — usados para montar as buscas no GitHub.
# Edite esta lista conforme seus projetos reais (stack, domínio, problema).
MEUS_PROJETOS = [
    {
        "nome": "Projeção de IPCA (SARIMA/ETS)",
        "linguagem": "python",
        "topicos": ["time-series-forecasting", "sarima"],
        "problema": "projeção de séries temporais macroeconômicas",
    },
    {
        "nome": "Radar de economia/crédito (este projeto)",
        "linguagem": "python",
        "topicos": ["economic-indicators", "financial-data"],
        "problema": "ingestão e organização de indicadores econômicos",
    },
]

# Licenças permissivas aceitas (SPDX id, minúsculo). Qualquer outra licença
# (ou ausência de licença) é registrada com aviso em vez de descartada.
LICENCAS_PERMISSIVAS = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause"}

QTD_RESULTADOS_POR_BUSCA = 5

BASE_URL = "https://api.github.com/search/repositories"
# ---------------------------------------------------------------------------


def montar_headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": HTTP_USER_AGENT,
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def buscar_repositorios(linguagem, topico, qtd=QTD_RESULTADOS_POR_BUSCA):
    query = f"topic:{topico} language:{linguagem}"
    resposta = requests.get(
        BASE_URL,
        params={"q": query, "sort": "stars", "order": "desc", "per_page": qtd},
        headers=montar_headers(),
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    resposta.raise_for_status()
    return resposta.json().get("items", [])


def classificar_licenca(repo):
    licenca = repo.get("license") or {}
    spdx_id = (licenca.get("spdx_id") or "").lower()
    if spdx_id in LICENCAS_PERMISSIVAS:
        return spdx_id, False  # (licenca, restritiva?)
    if not spdx_id or spdx_id == "noassertion":
        return "sem licença declarada", True
    return spdx_id, True


def ingerir_candidatos():
    init_db()
    total_novos = 0

    for projeto in MEUS_PROJETOS:
        for topico in projeto["topicos"]:
            try:
                repos = buscar_repositorios(projeto["linguagem"], topico)
            except requests.RequestException as erro:
                print(f"[github_scan] falha na busca ({projeto['linguagem']}/{topico}): {erro}")
                continue

            for repo in repos:
                licenca, restritiva = classificar_licenca(repo)
                aviso = " [ATENÇÃO: licença restritiva/ausente]" if restritiva else ""
                resumo = (
                    f"Candidato para \"{projeto['nome']}\": {repo['full_name']} "
                    f"({repo['stargazers_count']}★) — {repo.get('description') or 'sem descrição'}"
                    f"{aviso}"
                )
                por_que_importa = (
                    f"Encontrado buscando topic:{topico} language:{projeto['linguagem']} "
                    f"por semelhança com o problema \"{projeto['problema']}\". "
                    "Ainda não desmontado — próximo passo é ler README/arquitetura antes de propor incorporação."
                )
                inserido = insert_signal(
                    fonte=f"GitHub - {repo['full_name']}",
                    modulo="remanufatura_digital",
                    tipo="tecnologia",
                    resumo=resumo,
                    por_que_importa=por_que_importa,
                    evidencias=repo["html_url"],
                    licenca=licenca,
                    tags=f"github,{projeto['linguagem']},{topico}",
                )
                if inserido:
                    total_novos += 1
                    print(f"[github_scan] novo: {resumo}")

    print(f"[github_scan] concluído — {total_novos} candidato(s) novo(s) inserido(s).")


if __name__ == "__main__":
    ingerir_candidatos()
