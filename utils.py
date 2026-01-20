import extra_streamlit_components as stx
import streamlit as st
import pandas as pd
import datetime
import base64
import time
import os

from PIL import Image

# --- CONSTANTES GLOBAIS ---
SUBCATEGORIAS_MATERIAIS = ["Geral", "Elétrica", "Hidráulica", "Pintura"]

# --- GERENCIADOR DE COOKIES ---
def get_manager():
    return stx.CookieManager(key="session_cookie_manager")

# --- Funções de Login ---

def recuperar_sessao(supabase):
    """
    Tenta recuperar a sessão via Session State ou Cookies.
    Retorna o objeto User se autenticado, ou None se não autenticado.
    """

    # Verifica se o usuário acabou de fazer logout para evitar relogin automático imediato
    if st.session_state.get("logout_flag"):
        return None, "logout"

    # 1. Se o usuário já está logado na session_state, retorna o usuário.
    if "usuario_logado" in st.session_state and st.session_state["usuario_logado"]:
        return st.session_state["usuario_logado"], "session_state"
    
    # 2. Tenta recuperar TOKENS do Cookie via CookieManager
    if "cookie_manager" in st.session_state:
        print("Lendo cookies...", flush=True)
        cookies = st.session_state["cookie_manager"].get_all(key="get_all_mngr")

        if cookies is None:
            st.stop()

        access_token = cookies.get("sb_access_token")
        refresh_token = cookies.get("sb_refresh_token")
        print("Cookies lidos!", flush=True)
    
    if access_token and refresh_token:
        try:
            # Injeta os tokens no cliente Supabase para restaurar a sessão
            session = supabase.auth.set_session(access_token, refresh_token)
            
            if session.user:
                st.session_state["usuario_logado"] = session.user
                return session.user, "tokens"
                
        except Exception as e:
            # Se o token expirou ou é inválido, o set_session falhará.
            # A execução continuará para a tela de login.
            st.warning(f"Sua sessão expirou. Por favor, faça login novamente.")
            pass

    return None, "None"

def tela_login(supabase):
    """Login que salva Access Token E Refresh Token"""
    # st.markdown("<style> [data-testid='stSidebar'] {display: none;} </style>", unsafe_allow_html=True)
    
    # Recupera o gerenciador instanciado no app.py
    cookie_manager = st.session_state["cookie_manager"]
    
    login_placeholder = st.empty()

    with login_placeholder.container():
        col1, col2, col3 = st.columns(3)
        
        with col2:
            st.title(":material/login: Login")
            
            with st.form(key="form_login"):
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
                
    if submit:
        print("Fazendo login...", flush=True)
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            
            login_placeholder.empty()
            with st.container(horizontal_alignment="center"):
                with st.spinner():
                    time.sleep(1)

            st.session_state["usuario_logado"] = res.user
            if "logout_flag" in st.session_state:
                del st.session_state["logout_flag"]
            
            # Define validade para 7 dias (Usa datetime naive para evitar erro de serialização/tela branca)
            expire_date = datetime.datetime.now() + datetime.timedelta(days=7)
            
            cookie_manager.set("sb_access_token", res.session.access_token, expires_at=expire_date, key="set_access")
            cookie_manager.set("sb_refresh_token", res.session.refresh_token, expires_at=expire_date, key="set_refresh")
            print("Cookies salvos!", flush=True)
            time.sleep(2)
            
        except Exception as e:
            col2.error(f"Usuário ou senha incorretos.")

def botao_logout():
    if st.sidebar.button("Sair"):
        st.session_state["usuario_logado"] = None
        st.session_state["logout_flag"] = True
        
        cookie_manager = st.session_state["cookie_manager"]
        cookie_manager.delete("sb_access_token", key="delete_access")
        cookie_manager.delete("sb_refresh_token", key="delete_refresh")

        try:
            st.session_state["supabase"].auth.sign_out()
        except:
            pass

        time.sleep(2)

# --- Funções de Configuração Visual ---

def sidebar_config():    
    # Caminho absoluto para garantir que a imagem seja encontrada de qualquer página
    caminho_logo = os.path.join(os.path.dirname(__file__), 'logo_mino.JPG')
    
    # Verifica se a imagem existe para não dar erro
    if os.path.exists(caminho_logo):
        imagem = Image.open(caminho_logo)
        # Exibe no topo da sidebar
        st.sidebar.image(imagem, width="stretch")
    else:
        st.sidebar.warning("Logo não encontrada")

    botao_logout()

def adicionar_watermark():
    # Define o caminho da imagem (usando a mesma logo da sidebar)
    caminho_imagem = os.path.join(os.path.dirname(__file__), 'marca_dagua.png')
    
    if os.path.exists(caminho_imagem):
        with open(caminho_imagem, "rb") as image_file:
            # Converte a imagem para um texto base64
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        # Cria o CSS para injetar na página
        # O 'opacity: 0.08' é o que deixa ela bem clarinha (8% de opacidade)
        # O 'z-index: -1' garante que ela fique ATRÁS do texto
        estilo_css = f"""
        <style>
        /* 1. A Marca D'água no Fundo Geral */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url("data:image/png;base64,{encoded_string}");
            background-repeat: no-repeat;
            background-position: center;
            background-size: 100%;
            opacity: 1.0;
            z-index: 0;
            pointer-events: none;
        }}
        </style>
        """
        # Injeta o CSS na página
        st.markdown(estilo_css, unsafe_allow_html=True)

def reduzir_espaco_topo():
    st.markdown("""
        <style>
            /* Reduz o padding superior do container principal */
            .block-container {
                padding-top: 2rem !important; /* O padrão é por volta de 6rem */
                padding-bottom: 1rem !important;
            }
            
            /* (Opcional) Se quiser subir ainda mais o título, remova a margem do h1 */
            h1 {
                margin-top: -1rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

# --- Funções de Interação com o Banco de Dados ---
                    
def salvar_movimentacao(supabase, lista_envio, info_container=None):
    # -- Grava no Supabase --
    response = supabase.table("movimentacoes").upsert(
        lista_envio,
        on_conflict="obra_id,Data,Detalhes,Valor,Categoria,Descrição",
        ignore_duplicates=True
    ).execute()

    if info_container is None:
        info_container = st.container()
    with info_container:                    
        # --- Lógica de Feedback ---
        count = len(response.data)

        if count == 0:
            st.warning("Nenhuma novidade! Todas as linhas enviadas já existiam no banco de dados.")
        elif count < len(lista_envio):
            st.success(f"Processamento concluído: {count} novos lançamentos inseridos.")
            st.info(f"{len(lista_envio) - count} itens duplicados foram ignorados.")
        else:
            st.success(f"Movimentações salvas com sucesso!")

def salvar_obra(supabase, lista_envio, info_container=None):
    supabase.table("obras").insert(lista_envio).execute()

    if info_container is None:
        info_container = st.container()
    with info_container:
        st.success(f"Obra '{lista_envio['Nome']}' cadastrada com sucesso!")

def on_dismiss():
    if "modal" in st.session_state:
        del st.session_state["modal"]

# --- Funções de Pop-up ---

# Modal de Cadastro de Obras
@st.dialog(" ", width="medium", on_dismiss=on_dismiss)
def popup_cadastro_obras(supabase, obras_desconhecidas):
    if st.session_state.get("modal") != "Cadastro":
        st.warning(f"As seguintes obras foram digitadas mas não existem no banco de dados: {', '.join(obras_desconhecidas)}")
        
        st.write("Deseja cadastrá-las agora?")
        
        col_cancel, col_confirm = st.columns(2)
        
        with col_cancel:
            if st.button("Cancelar"):
                st.rerun(scope="app")
                
        with col_confirm:
            if st.button("Sim, Cadastrar Todas", type="primary"):
                st.session_state["modal"] = "Cadastro"
                st.rerun(scope="fragment")
    else:
        obra = obras_desconhecidas[0]
        # --- Formulário de Cadastro ---
        # Usamos 'st.form' para agrupar tudo e só enviar quando clicar no botão final
        with st.form("form_cadastro_obra"):
            
            # Dividindo a tela em duas colunas para ficar visualmente agradável
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome da Obra", value=obra, disabled=True)
                endereco = st.text_input("Endereço", placeholder="Ex: Rua das Flores, 123")
                orcamento = st.number_input("Orçamento Total (R$)", min_value=0.0, step=1000.0, format="%.2f")

            with col2:
                cliente_nome = st.text_input("Nome do Cliente")
                cliente_cpf = st.text_input("CPF do Cliente")
                col_data1, col_data2 = st.columns(2)
                data_inicio = col_data1.date_input("Data de Início", datetime.date.today(), format="DD/MM/YYYY")
                data_fim = col_data2.date_input("Previsão de Término", datetime.date.today(), format="DD/MM/YYYY")

            # Botão de confirmação
            submitted = st.form_submit_button("Criar Nova Obra")

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
                    salvar_obra(supabase, lista_envio)
                    obras_desconhecidas.pop(0)
                    if len(obras_desconhecidas) > 0:
                        time.sleep(1)
                        st.rerun(scope="fragment")
                    else:
                        time.sleep(1)
                        del st.session_state["modal"]
                        st.rerun(scope="app")

                except Exception as e:
                    st.error(f"Erro ao salvar no banco de dados: {e}")
                    if "modal" in st.session_state:
                        del st.session_state["modal"]

# Modal de Detalhamento de Materiais
@st.dialog(" ", width="large", on_dismiss=on_dismiss)
def popup_detalhar_material(supabase, lista_material):
    # --- Seleção das Movimentações de "Material" ---
    if st.session_state["modal"] == "Selecionar":
        st.info("Foram identificadas movimentações de 'Material'. Por favor, selecione abaixo aquelas que deseja detalhar.")

        # Criar DataFrame para exibir
        df_material = pd.DataFrame(lista_material)
        df_material.loc[:, "Data"] = pd.to_datetime(df_material["Data"], dayfirst=True).dt.date
        df_material.loc[:, "Detalhar"] = False
        df_material = df_material.astype({
            "Detalhes": "string",
            "Obra": "string",
            "Categoria": "string",
            "Valor": "float",
            "Descrição": "string",
            "Detalhar": "boolean",
        })

        data_editor = st.data_editor(
            df_material,
            column_config={
                "Data": st.column_config.DateColumn(label="Data", disabled=True),
                "Detalhes": st.column_config.TextColumn(label="Detalhes", disabled=True),
                "Obra": st.column_config.TextColumn(label="Obra", disabled=True),
                "Categoria": st.column_config.TextColumn(label="Categoria", disabled=True),
                "Valor": st.column_config.NumberColumn(label="Valor (R$)", disabled=True, format="R$ %.2f"),
                "Descrição": st.column_config.TextColumn(label="Descrição", disabled=True),
                "Detalhar": st.column_config.CheckboxColumn(label="Detalhar", default=False),
            },
            width="stretch",
            hide_index=True,
        )

        col_cancel, col_confirm, col_info = st.columns([1, 1, 6])
        
        with col_cancel:
            if st.button("Cancelar", width="stretch"):
                st.rerun(scope="app")
                
        with col_confirm:
            if st.button("Continuar", type="primary", width="stretch"):
                if not data_editor["Detalhar"].all():
                    # Buscar Obras para obter IDs
                    response = supabase.table("obras").select("id, Nome").execute()
                    obras_dict = {row["Nome"]: row["id"] for row in response.data} # Cria um mapa {Nome: ID}

                    # Salvar apenas os não-selecionados
                    lista_envio = [{
                        "Data": row["Data"].isoformat(),
                        "Detalhes": row["Detalhes"],
                        "obra_id": obras_dict[row["Obra"].upper()],
                        "Categoria": row["Categoria"],
                        "Valor": row["Valor"],
                        "Descrição": row["Descrição"],
                    } for index, row in data_editor.loc[~data_editor["Detalhar"]].iterrows()]

                    salvar_movimentacao(supabase, lista_envio, col_info)
                    time.sleep(1)

                if data_editor["Detalhar"].any():
                    # Entrar no modo de detalhamento
                    st.session_state["df_selecionado"] = data_editor.loc[data_editor["Detalhar"] == True]
                    st.session_state["modal"] = "Detalhar"
                    st.rerun(scope="fragment")

    # --- Detalhamento dos Materiais ---
    elif st.session_state["modal"] == "Detalhar":
        df_selecionado = st.session_state["df_selecionado"]

        st.info("Por favor, detalhe a movimentação selecionada abaixo.")

        # Formulário visual
        with st.form("form_detalhar_material"):
            col1, col2, col3, col4, col5 = st.columns(5)
            data = col2.date_input(label="Data", value=df_selecionado.iloc[0]["Data"], disabled=True)
            detalhes = col3.text_input("Detalhes", value=df_selecionado.iloc[0]["Detalhes"], disabled=True)
            obra = col4.text_input("Obra", value=df_selecionado.iloc[0]["Obra"].upper(), disabled=True)
            categoria = col2.text_input("Categoria", value=df_selecionado.iloc[0]["Categoria"], disabled=True)
            valor_total = col3.number_input("Valor Total (R$)", value=df_selecionado.iloc[0]["Valor"], format="%.2f", disabled=True)
            descricao = col4.text_input("Descrição", value=df_selecionado.iloc[0]["Descrição"], disabled=True)
            
            # Criamos um DataFrame vazio para servir de template
            df_template = pd.DataFrame({
                "Item": pd.Series(dtype="string"),
                "Subcategoria": pd.Series(dtype="string"),
                "Quantidade": pd.Series(dtype="float"),
                "Valor (R$)": pd.Series(dtype="float")
            })

            itens_compra = st.data_editor(
                df_template,
                num_rows="dynamic",
                column_config={
                    "Item": st.column_config.TextColumn(required=True),
                    "Subcategoria": st.column_config.SelectboxColumn(options=SUBCATEGORIAS_MATERIAIS),
                    "Quantidade": st.column_config.NumberColumn(min_value=0.1, step=1.0, required=True),
                    "Valor (R$)": st.column_config.NumberColumn(min_value=0.0, format="R$ %.2f", required=True)
                },
                hide_index=True,
                width="stretch",
            )

            # Botão de salvar
            if st.form_submit_button("Salvar Movimentação", type="primary"):
                if itens_compra.empty:
                    st.error("Por favor, adicione ao menos um item para detalhar a compra.")
                else:
                    # Verificar o valor total
                    total_calculado = itens_compra["Valor (R$)"].sum()

                    if abs(total_calculado - valor_total) > 0:
                        st.error(f"A soma do valor dos itens (R\\$ {total_calculado:.2f}) é diferente do valor total do extrato (R\\$ {valor_total:.2f}).")
                        st.stop()
                    else:
                        # Buscar Obras para obter IDs
                        response = supabase.table("obras").select("id, Nome").execute()
                        obras_dict = {row["Nome"]: row["id"] for row in response.data} # Cria um mapa {Nome: ID}
                        obra_id = obras_dict[obra]
                        try:
                            # Inserir como uma única movimentação com detalhamento em JSON
                            itens_list = []
                            for _, row in itens_compra.iterrows():
                                itens_list.append({
                                    "Item": row["Item"],
                                    "Subcategoria": row["Subcategoria"],
                                    "Quantidade": row["Quantidade"],
                                    "Valor": row["Valor (R$)"]
                                })

                            lista_envio = [{
                                "obra_id": obra_id,
                                "Data": data.isoformat(),
                                "Detalhes": detalhes,
                                "Categoria": categoria,
                                "Valor": valor_total,
                                "Descrição": descricao,
                                "Itens": itens_list
                            }]

                            salvar_movimentacao(supabase, lista_envio)
                            time.sleep(1)
                            
                            # Remover a movimentação já detalhada da lista
                            df_selecionado = df_selecionado.drop(df_selecionado.index[0])
                            if len(df_selecionado) > 0:
                                st.session_state["df_selecionado"] = df_selecionado
                                st.rerun(scope="fragment")
                            else:
                                del st.session_state["modal"]
                                del st.session_state["df_selecionado"]
                                st.rerun(scope="app")

                        except Exception as e:
                            st.error(f"Erro ao salvar no banco de dados: {e}")
                        