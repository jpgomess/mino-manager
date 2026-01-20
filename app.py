import streamlit as st
import utils

from supabase import create_client

# --- Configuração Inicial ---
st.set_page_config(
    page_title="Mino Manager", 
    layout="wide"
)

# --- Inicialização do Supabase (Global) ---
if "supabase" not in st.session_state:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    st.session_state["supabase"] = create_client(url, key)

supabase = st.session_state["supabase"]

# --- Inicialização do CookieManager (Singleton) ---
# Instancia uma única vez por execução e salva para uso nas funções de utils
st.session_state["cookie_manager"] = utils.get_manager()

# --- Verificação de Autenticação ---
usuario, mode = utils.recuperar_sessao(supabase)
st.write(f"Modo de recuperação de sessão: {mode}")

# --- Definição das Páginas ---
if not usuario:
    pg = st.navigation([st.Page(lambda: utils.tela_login(supabase), title="Login", icon=":material/login:")])
else:
    # Se ESTIVER logado, carrega a estrutura completa
    pg = st.navigation(
        {
            "": [st.Page("1_home.py", title="Home", icon=":material/home:")],
            "Cadastro": [
                st.Page("2_page_cadastro_obra.py", title="Cadastro de Obra", icon=":material/add_home_work:"),
                st.Page("3_movimentacao.py", title="Lançamento", icon=":material/list_alt_add:"),
                st.Page("4_extrato.py", title="Importar Extrato", icon=":material/upload_file:"),
            ],
            "Consulta": [
                st.Page("5_consulta_obra.py", title="Consulta de Obra", icon=":material/manage_search:"),
                st.Page("6_consulta_material.py", title="Consulta de Material", icon=":material/construction:"),
            ]
        }
    )

pg.run()