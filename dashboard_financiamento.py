
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Carregar dados
@st.cache_data
def load_data():
    return pd.read_csv("dataset_financiamentos_filtrado.csv")

df = load_data()

# Título
st.title("Análise Interativa de Financiamentos - Contratos Até R$70.000")

# Variáveis para análise
variaveis = [
    "VALOR_FINAL", "VALOR_PARCELA", "QTD_PARCELA", "CARENCIA",
    "TAXA_CLIENTE", "VALOR_TOTAL_PAGAR", "SPREAD_EFETIVO"
]

# Filtros
bancos = df["BANCO_VENCEDOR"].dropna().unique().tolist()
selected_bancos = st.multiselect("Selecione os bancos para análise:", bancos, default=bancos)

valor_range = st.slider("Intervalo de Valor Financiado:", 0, 70000, (0, 70000), step=1000)

df_filtered = df[
    (df["BANCO_VENCEDOR"].isin(selected_bancos)) &
    (df["VALOR_FINAL"] >= valor_range[0]) &
    (df["VALOR_FINAL"] <= valor_range[1])
].copy()

# Transformar CARENCIA e QTD_PARCELA em categorias, para evitar lacunas no histograma
carencia_ordenada = sorted(df_filtered["CARENCIA"].dropna().unique().astype(int))
df_filtered["CARENCIA_LABEL"] = pd.Categorical(
    df_filtered["CARENCIA"].astype(int).astype(str),
    categories=[str(x) for x in carencia_ordenada],
    ordered=True
)

parcelas_ordenada = sorted(df_filtered["QTD_PARCELA"].dropna().unique().astype(int))
df_filtered["QTD_PARCELA_LABEL"] = pd.Categorical(
    df_filtered["QTD_PARCELA"].astype(int).astype(str),
    categories=[str(x) for x in parcelas_ordenada],
    ordered=True
)

# Seção: Resumo estatístico por banco
st.subheader("📊 Resumo Estatístico por Banco")
resumo_bancos = df_filtered.groupby("BANCO_VENCEDOR")[variaveis].agg(
    ["count", "mean", "median", "std", "min", "max"]
).round(2)
st.dataframe(resumo_bancos)

# Seção: Gráfico de dispersão entre variáveis
st.subheader("🔍 Análise Bivariada entre Variáveis")
x_var = st.selectbox("Eixo X:", variaveis, index=0)
y_var = st.selectbox("Eixo Y:", variaveis, index=1)

fig1, ax1 = plt.subplots(figsize=(5, 3))
sns.scatterplot(
    data=df_filtered,
    x=x_var,
    y=y_var,
    hue="BANCO_VENCEDOR",
    alpha=0.6,
    ax=ax1
)
st.pyplot(fig1)

# Seção: Histogramas por variável
st.subheader("📈 Distribuição de Variáveis por Banco")

var_hist = st.selectbox("Variável para o histograma:", variaveis)

# Configurações visuais
stat = st.radio("Eixo Y:", ["density", "count"], index=0)
common_norm = st.checkbox("Normalizar todos os bancos juntos (common_norm=True)", value=True)
multiple_option = st.selectbox(
    "Modo de sobreposição das distribuições:",
    ["layer", "stack", "dodge", "fill"],
    index=0
)

# Lógica para variáveis discretas
if var_hist in ["CARENCIA", "QTD_PARCELA"]:
    var_hist_plot = var_hist + "_LABEL"
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
    bins=30 if not use_discrete else None,
    kde=kde,
    stat=stat,
    common_norm=common_norm,
    multiple=multiple_option,
    discrete=use_discrete,
    alpha=0.6,
    ax=ax2
)
st.pyplot(fig2)

# Download da base filtrada
st.download_button(
    "📥 Baixar base filtrada (CSV)",
    df_filtered.to_csv(index=False),
    file_name="financiamentos_filtrados.csv",
    mime="text/csv"
)

st.subheader("🗺️ Análise Regional por Estado")

# Converter ESTADO para string e garantir consistência
df_filtered["ESTADO"] = df_filtered["ESTADO"].astype(str).str.upper()

# Contagem de contratos por estado
contratos_por_estado = df_filtered.groupby("ESTADO").size().reset_index(name="Contratos")

# Taxa média por estado
taxa_media_estado = df_filtered.groupby("ESTADO")["TAXA_CLIENTE"].mean().reset_index(name="Taxa_Média")

# Distribuição por banco (quantidade por banco por estado)
banco_estado = df_filtered.groupby(["ESTADO", "BANCO_VENCEDOR"]).size().reset_index(name="Qtd")

# -------------------------------
# Mapa 1: Número de contratos por estado
fig_mapa1 = px.choropleth(
    contratos_por_estado,
    locations="ESTADO",
    locationmode="USA-states",
    color="Contratos",
    color_continuous_scale="Blues",
    scope="south america",
    labels={"ESTADO": "UF"},
    title="Número de Contratos por Estado",
)
st.plotly_chart(fig_mapa1)

# -------------------------------
# Mapa 2: Taxa média por estado
fig_mapa2 = px.choropleth(
    taxa_media_estado,
    locations="ESTADO",
    locationmode="USA-states",
    color="Taxa_Média",
    color_continuous_scale="Reds",
    scope="south america",
    labels={"ESTADO": "UF"},
    title="Taxa Média por Estado",
)
st.plotly_chart(fig_mapa2)

# -------------------------------
# Gráfico 3: Distribuição de bancos por estado
st.subheader("🏦 Distribuição de Bancos por Estado")

fig_barras = px.bar(
    banco_estado,
    x="ESTADO",
    y="Qtd",
    color="BANCO_VENCEDOR",
    barmode="group",
    title="Quantidade de Contratos por Banco e Estado"
)
st.plotly_chart(fig_barras)