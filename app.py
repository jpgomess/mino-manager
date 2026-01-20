import streamlit as st
import utils

from supabase import create_client

# --- Configuração Inicial ---
st.set_page_config(
    page_title="Mino Manager", 
    layout="wide"
)

# --- DIAGNÓSTICO DE COOKIES (Remover após corrigir) ---
import datetime
st.sidebar.header("🔧 Debug Cookies")
if hasattr(st, "context") and hasattr(st.context, "cookies"):
    cookies_presentes = st.context.cookies
    st.sidebar.write(f"Cookies Detectados: {len(cookies_presentes)}")
    if "sb_access_token" in cookies_presentes:
        st.sidebar.success("✅ Token de Acesso Encontrado")
    else:
        st.sidebar.error("❌ Token de Acesso AUSENTE")
else:
    st.sidebar.warning("⚠️ st.context.cookies não disponível")
st.sidebar.write(f"Hora Servidor: {datetime.datetime.now().strftime('%H:%M:%S')}")
# ------------------------------------------------------

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
usuario = utils.recuperar_sessao(supabase)

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