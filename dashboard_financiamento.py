
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Carregar os dados do CSV exportado
@st.cache_data
def load_data():
    return pd.read_csv("dataset_financiamentos_filtrado.csv")

df = load_data()

# Título do app
st.title("Análise Interativa de Financiamentos - Contratos Até R$70.000")

# Filtros interativos
bancos = df["BANCO_VENCEDOR"].dropna().unique().tolist()
selected_bancos = st.multiselect("Selecione os bancos para análise:", bancos, default=bancos)

# Intervalo de valor financiado
valor_range = st.slider("Intervalo de Valor Financiado:", 0, 70000, (0, 70000), step=1000)

# Aplicar filtros
df_filtered = df[
    (df["BANCO_VENCEDOR"].isin(selected_bancos)) &
    (df["VALOR_FINAL"] >= valor_range[0]) &
    (df["VALOR_FINAL"] <= valor_range[1])
]

# Gráfico de dispersão interativo
st.subheader("Relação entre Taxa, Valor Final e Parcelas")
fig1, ax1 = plt.subplots()
sns.scatterplot(
    data=df_filtered,
    x="VALOR_FINAL",
    y="TAXA_CLIENTE",
    hue="BANCO_VENCEDOR",
    size="QTD_PARCELA",
    alpha=0.6,
    ax=ax1
)
plt.xlabel("Valor Financiado (R$)")
plt.ylabel("Taxa do Cliente (%)")
st.pyplot(fig1)

# Histograma de spread
st.subheader("Distribuição do Spread Efetivo")
fig2, ax2 = plt.subplots()
sns.histplot(df_filtered["SPREAD_EFETIVO"], bins=30, kde=True, ax=ax2, color="purple", alpha=0.6)
plt.xlabel("Spread Efetivo")
st.pyplot(fig2)

# Estatísticas
st.subheader("Resumo Estatístico")
st.write(df_filtered.describe())
