
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import requests

st.set_page_config(layout="wide")
st.title("📊 Dashboard Interativo de Financiamentos")

@st.cache_data
def load_data():
    return pd.read_csv("dataset_financiamentos_filtrado.csv")

df = load_data()

# Sidebar
st.sidebar.header("🔎 Filtros")

bancos = df["BANCO_VENCEDOR"].dropna().unique().tolist()
selected_bancos = st.sidebar.multiselect("Banco vencedor", bancos, default=bancos)

valor_range = st.sidebar.slider("Valor final do financiamento", 0, 70000, (0, 70000), step=1000)

st.sidebar.markdown("### 📝 Tipo de Proposta")
escolhido_opcao = st.sidebar.radio("Proposta escolhida?", ["Todos", "Sim", "Não"], index=0)

# -------------------------------
# Seção: Mapa Interativo por Estado (Brasil) com filtro e mapa completo
# -------------------------------

# Lista completa de UFs e nomes
uf_para_nome_estado = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará",
    "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
    "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
}

# Adicionar filtro de estado na barra lateral
lista_ufs = sorted(uf_para_nome_estado.keys())
todos_estados_opcao = ["Selecionar todos"] + lista_ufs
selected_ufs_opcao = st.sidebar.multiselect("Estado (UF)", todos_estados_opcao, default=todos_estados_opcao)

if "Selecionar todos" in selected_ufs_opcao:
    selected_ufs = lista_ufs
else:
    selected_ufs = selected_ufs_opcao

if escolhido_opcao != "Todos":
    df_filtered = df[df["ESCOLHIDO"] == escolhido_opcao].copy()
else:
    df_filtered = df.copy()

df_filtered = df[
    (df["BANCO_VENCEDOR"].isin(selected_bancos)) &
    (df["VALOR_FINAL"] >= valor_range[0]) &
    (df["VALOR_FINAL"] <= valor_range[1]) &
    (df["ESTADO"].isin(selected_ufs))
].copy()

# Discretização ordenada
for var in ["CARENCIA", "QTD_PARCELA"]:
    ordenado = sorted(df_filtered[var].dropna().unique().astype(int))
    df_filtered[f"{var}_LABEL"] = pd.Categorical(
        df_filtered[var].astype(int).astype(str),
        categories=[str(x) for x in ordenado],
        ordered=True
    )

# Métricas agregadas por banco
st.subheader("📌 Resumo por Banco Vencedor")
variaveis = ["VALOR_FINAL", "VALOR_PARCELA", "QTD_PARCELA", "CARENCIA", "TAXA_CLIENTE", "VALOR_TOTAL_PAGAR", "SPREAD_EFETIVO"]
resumo = df_filtered.groupby("BANCO_VENCEDOR")[variaveis].agg(["count", "mean", "median", "std", "min", "max"]).round(2)
st.dataframe(resumo)

# Pairplot interativo
st.subheader("📉 Análise Bivariada (Dispersão)")
x_var = st.selectbox("Variável X", variaveis, index=0)
y_var = st.selectbox("Variável Y", variaveis, index=4)

fig1, ax1 = plt.subplots(figsize=(5, 3))
sns.scatterplot(data=df_filtered, x=x_var, y=y_var, hue="BANCO_VENCEDOR", alpha=0.6, ax=ax1)
st.pyplot(fig1)

# Histograma com controles
st.subheader("📈 Histograma por Banco")
var_hist = st.selectbox("Variável para o histograma", variaveis, index=4)
stat = st.radio("Eixo Y", ["density", "count"], index=0)
common_norm = st.checkbox("Normalização comum entre bancos", value=True)
multiple_option = st.selectbox("Modo de sobreposição", ["layer", "stack", "dodge", "fill"], index=0)

if var_hist in ["CARENCIA", "QTD_PARCELA"]:
    var_hist_plot = f"{var_hist}_LABEL"
    use_discrete = True
    kde = False
    bw = None
else:
    var_hist_plot = var_hist
    use_discrete = False
    kde = True

fig2, ax2 = plt.subplots(figsize=(5, 3))
sns.histplot(
    data=df_filtered,
    x=var_hist_plot,
    hue="BANCO_VENCEDOR",
    kde=kde,
    stat=stat,
    multiple=multiple_option,
    common_norm=common_norm,
    discrete=use_discrete,
    alpha=0.6,
    ax=ax2
)
st.pyplot(fig2)

st.subheader("🗺️ Análise Regional por Estado")

# Mapear UFs para nomes e filtrar dados
df_filtered["ESTADO"] = df_filtered["ESTADO"].astype(str).str.upper()
df_filtered["ESTADO_NOME"] = df_filtered["ESTADO"].map(uf_para_nome_estado)
df_estado_filtrado = df_filtered[df_filtered["ESTADO"].isin(selected_ufs)]

# GeoJSON
geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson_estados = requests.get(geojson_url).json()

# DataFrame base com todos os estados (para garantir exibição no mapa)
todos_estados_df = pd.DataFrame({
    "ESTADO": lista_ufs,
    "ESTADO_NOME": [uf_para_nome_estado[uf] for uf in lista_ufs]
})

# Contratos por estado (incluindo estados sem dados)
contratos_estado = df_estado_filtrado.groupby("ESTADO_NOME").size().reset_index(name="Contratos")
contratos_estado = todos_estados_df.merge(contratos_estado, on="ESTADO_NOME", how="left").fillna(0)

# Taxa média por estado
taxa_estado = df_estado_filtrado.groupby("ESTADO_NOME")["TAXA_CLIENTE"].mean().reset_index(name="Taxa_Média")
taxa_estado = todos_estados_df.merge(taxa_estado, on="ESTADO_NOME", how="left").fillna(0)

# Mapa: Contratos
fig_mapa1 = px.choropleth(
    contratos_estado, geojson=geojson_estados, featureidkey="properties.name",
    locations="ESTADO_NOME", color="Contratos", color_continuous_scale="Blues",
    title="Número de Contratos por Estado"
)
fig_mapa1.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig_mapa1)

# Mapa: Taxa média
fig_mapa2 = px.choropleth(
    taxa_estado, geojson=geojson_estados, featureidkey="properties.name",
    locations="ESTADO_NOME", color="Taxa_Média", color_continuous_scale="Reds",
    title="Taxa Média por Estado"
)
fig_mapa2.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig_mapa2)

# Gráfico de barras por banco/estado
st.subheader("🏦 Distribuição de Bancos por Estado")
banco_estado = df_estado_filtrado.groupby(["ESTADO", "BANCO_VENCEDOR"]).size().reset_index(name="Qtd")
fig_barras = px.bar(
    banco_estado, x="ESTADO", y="Qtd", color="BANCO_VENCEDOR",
    barmode="group", title="Contratos por Banco e Estado"
)
st.plotly_chart(fig_barras)


st.subheader("🏦 Distribuição de Bancos por Estado")
banco_estado = df_filtered.groupby(["ESTADO", "BANCO_VENCEDOR"]).size().reset_index(name="Qtd")
fig_barras = px.bar(
    banco_estado, x="ESTADO", y="Qtd", color="BANCO_VENCEDOR",
    barmode="group", title="Contratos por Banco e Estado"
)
st.plotly_chart(fig_barras)

# Download da base filtrada
st.sidebar.markdown("---")
st.sidebar.download_button(
    "📥 Baixar base filtrada (CSV)",
    df_filtered.to_csv(index=False),
    file_name="financiamentos_filtrados.csv",
    mime="text/csv"
)
