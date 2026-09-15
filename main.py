from flask import Flask, render_template, request, jsonify, session, redirect, url_for

import psycopg2
from psycopg2 import OperationalError
import os
import uuid
from datetime import date, timedelta
from dotenv import load_dotenv 

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv( "FLASK_SECRET_KEY", "chave-temporaria-do-projeto" ) 
# ========================================================= # CONEXÃO COM O BANCO # =========================================================
def get_connection():
    """Abre uma nova conexão PostgreSQL usando variáveis de ambiente."""
    try:

        return psycopg2.connect( 
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
            sslmode="require")
    except OperationalError as erro:
        print("Erro na conexão com o banco:", erro)
        return None


# =========================================================
# LOGIN
# =========================================================

@app.route("/")
def login():
   
    return render_template("login.html")


# =========================================================
# ENTRAR
# =========================================================

@app.route("/entrar", methods=["POST"])
def entrar():

    tipo_usuario = request.form.get("tipo_usuario")

    # -----------------------------------------------------
    # TEMPORÁRIO
    # Depois faremos autenticação real pelo banco
    # -----------------------------------------------------

    if tipo_usuario == "adm":

        session["usuario_id"] = 1
        session["tipo_usuario"] = "adm"

        return redirect(
            url_for("dashboard_adm")
        )


    elif tipo_usuario == "funcionario":

        # TEMPORÁRIO
        # Depois o ID virá do login real

        session["usuario_id"] = 1
        session["tipo_usuario"] = "funcionario"

        return redirect(
            url_for("inicio_funcionario")
        )


    return redirect(
        url_for("login")
    )


# =========================================================
# SAIR
# =========================================================

@app.route("/sair")
def sair():

    session.clear()

    return redirect(
        url_for("login")
    )

# =========================================================
# DASHBOARD ADMINISTRADOR
# =========================================================

@app.route("/dashboard-adm")
def dashboard_adm():

    

    # -------------------------------------------------
    # FILTRO POR PERÍODO
    # -------------------------------------------------

    periodo = request.args.get(
        "periodo",
        ""
    )

    funcionario_id = request.args.get(
        "funcionario",
        ""
    )

    etapa = request.args.get(
        "etapa",
        ""
    )

    data_inicio_texto = request.args.get(
        "data_inicio",
        ""
    )

    data_fim_texto = request.args.get(
        "data_fim",
        ""
    )

    hoje = date.today()

    data_inicio = None
    data_fim = None


    if periodo == "hoje":

        data_inicio = hoje
        data_fim = hoje


    elif periodo == "semana":

        data_inicio = hoje - timedelta(
            days=hoje.weekday()
        )

        data_fim = hoje


    elif periodo == "mes":

        data_inicio = hoje.replace(
            day=1
        )

        data_fim = hoje


    elif periodo == "personalizado":

        try:

            if data_inicio_texto:

                data_inicio = date.fromisoformat(
                    data_inicio_texto
                )

            if data_fim_texto:

                data_fim = date.fromisoformat(
                    data_fim_texto
                )

        except ValueError:

            data_inicio = None
            data_fim = None


    # -------------------------------------------------
    # CONEXÃO
    # -------------------------------------------------

    conn = get_connection()

    if conn is None:

        return (
            "Não foi possível conectar ao banco.",
            500
        )

    cursor = None


    try:

        cursor = conn.cursor()


        # -------------------------------------------------
        # PRODUÇÃO TOTAL DE HOJE
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COALESCE(
                SUM(
                    COALESCE(quantidade_p, 0) +
                    COALESCE(quantidade_m, 0) +
                    COALESCE(quantidade_g, 0) +
                    COALESCE(quantidade_gg, 0) +
                    COALESCE(quantidade_xg, 0)
                ),
                0
            )

            FROM producoes

            WHERE data_producao = CURRENT_DATE
            """
        )

        producao_hoje = cursor.fetchone()[0]


        # -------------------------------------------------
        # PRODUÇÃO TOTAL DO MÊS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COALESCE(
                SUM(
                    COALESCE(quantidade_p, 0) +
                    COALESCE(quantidade_m, 0) +
                    COALESCE(quantidade_g, 0) +
                    COALESCE(quantidade_gg, 0) +
                    COALESCE(quantidade_xg, 0)
                ),
                0
            )

            FROM producoes

            WHERE DATE_TRUNC(
                'month',
                data_producao
            )
            =
            DATE_TRUNC(
                'month',
                CURRENT_DATE
            )
            """
        )

        producao_mes = cursor.fetchone()[0]


        # -------------------------------------------------
        # FUNCIONÁRIOS ATIVOS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)

            FROM usuarios

            WHERE ativo = TRUE
            """
        )

        funcionarios_ativos = cursor.fetchone()[0]


        # -------------------------------------------------
        # LISTA DE FUNCIONÁRIOS PARA O FILTRO
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                nome

            FROM usuarios

            WHERE ativo = TRUE

            ORDER BY nome
            """
        )

        funcionarios_filtro = cursor.fetchall()


        # -------------------------------------------------
        # FILTRO DA PRODUÇÃO POR FUNCIONÁRIO
        # -------------------------------------------------

        condicao_data = ""
        condicao_funcionario = ""
        condicao_etapa = ""
        parametros = []


        if data_inicio is not None:

            condicao_data += """
                AND producoes.data_producao >= %s
            """

            parametros.append(
                data_inicio
            )


        if data_fim is not None:

            condicao_data += """
                AND producoes.data_producao <= %s
            """

            parametros.append(
                data_fim
            )

        if etapa:

            condicao_etapa = """
                AND producoes.etapa = %s
            """

            parametros.append(
                etapa
            )

        if funcionario_id:

            condicao_funcionario = """
                AND usuarios.id = %s
            """

            parametros.append(
                funcionario_id
            )

        # -------------------------------------------------
        # PRODUÇÃO POR FUNCIONÁRIO
        # -------------------------------------------------

        query_funcionarios = f"""
            SELECT
                usuarios.id,
                usuarios.nome,

                COALESCE(
                    SUM(
                        COALESCE(producoes.quantidade_p, 0) +
                        COALESCE(producoes.quantidade_m, 0) +
                        COALESCE(producoes.quantidade_g, 0) +
                        COALESCE(producoes.quantidade_gg, 0) +
                        COALESCE(producoes.quantidade_xg, 0)
                    ),
                    0
                ) AS total_produzido,

                MAX(
                    producoes.data_producao
                ) AS ultima_producao

            FROM usuarios

            LEFT JOIN producoes
                ON usuarios.id = producoes.usuario_id
                {condicao_data}
                {condicao_etapa}

            WHERE usuarios.ativo = TRUE
            {condicao_funcionario}

            GROUP BY
                usuarios.id,
                usuarios.nome

            ORDER BY
                usuarios.nome
        """


        cursor.execute(
            query_funcionarios,
            parametros
        )

        producao_funcionarios = cursor.fetchall()

                # -------------------------------------------------
        # CARDS COM BASE NOS FILTROS
        # -------------------------------------------------

        producao_filtrada = sum(
            funcionario[2] or 0
            for funcionario in producao_funcionarios
        )

        funcionarios_filtrados = sum(
            1
            for funcionario in producao_funcionarios
            if (funcionario[2] or 0) > 0
        )

                # -------------------------------------------------
        # RESUMO POR PRODUTO
        # -------------------------------------------------

        parametros_produtos = []

        condicao_produto_data = ""
        condicao_produto_funcionario = ""
        condicao_produto_etapa = ""


        if data_inicio is not None:

            condicao_produto_data += """
                AND producoes.data_producao >= %s
            """

            parametros_produtos.append(
                data_inicio
            )


        if data_fim is not None:

            condicao_produto_data += """
                AND producoes.data_producao <= %s
            """

            parametros_produtos.append(
                data_fim
            )


        if funcionario_id:

            condicao_produto_funcionario = """
                AND producoes.usuario_id = %s
            """

            parametros_produtos.append(
                funcionario_id
            )


        if etapa:

            condicao_produto_etapa = """
                AND producoes.etapa = %s
            """

            parametros_produtos.append(
                etapa
            )


        query_produtos = f"""
            SELECT
                produto,

                SUM(
                    COALESCE(quantidade_p, 0) +
                    COALESCE(quantidade_m, 0) +
                    COALESCE(quantidade_g, 0) +
                    COALESCE(quantidade_gg, 0) +
                    COALESCE(quantidade_xg, 0)
                ) AS quantidade

            FROM producoes

            WHERE 1 = 1

            {condicao_produto_data}

            {condicao_produto_funcionario}

            {condicao_produto_etapa}

            GROUP BY produto

            ORDER BY quantidade DESC
        """


        cursor.execute(
            query_produtos,
            parametros_produtos
        )

        resumo_produtos = cursor.fetchall()

        produtos_filtrados = len(resumo_produtos)

                # -------------------------------------------------
        # RESUMO POR COR E TAMANHO
        # -------------------------------------------------

        parametros_cores = []

        condicao_cor_data = ""
        condicao_cor_funcionario = ""
        condicao_cor_etapa = ""


        if data_inicio is not None:

            condicao_cor_data += """
                AND producoes.data_producao >= %s
            """

            parametros_cores.append(
                data_inicio
            )


        if data_fim is not None:

            condicao_cor_data += """
                AND producoes.data_producao <= %s
            """

            parametros_cores.append(
                data_fim
            )


        if etapa:

            condicao_cor_etapa = """
                AND producoes.etapa = %s
            """

            parametros_cores.append(
                etapa
            )


        if funcionario_id:

            condicao_cor_funcionario = """
                AND producoes.usuario_id = %s
            """

            parametros_cores.append(
                funcionario_id
            )


        query_cores = f"""
            SELECT
                cor,

                SUM(COALESCE(quantidade_p, 0)) AS total_p,

                SUM(COALESCE(quantidade_m, 0)) AS total_m,

                SUM(COALESCE(quantidade_g, 0)) AS total_g,

                SUM(COALESCE(quantidade_gg, 0)) AS total_gg,

                SUM(COALESCE(quantidade_xg, 0)) AS total_xg,

                SUM(
                    COALESCE(quantidade_p, 0) +
                    COALESCE(quantidade_m, 0) +
                    COALESCE(quantidade_g, 0) +
                    COALESCE(quantidade_gg, 0) +
                    COALESCE(quantidade_xg, 0)
                ) AS total

            FROM producoes

            WHERE 1 = 1

            {condicao_cor_data}

            {condicao_cor_etapa}

            {condicao_cor_funcionario}

            GROUP BY cor

            ORDER BY total DESC
        """


        cursor.execute(
            query_cores,
            parametros_cores
        )

        resumo_cores = cursor.fetchall()


        # -------------------------------------------------
        # CARREGA O HTML
        # -------------------------------------------------

        return render_template(
            "dashboard_adm.html",

            producao_hoje=producao_hoje,

            producao_mes=producao_mes,

            funcionarios_ativos=funcionarios_ativos,

            funcionarios_filtro=funcionarios_filtro,

            producao_funcionarios=producao_funcionarios,

            resumo_produtos=resumo_produtos,

            resumo_cores=resumo_cores,

            producao_filtrada=producao_filtrada,

            funcionarios_filtrados=funcionarios_filtrados,

            produtos_filtrados=produtos_filtrados,

            funcionario_id=funcionario_id,

            etapa=etapa,

            periodo=periodo,

            data_inicio=data_inicio_texto,

            data_fim=data_fim_texto
        )


    except Exception as erro:

        print(
            "Erro ao carregar Dashboard ADM:"
        )

        print(
            repr(erro)
        )

        return (
            "Erro ao carregar Dashboard ADM.",
            500
        )


    finally:

        if cursor:
            cursor.close()

        conn.close()

# =========================================================
# GERENCIAR FUNCIONÁRIOS
# =========================================================

@app.route("/funcionarios")
def funcionarios():

    conn = get_connection()

    if conn is None:
        return (
            "Não foi possível conectar ao banco.",
            500
        )

    cursor = None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nome,
                ativo

            FROM usuarios

            ORDER BY nome
            """
        )

        lista_funcionarios = cursor.fetchall()

        return render_template(
            "funcionarios.html",
            lista_funcionarios=lista_funcionarios
        )

    except Exception as erro:

        print(
            "Erro ao carregar funcionários:"
        )

        print(
            repr(erro)
        )

        return (
            "Erro ao carregar funcionários.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        conn.close()

# =========================================================
# ADICIONAR FUNCIONÁRIO
# =========================================================

@app.route("/funcionarios/adicionar", methods=["POST"])
def adicionar_funcionario():

    nome = request.form.get("nome", "").strip()
    usuario = request.form.get("usuario", "").strip()
    senha = request.form.get("senha", "").strip()

    # ---------------------------------------------------------
    # FUNÇÕES
    # ---------------------------------------------------------

    funcoes = request.form.getlist("funcoes")

    pode_corte = "cortar" in funcoes
    pode_costura = "costurar" in funcoes
    pode_colagem = "colagem" in funcoes

    # ---------------------------------------------------------
    # VALORES
    # ---------------------------------------------------------

    try:

        valorcorte = float(
            request.form.get("valor_corte") or 0
        )

        valorcostura = float(
            request.form.get("valor_costura") or 0
        )

        valorcolagem = float(
            request.form.get("valor_colagem") or 0
        )

    except ValueError:

        return redirect(
            url_for("funcionarios")
        )

    # ---------------------------------------------------------
    # VALIDAÇÃO
    # ---------------------------------------------------------

    if not nome or not usuario or not senha:

        return redirect(
            url_for("funcionarios")
        )

    # ---------------------------------------------------------
    # CONEXÃO
    # ---------------------------------------------------------

    conn = get_connection()

    if conn is None:

        return (
            "Não foi possível conectar ao banco.",
            500
        )

    cursor = None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO usuarios
                (
                    nome,
                    usuario,
                    senha_hash,
                    ativo,
                    pode_corte,
                    pode_costura,
                    pode_colagem,
                    valor_corte,
                    valor_costura,
                    valor_colagem
                )
            VALUES
                (
                    %s,
                    %s,
                    %s,
                    TRUE,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """,
            (
                nome,
                usuario,
                senha,
                pode_corte,
                pode_costura,
                pode_colagem,
                valorcorte,
                valorcostura,
                valorcolagem
            )
        )

        conn.commit()

        return redirect(
            url_for("funcionarios")
        )

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao adicionar funcionário:"
        )

        print(
            repr(erro)
        )

        return (
            "Erro ao adicionar funcionário.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        conn.close()
# =========================================================
# ATIVAR / DESATIVAR FUNCIONÁRIO
# =========================================================

@app.route(
    "/funcionarios/<int:funcionario_id>/status",
    methods=["POST"]
)
def alterar_status_funcionario(funcionario_id):

    conn = get_connection()

    if conn is None:
        return (
            "Não foi possível conectar ao banco.",
            500
        )

    cursor = None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE usuarios

            SET ativo = NOT ativo

            WHERE id = %s
            """,
            (funcionario_id,)
        )

        conn.commit()

        return redirect(
            url_for("funcionarios")
        )

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao alterar status do funcionário:"
        )

        print(
            repr(erro)
        )

        return (
            "Erro ao alterar status do funcionário.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        conn.close()
# =========================================================
# EDITAR FUNCIONÁRIO
# =========================================================

@app.route(
    "/funcionarios/<int:funcionario_id>/editar",
    methods=["POST"]
)
def editar_funcionario(funcionario_id):

    nome = request.form.get(
        "nome",
        ""
    ).strip()

    usuario = request.form.get(
        "usuario",
        ""
    ).strip()

    senha = request.form.get(
        "senha",
        ""
    ).strip()

    # ---------------------------------------------------------
    # FUNÇÕES
    # ---------------------------------------------------------

    funcoes = request.form.getlist("funcoes")

    pode_corte = "cortar" in funcoes
    pode_costura = "costurar" in funcoes
    pode_colagem = "colagem" in funcoes

    # ---------------------------------------------------------
    # VALORES
    # ---------------------------------------------------------

    try:

        valor_corte = float(
            request.form.get(
                "valor_corte"
            ) or 0
        )

        valor_costura = float(
            request.form.get(
                "valor_costura"
            ) or 0
        )

        valor_colagem = float(
            request.form.get(
                "valor_colagem"
            ) or 0
        )

    except ValueError:

        return redirect(
            url_for("funcionarios")
        )

    # ---------------------------------------------------------
    # VALIDAÇÃO
    # ---------------------------------------------------------

    if not nome or not usuario:

        return redirect(
            url_for("funcionarios")
        )

    # ---------------------------------------------------------
    # CONEXÃO
    # ---------------------------------------------------------

    conn = get_connection()

    if conn is None:

        return (
            "Não foi possível conectar ao banco.",
            500
        )

    cursor = None

    try:

        cursor = conn.cursor()

        # -----------------------------------------------------
        # COM SENHA NOVA
        # -----------------------------------------------------

        if senha:

            cursor.execute(
                """
                UPDATE usuarios

                SET
                    nome = %s,
                    usuario = %s,
                    senha_hash = %s,

                    pode_corte = %s,
                    pode_costura = %s,
                    pode_colagem = %s,

                    valor_corte = %s,
                    valor_costura = %s,
                    valor_colagem = %s

                WHERE id = %s
                """,
                (
                    nome,
                    usuario,
                    senha,

                    pode_corte,
                    pode_costura,
                    pode_colagem,

                    valor_corte,
                    valor_costura,
                    valor_colagem,

                    funcionario_id
                )
            )

        # -----------------------------------------------------
        # SEM ALTERAR SENHA
        # -----------------------------------------------------

        else:

            cursor.execute(
                """
                UPDATE usuarios

                SET
                    nome = %s,
                    usuario = %s,

                    pode_corte = %s,
                    pode_costura = %s,
                    pode_colagem = %s,

                    valor_corte = %s,
                    valor_costura = %s,
                    valor_colagem = %s

                WHERE id = %s
                """,
                (
                    nome,
                    usuario,

                    pode_corte,
                    pode_costura,
                    pode_colagem,

                    valor_corte,
                    valor_costura,
                    valor_colagem,

                    funcionario_id
                )
            )

        conn.commit()

        return redirect(
            url_for("funcionarios")
        )

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao editar funcionário:"
        )

        print(
            repr(erro)
        )

        return (
            "Erro ao editar funcionário.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        conn.close()

# =========================================================
# BUSCAR FUNCIONÁRIO PARA EDIÇÃO
# =========================================================

@app.route(
    "/api/funcionarios/<int:funcionario_id>",
    methods=["GET"]
)
def buscar_funcionario(funcionario_id):

    conn = get_connection()

    if conn is None:

        return jsonify({
            "erro": "Não foi possível conectar ao banco."
        }), 500

    cursor = None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nome,
                usuario,
                pode_corte,
                pode_costura,
                pode_colagem,
                valor_corte,
                valor_costura,
                valor_colagem
            FROM usuarios
            WHERE id = %s
            """,
            (
                funcionario_id,
            )
        )

        funcionario = cursor.fetchone()

        if not funcionario:

            return jsonify({
                "erro": "Funcionário não encontrado."
            }), 404

        return jsonify({

            "id": funcionario[0],

            "nome": funcionario[1],

            "usuario": funcionario[2],

            "pode_corte": bool(
                funcionario[3]
            ),

            "pode_costura": bool(
                funcionario[4]
            ),

            "pode_colagem": bool(
                funcionario[5]
            ),

            "valor_corte": float(
                funcionario[6] or 0
            ),

            "valor_costura": float(
                funcionario[7] or 0
            ),

            "valor_colagem": float(
                funcionario[8] or 0
            )
        })

    except Exception as erro:

        print(
            "Erro ao buscar funcionário:"
        )

        print(
            repr(erro)
        )

        return jsonify({
            "erro": "Erro ao buscar funcionário."
        }), 500

    finally:

        if cursor:
            cursor.close()

        conn.close()





# =========================================================
# EXCLUIR FUNCIONÁRIO
# =========================================================

@app.route(
    "/funcionarios/<int:funcionario_id>/excluir",
    methods=["POST"]
)
def excluir_funcionario(funcionario_id):

    conn = get_connection()

    if conn is None:
        return (
            "Não foi possível conectar ao banco.",
            500
        )

    cursor = None

    try:

        cursor = conn.cursor()

        # EXCLUI AS PRODUÇÕES DO FUNCIONÁRIO

        cursor.execute(
            """
            DELETE FROM producoes
            WHERE usuario_id = %s
            """,
            (funcionario_id,)
        )

        # EXCLUI O FUNCIONÁRIO

        cursor.execute(
            """
            DELETE FROM usuarios
            WHERE id = %s
            """,
            (funcionario_id,)
        )

        conn.commit()

        return redirect(
            url_for("funcionarios")
        )

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao excluir funcionário:"
        )

        print(
            repr(erro)
        )

        return (
            "Erro ao excluir funcionário.",
            500
        )

    finally:

        if cursor:
            cursor.close()

        conn.close()

# =========================================================
# INÍCIO DO FUNCIONÁRIO
# =========================================================

@app.route("/inicio")
def inicio_funcionario():

    # -----------------------------------------------------
    # TEMPORÁRIO
    # Depois virá da sessão de login
    # -----------------------------------------------------

    usuario_id = session.get(
        "usuario_id",
        1
    )


    conn = get_connection()

    if conn is None:

        return (
            "Não foi possível conectar ao banco.",
            500
        )

    cursor = None

    try:

        cursor = conn.cursor()


        # -------------------------------------------------
        # PRODUÇÃO DE HOJE
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COALESCE(
                SUM(
                    COALESCE(quantidade_p, 0) +
                    COALESCE(quantidade_m, 0) +
                    COALESCE(quantidade_g, 0) +
                    COALESCE(quantidade_gg, 0) +
                    COALESCE(quantidade_xg, 0)
                ),
                0
            )

            FROM producoes

            WHERE usuario_id = %s

            AND data_producao = CURRENT_DATE
            """,
            (usuario_id,)
        )

        producao_hoje = cursor.fetchone()[0]


        # -------------------------------------------------
        # PRODUÇÃO DO MÊS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COALESCE(
                SUM(
                    COALESCE(quantidade_p, 0) +
                    COALESCE(quantidade_m, 0) +
                    COALESCE(quantidade_g, 0) +
                    COALESCE(quantidade_gg, 0) +
                    COALESCE(quantidade_xg, 0)
                ),
                0
            )

            FROM producoes

            WHERE usuario_id = %s

            AND DATE_TRUNC(
                'month',
                data_producao
            )
            =
            DATE_TRUNC(
                'month',
                CURRENT_DATE
            )
            """,
            (usuario_id,)
        )

        producao_mes = cursor.fetchone()[0]


        # -------------------------------------------------
        # ÚLTIMOS RELATÓRIOS
        # -------------------------------------------------

        cursor.execute(
            """
           SELECT
            relatorio_id,
            MAX(data_producao) AS data_producao,
            MAX(produto) AS produto,
            MAX(etapa) AS etapa,
            MAX(observacao) AS observacao,

            SUM(
                COALESCE(quantidade_p, 0) +
                COALESCE(quantidade_m, 0) +
                COALESCE(quantidade_g, 0) +
                COALESCE(quantidade_gg, 0) +
                COALESCE(quantidade_xg, 0)
            ) AS quantidade

        FROM producoes

        WHERE usuario_id = %s

        GROUP BY relatorio_id

        ORDER BY data_producao DESC

        LIMIT 5
            """,
            (usuario_id,)
        )

        ultimos_registros = cursor.fetchall()
        print(ultimos_registros)

        return render_template(
            "inicio_funcionario.html",

            producao_hoje=producao_hoje,

            producao_mes=producao_mes,

            ultimos_registros=ultimos_registros

            
        )


    except Exception as erro:

        print(
            "Erro ao carregar dashboard:"
        )

        print(repr(erro))

        return (
            "Erro ao carregar dashboard.",
            500
        )


    finally:

        if cursor:
            cursor.close()

        conn.close()


# =========================================================
# Detalhes relatorio
# =========================================================
@app.route("/api/producoes/relatorio/<relatorio_id>")
def detalhes_relatorio(relatorio_id):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                relatorio_id,
                data_producao,
                etapa,
                produto,
                cor,
                genero,
                quantidade_p,
                quantidade_m,
                quantidade_g,
                quantidade_gg,
                quantidade_xg,
                observacao
            FROM producoes
            WHERE relatorio_id = %s
            ORDER BY
                CASE
                    WHEN genero = 'Masculino' THEN 1
                    WHEN genero = 'Feminino' THEN 2
                    ELSE 3
                END
        """, (relatorio_id,))

        registros = cursor.fetchall()

        if not registros:
            return jsonify({
                "erro": "Relatório não encontrado."
            }), 404

        dados = []

        total_geral = 0

        for registro in registros:

            (
                relatorio_id,
                data_producao,
                etapa,
                produto,
                cor,
                genero,
                quantidade_p,
                quantidade_m,
                quantidade_g,
                quantidade_gg,
                quantidade_xg,
                observacao
            ) = registro

            quantidade_p = quantidade_p or 0
            quantidade_m = quantidade_m or 0
            quantidade_g = quantidade_g or 0
            quantidade_gg = quantidade_gg or 0
            quantidade_xg = quantidade_xg or 0

            total_genero = (
                quantidade_p +
                quantidade_m +
                quantidade_g +
                quantidade_gg +
                quantidade_xg
            )

            total_geral += total_genero

            dados.append({
                "genero": genero,
                "cor": cor,
                "quantidades": {
                    "P": quantidade_p,
                    "M": quantidade_m,
                    "G": quantidade_g,
                    "GG": quantidade_gg,
                    "XG": quantidade_xg
                },
                "total": total_genero
            })

        return jsonify({
            "relatorio_id": str(relatorio_id),
            "data": registros[0][1].strftime("%d/%m/%Y"),
            "etapa": registros[0][2],
            "produto": registros[0][3],
            "observacao": registros[0][11],
            "total_geral": total_geral,
            "generos": dados
        })

    except Exception as e:

        print("Erro ao buscar detalhes:", e)

        return jsonify({
            "erro": "Erro ao buscar detalhes do relatório."
        }), 500

    finally:
        conn.close()

# =========================================================
# RELATÓRIOS POR FUNCIONÁRIO
# =========================================================

@app.route("/api/funcionarios/<int:usuario_id>/relatorios")
def relatorios_funcionario(usuario_id):

    # -------------------------------------------------
    # FILTRO POR PERÍODO
    # -------------------------------------------------

    periodo = request.args.get(
        "periodo",
        ""
    )

    etapa = request.args.get(
        "etapa",
        ""
    )

    data_inicio_texto = request.args.get(
        "data_inicio",
        ""
    )

    data_fim_texto = request.args.get(
        "data_fim",
        ""
    )

    hoje = date.today()

    data_inicio = None
    data_fim = None


    if periodo == "hoje":

        data_inicio = hoje
        data_fim = hoje


    elif periodo == "semana":

        data_inicio = hoje - timedelta(
            days=hoje.weekday()
        )

        data_fim = hoje


    elif periodo == "mes":

        data_inicio = hoje.replace(
            day=1
        )

        data_fim = hoje


    elif periodo == "personalizado":

        try:

            if data_inicio_texto:
                data_inicio = date.fromisoformat(
                    data_inicio_texto
                )

            if data_fim_texto:
                data_fim = date.fromisoformat(
                    data_fim_texto
                )

        except ValueError:

            data_inicio = None
            data_fim = None


    # -------------------------------------------------
    # CONEXÃO
    # -------------------------------------------------

    conn = get_connection()

    if conn is None:

        return jsonify({
            "erro": "Não foi possível conectar ao banco."
        }), 500


    cursor = None


    try:

        cursor = conn.cursor()


        # -------------------------------------------------
        # MONTA O FILTRO DE DATA
        # -------------------------------------------------

        condicao_data = ""
        condicao_etapa = ""

        parametros = [
            usuario_id
        ]


        if data_inicio is not None:

            condicao_data += """
                AND data_producao >= %s
            """

            parametros.append(
                data_inicio
            )


        if data_fim is not None:

            condicao_data += """
                AND data_producao <= %s
            """

            parametros.append(
                data_fim
            )

        if etapa:

            condicao_etapa = """
                AND etapa = %s
            """

            parametros.append(
                etapa
            )


        # -------------------------------------------------
        # BUSCA OS RELATÓRIOS
        # -------------------------------------------------

        query = f"""
            SELECT
                relatorio_id,
                MAX(data_producao) AS data_producao,
                MAX(produto) AS produto,
                MAX(etapa) AS etapa,

                SUM(
                    COALESCE(quantidade_p, 0) +
                    COALESCE(quantidade_m, 0) +
                    COALESCE(quantidade_g, 0) +
                    COALESCE(quantidade_gg, 0) +
                    COALESCE(quantidade_xg, 0)
                ) AS quantidade

            FROM producoes

            WHERE usuario_id = %s

            {condicao_data}

            {condicao_etapa}

            GROUP BY relatorio_id

            ORDER BY data_producao DESC
        """


        cursor.execute(
            query,
            parametros
        )


        registros = cursor.fetchall()

        relatorios = []


        for registro in registros:

            relatorios.append({
                "relatorio_id": str(registro[0]),
                "data": registro[1].strftime("%d/%m/%Y"),
                "produto": registro[2],
                "etapa": registro[3],
                "quantidade": registro[4]
            })


        return jsonify(
            relatorios
        )


    except Exception as erro:

        print(
            "Erro ao buscar relatórios do funcionário:"
        )

        print(
            repr(erro)
        )

        return jsonify({
            "erro":
            "Não foi possível buscar os relatórios."
        }), 500


    finally:

        if cursor:
            cursor.close()

        conn.close()

# =========================================================
# TELA DE PRODUÇÃO
# =========================================================

@app.route("/producao")
def producao():

    return render_template(
        "producao.html"
    )


# =========================================================
# API - REGISTRAR PRODUÇÃO
# =========================================================

@app.route(
    "/api/producoes",
    methods=["POST"]
)
def api_producoes():

    # -----------------------------------------------------
    # RECEBE JSON
    # -----------------------------------------------------

    dados = request.get_json()

    if not dados:

        return jsonify({
            "erro": "Nenhum dado recebido."
        }), 400


    # -----------------------------------------------------
    # DADOS PRINCIPAIS
    # -----------------------------------------------------

    data_producao = dados.get(
        "data_producao"
    )

    etapa = dados.get(
        "etapa"
    )

    produto = dados.get(
        "produto"
    )

    observacao = dados.get(
        "observacao",
        ""
    )

    itens = dados.get(
        "itens",
        []
    )


    # -----------------------------------------------------
    # VALIDAÇÕES
    # -----------------------------------------------------

    if not data_producao:

        return jsonify({
            "erro": "Informe a data da produção."
        }), 400


    if not etapa:

        return jsonify({
            "erro": "Informe a etapa."
        }), 400


    if etapa not in [
        "Corte",
        "Costura",
        "Colagem"
    ]:

        return jsonify({
            "erro": "Etapa inválida."
        }), 400


    if not produto:

        return jsonify({
            "erro": "Informe o modelo do produto."
        }), 400



    if not itens:

        return jsonify({
            "erro": "Adicione pelo menos um item."
        }), 400


    # -----------------------------------------------------
    # USUÁRIO
    # -----------------------------------------------------

    usuario_id = session.get(
        "usuario_id",
        1
    )


    # -----------------------------------------------------
    # ID DO RELATÓRIO
    # -----------------------------------------------------

    relatorio_id = str(
        uuid.uuid4()
    )


    # -----------------------------------------------------
    # ESTRUTURA DOS ITENS
    # -----------------------------------------------------

    tamanhos_validos = [
        "P",
        "M",
        "G",
        "GG",
        "XG"
    ]

    generos_validos = [
        "Masculino",
        "Feminino"
    ]

    # Aqui serão agrupadas as peças por gênero + cor.
    #
    # Exemplo:
    #
    # ("Masculino", "Preto")
    # P = 5
    # M = 3
    #
    # ("Feminino", "Marrom")
    # G = 4

    grupos = {}


    # -----------------------------------------------------
    # PROCESSA OS ITENS
    # -----------------------------------------------------

    try:

        for item in itens:

            genero = item.get(
                "genero"
            )

            tamanho = item.get(
                "tamanho"
            )

            cor = item.get(
                "cor"
            )

            quantidade = int(
                item.get(
                    "quantidade",
                    0
                )
            )


            # ---------------------------------------------
            # VALIDA GÊNERO
            # ---------------------------------------------

            if genero not in generos_validos:

                return jsonify({
                    "erro": "Gênero inválido."
                }), 400


            # ---------------------------------------------
            # VALIDA TAMANHO
            # ---------------------------------------------

            if tamanho not in tamanhos_validos:

                return jsonify({
                    "erro": "Tamanho inválido."
                }), 400


            # ---------------------------------------------
            # VALIDA COR
            # ---------------------------------------------

            if not cor:

                return jsonify({
                    "erro": "Cor inválida."
                }), 400


            # ---------------------------------------------
            # VALIDA QUANTIDADE
            # ---------------------------------------------

            if quantidade <= 0:

                return jsonify({
                    "erro":
                    "A quantidade deve ser maior que zero."
                }), 400


            # ---------------------------------------------
            # CRIA O GRUPO GÊNERO + COR
            # ---------------------------------------------

            chave = (
                genero,
                cor
            )

            if chave not in grupos:

                grupos[chave] = {
                    "P": 0,
                    "M": 0,
                    "G": 0,
                    "GG": 0,
                    "XG": 0
                }


            # ---------------------------------------------
            # SOMA A QUANTIDADE AO TAMANHO
            # ---------------------------------------------

            grupos[chave][tamanho] += quantidade


    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "erro": "Quantidade inválida."
        }), 400


    # -----------------------------------------------------
    # CONEXÃO
    # -----------------------------------------------------

    conn = get_connection()

    if conn is None:

        return jsonify({
            "erro":
            "Não foi possível conectar ao banco."
        }), 500


    cursor = None


    try:

        cursor = conn.cursor()


        # -------------------------------------------------
        # QUERY
        # -------------------------------------------------

        query = """

            INSERT INTO producoes
            (
                relatorio_id,
                usuario_id,
                data_producao,
                etapa,
                produto,
                cor,
                observacao,
                genero,
                quantidade_p,
                quantidade_m,
                quantidade_g,
                quantidade_gg,
                quantidade_xg
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )

        """


               # -------------------------------------------------
        # SALVA CADA GRUPO GÊNERO + COR
        # -------------------------------------------------

        for chave, quantidades in grupos.items():

            genero, cor = chave

            cursor.execute(
                query,
                (
                    relatorio_id,
                    usuario_id,
                    data_producao,
                    etapa,
                    produto,
                    cor,
                    observacao,
                    genero,
                    quantidades["P"],
                    quantidades["M"],
                    quantidades["G"],
                    quantidades["GG"],
                    quantidades["XG"]
                )
            )


        # -------------------------------------------------
        # CONFIRMA
        # -------------------------------------------------

        conn.commit()


        print(
            "Relatório de produção registrado!"
        )

        print(
            "ID:",
            relatorio_id
        )


        return jsonify({

            "sucesso": True,

            "mensagem":
            "Produção enviada com sucesso!",

            "relatorio_id":
            relatorio_id

        })


    except Exception as erro:

        conn.rollback()


        print(
            "Erro ao registrar produção:"
        )

        print(
            repr(erro)
        )


        return jsonify({

            "erro":
            "Não foi possível registrar a produção."

        }), 500


    finally:

        if cursor:

            cursor.close()

        conn.close()


# =========================================================
# INICIALIZAÇÃO
# =========================================================

if __name__ == "__main__":

    # -----------------------------------------------------
    # TESTE DE CONEXÃO
    # -----------------------------------------------------

    conn = get_connection()

    if conn:

        conn.close()

        print(
            "Teste de conexão concluído."
        )


    app.debug = True

