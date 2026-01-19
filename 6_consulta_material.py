import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Consultar Materiais", layout="wide")

utils.sidebar_config()
utils.reduzir_espaco_topo()
utils.adicionar_watermark()

# --- Conexão com Supabase ---
supabase = st.session_state["supabase"]

# --- Título da Página ---

st.title("Rastreamento de Materiais 🧱")

# 1. Carregar Obras (Para traduzir o ID da obra para o Nome da Obra)
res_obras = supabase.table("obras").select("id, Nome").execute()
mapa_obras = {row["id"]: row["Nome"] for row in res_obras.data}

# 2. Carregar TODOS os materiais lançados
response = supabase.table("movimentacoes").select("*").eq("Categoria", "Material").execute()

if not response.data:
    st.info("Nenhum material foi lançado no sistema ainda.")
    st.stop()

df_raw = pd.DataFrame(response.data)

# Expansão dos itens JSON para linhas individuais (para manter a lógica de análise)
rows_expanded = []
for _, row in df_raw.iterrows():
    if "Itens" in row and row["Itens"] is not None and isinstance(row["Itens"], list) and len(row["Itens"]) > 0:
        for item in row["Itens"]:
            new_row = row.copy()
            new_row["Item"] = item.get("Item", "")
            new_row["Subcategoria"] = item.get("Subcategoria", "")
            new_row["Quantidade"] = item.get("Quantidade", 0)
            new_row["Valor"] = item.get("Valor", 0)
            rows_expanded.append(new_row)
    else:
        rows_expanded.append(row)

df = pd.DataFrame(rows_expanded)

# Tratamento de dados
# Garante que números são números
df["Quantidade"] = pd.to_numeric(df["Quantidade"])
df["Valor"] = pd.to_numeric(df["Valor"])

# Cria uma coluna com o NOME da obra (usando o mapa que criamos no passo 1)
df["Obra"] = df["obra_id"].map(mapa_obras)

# 3. Seletor de Material
subcategoria_selecionada = st.selectbox(
    label="Selecione a Subcategoria de Material:",
    options=utils.SUBCATEGORIAS_MATERIAIS,
)

# 4. Filtrar dados apenas dessa subcategoria
df_filtrado = df[df["Subcategoria"] == subcategoria_selecionada].copy()
st.divider()

if df_filtrado.empty:
    st.info(f"Nenhuma compra registrada para a subcategoria '{subcategoria_selecionada}'.")
else:
    # --- Métricas Gerais do Material ---
    col1, col2, col3 = st.columns(3)

    qtd_total = df_filtrado["Quantidade"].sum()
    gasto_total = df_filtrado["Valor"].sum()
    preco_medio = df_filtrado["Valor"].mean()

    col1.metric("Quantidade Total Comprada", f"{qtd_total:,.1f}")
    col2.metric("Gasto Total Acumulado", f"R$ {gasto_total:,.2f}")
    col3.metric("Preço Médio Unitário", f"R$ {preco_medio:,.2f}")

    # --- Análise Visual e Tabela ---
    tab1, tab2 = st.tabs(["📝 Histórico Completo", "📊 Comparativo por Obra"])

    with tab1:
        st.subheader(f"Todas as compras de '{subcategoria_selecionada}'")

        tabela_final = df_filtrado[[
            "Data", "Obra", "Descrição", "Quantidade", "Valor"
        ]].sort_values("Data", ascending=False)
        
        st.dataframe(
            tabela_final,
            column_config={
                "Data": st.column_config.DateColumn("Data"),
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "Quantidade": st.column_config.NumberColumn("Quantidade")
            },
            width="stretch",
            hide_index=True
        )

    with tab2:
        # Gráfico: Qual obra consumiu mais esse material?
        # Agrupa por obra somando a quantidade
        df_por_obra = df_filtrado.groupby("Obra")[["Quantidade", "Valor"]].sum().reset_index()
        
        col_g1, col_g2 = st.columns(2)
        
        # Gráfico de Barras: Quantidade por Obra
        fig_qtd = px.bar(
            df_por_obra, 
            x="Obra", 
            y="Quantidade", 
            title=f"Consumo de '{subcategoria_selecionada}' por Obra (Qtd)",
            text_auto=True
        )
        fig_qtd.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)',  paper_bgcolor='rgba(0, 0, 0, 0)', legend=dict(bgcolor='rgba(0, 0, 0, 0)'))

        col_g1.plotly_chart(fig_qtd, width="stretch")
        
        # Gráfico de Dispersão: Variação de Preço (Detectar se pagou caro)
        # Eixo X = Data, Eixo Y = Preço Unitário, Cor = Obra
        if "Data" in df_filtrado.columns:
            fig_preco = px.scatter(
                df_filtrado, 
                x="Data", 
                y="Valor", 
                color="Obra",
                size="Quantidade",
                title=f"Histórico de Preço Unitário: '{subcategoria_selecionada}'",
                hover_data=["Descrição"]
            )
            fig_preco.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)',  paper_bgcolor='rgba(0, 0, 0, 0)', legend=dict(bgcolor='rgba(0, 0, 0, 0)'))

            col_g2.plotly_chart(fig_preco, width="stretch")
