# TELA 2 - novos dados
import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Enchente RS 2024", layout="wide")

def formatar_milhoes(valor):
    # i feel so bonita 2
    milhoes = valor/1000000
    texto = f"{milhoes:.1f}".replace(".",",")
    return "R$ " + texto+ " mi"

def coluna_ebap(dia, colunas):
    partes = dia.split("/")
    dia_numero = partes[0]
    mes_numero = partes[1]
    desejada = "Situ_2024_" + mes_numero + "_" + dia_numero

    escolhida = None
    for coluna in colunas:  # colunas ja em ordem de data
        if coluna<=desejada:
            escolhida = coluna
    return escolhida

# ler arquivos
# ABRIGOS
abrigos = gpd.read_file("../dados/abrigos_unificado.gpkg")
abrigos["lat"] = abrigos.geometry.y
abrigos["lon"] = abrigos.geometry.x
abrigos = pd.DataFrame(abrigos.drop(columns="geometry"))

# a coluna data eh so um texto. criamos uma data de verdade para ordenar depois
abrigos["data_ordem"] = pd.to_datetime(abrigos["data"]+"/2024", format="%d/%m/%Y", errors="coerce")
abrigos = abrigos.dropna(subset=["data_ordem"])

# EBAPs
ebaps = gpd.read_file("../dados/rmpa_crise_sb_ebaps_limpo.gpkg")
ebaps["lat"] = ebaps.geometry.y
ebaps["lon"] = ebaps.geometry.x
ebaps = pd.DataFrame(ebaps.drop(columns="geometry"))

colunas_situ = []
for nome_coluna in ebaps.columns:
    if nome_coluna.startswith("Situ_"):
        colunas_situ.append(nome_coluna)
colunas_situ.sort()

cores_situacao = {"Operante": "green", "Inoperante": "red", "APURAR": "orange"}

# PATRIMONIO CULTURAL
patrimonio = gpd.read_file("../dados/rs_crise_patrimonio_cultural_limpo.gpkg")
patrimonio["lat"] = patrimonio.geometry.y
patrimonio["lon"] = patrimonio.geometry.x
patrimonio = pd.DataFrame(patrimonio.drop(columns="geometry"))

cores_esfera = {"Municipal": "purple", "Estadual": "magenta", "Federal": "brown"}

# registros do atlas
atlas = pd.read_csv("../dados/ad_menor_null.csv", encoding="utf-8-sig")
atlas["Data_Evento"] = pd.to_datetime(atlas["Data_Evento"], format="%m/%d/%Y", errors="coerce")

colunas_numericas = ["DH_MORTOS", "DH_FERIDOS", "DH_DESAPARECIDOS", "DH_total_danos_humanos_diretos", "DM_total_danos_materiais", "PE_PLePR"]
for coluna in colunas_numericas:
    atlas[coluna]=pd.to_numeric(atlas[coluna], errors="coerce")
    atlas[coluna]=atlas[coluna].fillna(0)

# layout
st.title("Enchente no Rio Grande do Sul - 2024")
col_mapa, col_dir = st.columns([4, 4])

with col_mapa:
    area_mapa = st.container()
    area_slider = st.container()

with area_slider:
    st.markdown("**2024**")
    datas_ordenadas = abrigos.sort_values("data_ordem")
    lista_de_dias = list(datas_ordenadas["data"].unique())
    dia = st.select_slider("Dia", options=lista_de_dias)

# mapa
with area_mapa:
    st.subheader("Abrigos e fontes públicas")
    todos_os_tipos = list(abrigos["tipo"].dropna().unique())
    tipos = st.multiselect("Filtrar por tipo de abrigo", todos_os_tipos, default=todos_os_tipos)
    mostrar_ebaps = st.checkbox("Mostrar EBAP", value=True)
    mostrar_patrimonio = st.checkbox("Mostrar patrimônio cultural", value=True)

    filtrado = abrigos[abrigos["data"] == dia]
    filtrado = filtrado[filtrado["tipo"].isin(tipos)]

    mapa = px.scatter_map(filtrado, lat="lat", lon="lon", color="tipo", hover_name="nome", zoom=9, height=520, map_style="open-street-map")
    # agrupa as legendas dos abrigos
    mapa.update_traces(legendgroup="abrigos", legendgrouptitle_text="Abrigos")
    mapa.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        legend_title_text="",
        legend_groupclick="toggleitem",
        map=dict(center=dict(lat=-30.05, lon=-51.2), zoom=10), # n quero mais aparecer no oceano obrigado
        uirevision="fixo" # mantem a posicao ao mudar o dia
    )

    coluna = coluna_ebap(dia, colunas_situ)
    if mostrar_ebaps and coluna is not None:
        ebaps_dia = ebaps.copy()
        ebaps_dia["situacao"]= ebaps_dia[coluna]
        camada_ebap = px.scatter_map(ebaps_dia, lat="lat", lon="lon", color="situacao", hover_name="Nome Completo", color_discrete_map=cores_situacao)
        camada_ebap.update_traces(marker=dict(size=14))
        camada_ebap.update_traces(legendgroup="ebaps", legendgrouptitle_text="Estações de Bombeamento (EBAP)")
        for traco in camada_ebap.data:
            mapa.add_trace(traco)
    if mostrar_patrimonio:
        camada_patrimonio = px.scatter_map(patrimonio, lat="lat", lon="lon", color="Esfera",
                                           hover_name="NomeInstituicao",
                                           color_discrete_map=cores_esfera)
        camada_patrimonio.update_traces(marker=dict(size=12))
        camada_patrimonio.update_traces(legendgroup="patrimonio",
                                        legendgrouptitle_text="Patrimônios culturais afetados")
        for traco in camada_patrimonio.data:
            mapa.add_trace(traco)

    st.plotly_chart(mapa, use_container_width=True)
    st.caption(f"{len(filtrado)} pontos em {dia}/2024")
    if mostrar_ebaps:
        if coluna is None:
            st.caption("Sem dados de EBAP para este dia!")
        else:
            partes = coluna.split("_")
            data_ebap = partes[3] + "/" + partes[2] #formatacao
            st.caption("EBAPs: situação em "+data_ebap)

# painel da direita
with col_dir:
    opcoes = ["Todo o RS"] + sorted(atlas["Nome_Municipio"].dropna().unique())
    municipio = st.selectbox("Município selecionado", opcoes)

    if municipio=="Todo o RS": 
        dados = atlas
    else: 
        dados = atlas[atlas["Nome_Municipio"]==municipio]

    coluna_a, coluna_b = st.columns(2)

    with coluna_a:
        texto = "- **Danos materiais:** " + formatar_milhoes(dados["DM_total_danos_materiais"].sum()) + "\n"
        texto = texto + "- **Prejuízo total:** " + formatar_milhoes(dados["PE_PLePR"].sum()) + "\n"
        texto = texto + "- **Danos humanos:** " + str(int(dados["DH_total_danos_humanos_diretos"].sum())) + "\n"
        texto = texto + "- **Número de alertas:** " + str(len(dados))
        st.markdown(texto)

    with coluna_b:
        texto = "- **Mortes:** " + str(int(dados["DH_MORTOS"].sum())) + "\n"
        texto = texto + "- **Feridos:** " + str(int(dados["DH_FERIDOS"].sum())) + "\n"
        texto = texto + "- **Desaparecidos:** " + str(int(dados["DH_DESAPARECIDOS"].sum()))
        st.markdown(texto)

    # grafico de quantos registros por dia blehh blehhh blehhhh blehhh blhheeee bleheheheh blheeee
    por_dia = dados.groupby("Data_Evento").size().reset_index(name="alertas")
    grafico = px.line(por_dia, x="Data_Evento", y="alertas", markers=True, title="Número de registros por dia (Data_Evento)", labels={"Data_Evento": "Data", "alertas": "Número de registros"})
    st.plotly_chart(grafico, use_container_width=True)

# fontes
st.divider()
st.subheader("Fontes dos dados")
st.markdown("- **[Registros de danos e alertas por município](https://atlasdigital.mdr.gov.br/arquivos/2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv)** (`ad_menor_null.csv`): Data de coleta: 28/10")
st.markdown("- **[Abrigos e fontes públicas](https://zenodo.org/records/14617475)** (`abrigos_unificado.gpkg`): Data de coleta: 27/10")
st.markdown("- **[Estações de bombeamento, EBAP](https://zenodo.org/records/14617475)** (`rmpa_crise_sb_ebaps_limpo.gpkg`): Data de coleta: 27/10")
st.markdown("- **[Patrimônio cultural](https://zenodo.org/records/14617475)** (`rs_crise_patrimonio_cultural_limpo.gpkg`): Data de coleta: 27/10")