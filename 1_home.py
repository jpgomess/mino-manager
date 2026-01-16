import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import utils

# --- Configuração da Página ---
st.set_page_config(
    page_title="Gestão de Obras - Visão Geral",
    page_icon="🏗️",
    layout="wide"
)

utils.sidebar_config()
utils.reduzir_espaco_topo()
utils.adicionar_watermark()

# --- Conexão com Supabase ---
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

if "supabase" not in st.session_state:
    st.session_state["supabase"] = init_connection()

supabase = st.session_state["supabase"]

# --- Título da Página ---

st.title("Painel de Controle da Empresa 🏗️")
st.markdown("Bem-vindo ao sistema de gestão unificada de obras.")

# --- 1. Carregamento de Dados ---
# Buscamos TUDO de uma vez para processar as estatísticas
try:
    # Busca Obras
    tab_obras = supabase.table("obras").select("*").execute()
    df_obras = pd.DataFrame(tab_obras.data)
    
    # Busca Movimentações
    tab_mov = supabase.table("movimentacoes").select("*").execute()
    df_mov = pd.DataFrame(tab_mov.data)

except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

# Verificação se existem dados para não quebrar o dashboard
if df_obras.empty:
    st.warning("Nenhuma obra cadastrada. Utilize o menu lateral para começar.")
    st.stop()

# --- 2. Processamento de Dados ---

# Garantir tipos numéricos
df_obras["Orçamento"] = pd.to_numeric(df_obras["Orçamento"], errors="coerce").fillna(0)

if not df_mov.empty:
    df_mov["Valor"] = pd.to_numeric(df_mov["Valor"], errors="coerce").fillna(0)
    
    # Agrupar gastos por Obra
    gastos_por_obra = df_mov.groupby("obra_id")["Valor"].sum().reset_index()
    gastos_por_obra.rename(columns={"Valor": "total_gasto"}, inplace=True)
    
    # Agrupar gastos por Categoria (Visão Empresa)
    gastos_por_categoria = df_mov.groupby("Categoria")["Valor"].sum().reset_index()
else:
    # Se não tiver gastos ainda, cria dataframes vazios com as colunas certas
    gastos_por_obra = pd.DataFrame(columns=["obra_id", "total_gasto"])
    gastos_por_categoria = pd.DataFrame(columns=["Categoria", "Valor"])

# Juntar (Merge) os dados das obras com os gastos
# Left Join: Queremos todas as obras, mesmo as que não têm gastos
df_resumo = pd.merge(df_obras, gastos_por_obra, left_on="id", right_on="obra_id", how="left")

# Preencher obras sem gastos com 0
df_resumo["total_gasto"] = df_resumo["total_gasto"].fillna(0)

# Calcular Saldo e Percentual
df_resumo["saldo"] = df_resumo["Orçamento"] - df_resumo["total_gasto"]
df_resumo["percentual_uso"] = (df_resumo["total_gasto"] / df_resumo["Orçamento"]) * 100
# Evitar divisão por zero ou infinitos
df_resumo["percentual_uso"] = df_resumo["percentual_uso"].fillna(0)

# --- 3. Layout do Dashboard ---

# SEÇÃO A: Métricas Globais (Big Numbers)
st.divider()
total_orcado_empresa = df_resumo["Orçamento"].sum()
total_gasto_empresa = df_resumo["total_gasto"].sum()
saldo_geral = total_orcado_empresa - total_gasto_empresa

col1, col2, col3, col4 = st.columns(4)

col1.metric("Obras Ativas", len(df_resumo))
col2.metric("Orçamento Global", f"R$ {total_orcado_empresa:,.2f}")
col3.metric("Total Gasto (Empresa)", f"R$ {total_gasto_empresa:,.2f}")
col4.metric(
    "Saldo em Caixa", 
    f"R$ {saldo_geral:,.2f}", 
    delta="Lucro Previsto" if saldo_geral > 0 else "Prejuízo",
    delta_color="normal" if saldo_geral > 0 else "inverse"
)

st.divider()

# SEÇÃO B: Gráficos
col_graf1, col_graf2 = st.columns(2) # O primeiro gráfico ocupa mais espaço

with col_graf1:
    st.subheader("Orçamento vs. Realizado (Por Obra)")
    if not df_resumo.empty:
        # Transformar dados para formato "longo" que o Plotly gosta para barras agrupadas
        # Queremos comparar duas barras: Azul (Orçamento) e Vermelho (Gasto)
        fig_barras = px.bar(
            df_resumo,
            x="Nome",
            y=["Orçamento", "total_gasto"],
            barmode="group",
            title="Comparativo Financeiro por Obra",
            labels={"value": "Valor (R$)", "Nome": "Obra", "variable": "Tipo"},
            color_discrete_map={"Orçamento": "#2E86C1", "total_gasto": "#E74C3C"} # Azul e Vermelho
        )
        # Ajuste de nomes na legenda
        new_names = {"Orçamento": "Orçamento Total", "total_gasto": "Já Gasto"}
        fig_barras.for_each_trace(lambda t: t.update(name = new_names[t.name]))
        fig_barras.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)',  paper_bgcolor='rgba(0, 0, 0, 0)', legend=dict(bgcolor='rgba(0, 0, 0, 0)'))

        st.plotly_chart(fig_barras, width="stretch")

with col_graf2:
    st.subheader("Para onde vai o dinheiro?")
    if not gastos_por_categoria.empty:
        # CORREÇÃO: Usamos px.pie com o argumento hole=0.4 para virar uma rosca
        fig_pizza = px.pie(
            gastos_por_categoria,
            values="Valor",
            names="Categoria",
            title="Distribuição de Custos",
            hole=0.4  # Isso transforma a pizza em uma rosca
        )
        fig_pizza.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)',  paper_bgcolor='rgba(0, 0, 0, 0)', legend=dict(bgcolor='rgba(0, 0, 0, 0)'))

        st.plotly_chart(fig_pizza, width="stretch")
    else:
        st.info("Sem dados de gastos para gerar gráfico.")

# SEÇÃO C: Tabela de Resumo Gerencial
st.divider()
st.subheader("Resumo Detalhado das Obras")

# Selecionar e ordenar colunas para exibição
colunas_exibicao = ["Nome", "Cliente_Nome", "Data_Início", "Orçamento", "total_gasto", "saldo", "percentual_uso"]

st.dataframe(
    df_resumo[colunas_exibicao].sort_values("percentual_uso", ascending=False),
    column_config={
        "Nome": "Obra",
        "Cliente_Nome": "Cliente",
        "Data_Início": st.column_config.DateColumn("Início", format="DD/MM/YYYY"),
        "Orçamento": st.column_config.NumberColumn("Orçamento", format="R$ %.2f"),
        "total_gasto": st.column_config.NumberColumn("Gasto Real", format="R$ %.2f"),
        "saldo": st.column_config.NumberColumn("Saldo", format="R$ %.2f"),
        "percentual_uso": st.column_config.ProgressColumn(
            "% Consumido", 
            format="%.1f%%", 
            min_value=0, 
            max_value=100
        ),
    },
    width="stretch",
    hide_index=True
)
