import streamlit as st
import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

# --- Configuração Inicial ---
st.set_page_config(page_title="Cadastro de Obras")

utils.sidebar_config()
utils.reduzir_espaco_topo()
utils.adicionar_watermark()

# --- Conexão com Supabase ---
supabase = st.session_state["supabase"]

# --- Título da Página ---

st.title("Cadastro de Nova Obra 🏗️")
st.markdown("Preencha as informações abaixo para iniciar uma nova gestão.")

# --- Formulário de Cadastro ---
# Usamos 'st.form' para agrupar tudo e só enviar quando clicar no botão final
with st.form("form_cadastro_obra"):
    
    # Dividindo a tela em duas colunas para ficar visualmente agradável
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome da Obra", placeholder="Ex: Patamares").upper()
        endereco = st.text_input("Endereço", placeholder="Ex: Rua das Flores, 123")
        orcamento = st.number_input("Orçamento Total (R$)", min_value=0.0, step=1000.0, format="%.2f")

    with col2:
        cliente_nome = st.text_input("Nome do Cliente")
        cliente_cpf = st.text_input("CPF do Cliente")
        col_data1, col_data2 = st.columns(2)
        data_inicio = col_data1.date_input("Data de Início", datetime.date.today(), format="DD/MM/YYYY")
        data_fim = col_data2.date_input("Previsão de Término", datetime.date.today(), format="DD/MM/YYYY")

    # Botão de confirmação
    submitted = st.form_submit_button("Criar Nova Obra", type="primary")

    if submitted:
        # 1. Validação dos Campos

        # Verificar preenchimento dos campos
        for field in [nome, endereco, orcamento, cliente_nome, cliente_cpf]:
            if not field:
                st.error("Por favor, preencha todos os campos.")
                st.stop()
        # Verificar CPF válido (11 dígitos numéricos)
        if len(cliente_cpf) != 11 or not cliente_cpf.isdigit():
            st.error("CPF inválido. Deve conter 11 dígitos numéricos.")
            st.stop()
        # Verificar datas lógicas
        if data_fim < data_inicio or data_inicio == data_fim:
            st.error("A data de término deve ser posterior à data de início.")
            st.stop()
        # Verificar se a obra já existe
        existing_data = supabase.table("obras").select("id").eq("Nome", nome).execute()
        if len(existing_data.data) > 0:
            st.warning(f"Atenção: Já existe uma obra cadastrada com o nome '{nome}'.")
            st.stop()

        # 2. Inserir no Banco de Dados
        lista_envio = {
            "Nome": nome,
            "Endereço": endereco,
            "Cliente_Nome": cliente_nome,
            "Cliente_CPF": cliente_cpf,
            "Orçamento": orcamento,
            "Data_Início": data_inicio.isoformat(),
            "Data_Fim": data_fim.isoformat()
        }
        
        try:
            utils.salvar_obra(supabase, lista_envio)
        except Exception as e:
            st.error(f"Erro ao salvar no banco de dados: {e}")
