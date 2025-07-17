
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
]

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

fig1, ax1 = plt.subplots(figsize=(5,3))
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
var_hist = st.selectbox("Selecione a variável para o histograma:", variaveis)
stat = st.radio("Eixo Y:", ["density", "count"], index=0)
common_norm = st.checkbox("Normalizar todos os bancos juntos (common_norm=True)", value=True)
multiple_option = st.selectbox("Modo de sobreposição das distribuições:",["layer", "stack", "dodge", "fill"],  index=0)
is_discrete = st.checkbox("Tratar variável como discreta (discrete=True)", value=False)

fig2, ax2 = plt.subplots(figsize=(5,3))
sns.histplot(
    data=df_filtered,
    x=var_hist,
    hue="BANCO_VENCEDOR",
    bins=30,
    kde=True,
    stat=stat,
    common_norm=common_norm,
    multiple=multiple_option,
    discrete=is_discrete,
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
