# TELA 1 - como estava o dashboard do flooding
import json
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Simulação de Cheia - Porto Alegre", layout="wide")

def formatar_numero(n):
    # i feel so bonita
    texto = f"{n:,}"
    return texto.replace(",", ".")

def pegar_valores(dados_bairro, nivel):
    # retorna [pessoas afetadas, predios afetados] de um bairro para o nivel escolhido
    pessoas = 0 
    predios = 0
    posicao = 0
    for chave, valor in dados_bairro["affected_population"].items():
        nivel_da_chave = float(chave.replace("m", "").replace("_", "."))  # "4_3m" -> 4.3
        if nivel_da_chave<=nivel:
            pessoas = valor
            predios = dados_bairro["affected_buildings"][posicao]
        posicao = posicao+1
    return pessoas, predios #ver depois

# ler arquivo
arquivo = open("dados/dados_limpos.json", encoding="utf-8")
dados = json.load(arquivo)
arquivo.close()

# titulo e slider
st.title("Simulação de Cheia - Porto Alegre")
col_nivel, col_mapa, col_info = st.columns([1,4,3])

with col_nivel:
    nivel = st.slider("Nível da água (m)", 3.0, 10.0, 5.0, 0.1)
    nivel = round(nivel, 1)

# montar tabela com uma linha por bairro
linhas = []
for nome_bairro in dados:
    bairro = dados[nome_bairro]
    pessoas, predios = pegar_valores(bairro, nivel)

    pct_moradores = 0
    if bairro["population"]>0:
        pct_moradores = pessoas/bairro["population"]
    pct_predios = 0
    if bairro["total_buildings"]>0:
        pct_predios = predios/bairro["total_buildings"]

    linhas.append({
        "bairro": nome_bairro,
        "populacao": bairro["population"],
        "pessoas": pessoas,
        "predios": predios,
        "pct_moradores": pct_moradores,
        "pct_predios": pct_predios})

tabela = pd.DataFrame(linhas)

total_pessoas = int(tabela["pessoas"].sum())
total_predios = int(tabela["predios"].sum())
total_populacao = int(tabela["populacao"].sum())

# coluna do meio
with col_mapa:
    c1, c2, c3 = st.columns(3)
    c1.metric("Pessoas afetadas", formatar_numero(total_pessoas))
    c2.metric("Prédios afetados", formatar_numero(total_predios))
    c3.metric("Bairros atingidos", len(tabela[tabela["predios"] > 0]))
    st.info("OPCIONAL: Aonde o mapa ficaria, mas não conseguimos implementar")
    st.caption("AVISO: Os seguintes números são estimativas de uma simulação, não previsões nem contagens oficiais!")

# % da população total
    pct_total = 0
    if total_populacao > 0:
        pct_total = total_pessoas / total_populacao
    st.markdown(f"### {pct_total:.0%} da população total de Porto Alegre afetada")

    # curva: população afetada na cidade inteira para cada nível de 3,0 a 10,0
    niveis_curva = []
    pessoas_curva = []
    for i in range(71):
        n = round(3.0 + i * 0.1, 1)
        soma = 0
        for nome_bairro in dados:
            pessoas_b, predios_b = pegar_valores(dados[nome_bairro], n)
            soma = soma + pessoas_b
        niveis_curva.append(n)
        pessoas_curva.append(soma)
    curva = pd.DataFrame({"nivel": niveis_curva, "pessoas": pessoas_curva})

    grafico_curva = px.line(curva, x="nivel", y="pessoas",
                            title="População afetada por nível do Guaíba",
                            labels={"nivel": "Nível do Guaíba (m)", "pessoas": "População afetada (estimada)"})
    grafico_curva.add_vline(x=5.35, line_dash="dash", annotation_text="Recorde de maio/2024: 5,35 m")
    grafico_curva.add_scatter(x=[nivel], y=[total_pessoas], mode="markers",
                              marker=dict(size=10), showlegend=False)  # ponto do nível escolhido
    grafico_curva.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(grafico_curva, use_container_width=True)

    # barras: % de prédios afetados em cada bairro atingido
    st.subheader("% de prédios afetados por bairro")
    quantos_barras = st.selectbox("Mostrar os bairros com maior %", [10, 20, 30, 50])

    por_pct = tabela[tabela["predios"] > 0].sort_values("pct_predios", ascending=False)
    por_pct = por_pct.head(quantos_barras).copy()
    por_pct["pct_100"] = por_pct["pct_predios"] * 100

    if len(por_pct) == 0:
        st.caption("Nenhum bairro atingido neste nível.")
    else:
        barras = px.bar(por_pct, x="pct_100", y="bairro", orientation="h",
                        color_discrete_sequence=["#4192b0"],
                        labels={"pct_100": "% de prédios afetados", "bairro": ""})
        barras.update_yaxes(autorange="reversed")  # maior % no topo
        barras.update_xaxes(range=[0, 100])
        barras.update_layout(height=60 + 24 * len(por_pct), margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(barras, use_container_width=True)

# coluna da direita
with col_info:
    t1, t2 = st.columns([2, 1])
    t1.subheader("Bairros afetados")
    ordem = t2.selectbox("Ordenar por", ["Pop. afetada", "Prédios afetados", "% dos moradores"])

    # apenas bairros com algum predio afetado
    afetados = tabela[tabela["predios"] > 0]

    if ordem == "Pop. afetada":
        afetados = afetados.sort_values("pessoas", ascending=False)
    elif ordem == "Prédios afetados":
        afetados = afetados.sort_values("predios", ascending=False)
    else:
        afetados = afetados.sort_values("pct_moradores", ascending=False)

    # mostra os 5 primeiros
    quantos = min(5, len(afetados))
    for i in range(quantos):
        b = afetados.iloc[i]
        st.markdown(f"- **{b['bairro']}**")
        st.markdown(f"    - {b['pct_predios']:.0%} dos prédios afetados")
        st.markdown(f"    - {b['pct_moradores']:.0%} dos moradores afetados")
    if len(afetados)>5:
        st.markdown("...")
