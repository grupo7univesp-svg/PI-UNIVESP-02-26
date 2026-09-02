from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from livereload import Server
import psycopg2
import os
import uuid


app = Flask(__name__)
app.secret_key = os.getenv( "FLASK_SECRET_KEY", "chave-temporaria-do-projeto" ) 
# ========================================================= # CONEXÃO COM O BANCO # =========================================================
def get_connection():
  print("Entrou na função de conexão") 
  try:
   conn = psycopg2.connect( host="aws-0-sa-east-1.pooler.supabase.com", database="postgres", user="postgres.ytfbetitkfnxgvxcfoew", password="Univesp@201", port=5432, sslmode="require" ) 
   print("Conectado ao banco de dados!")
   return conn

  except Exception as erro:

        print("Erro na conexão:")
        print(repr(erro))

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
        # PRODUÇÃO POR FUNCIONÁRIO
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
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

            WHERE usuarios.ativo = TRUE

            GROUP BY
                usuarios.id,
                usuarios.nome

            ORDER BY
                usuarios.nome
            """
        )

        producao_funcionarios = cursor.fetchall()


        return render_template(
            "dashboard_adm.html",

            producao_hoje=producao_hoje,

            producao_mes=producao_mes,

            funcionarios_ativos=funcionarios_ativos,

            producao_funcionarios=producao_funcionarios
        )


    except Exception as erro:

        print(
            "Erro ao carregar Dashboard ADM:"
        )

        print(repr(erro))

        return (
            "Erro ao carregar Dashboard ADM.",
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
                data_producao,
                produto,
                etapa,
                observacao,
                quantidade

            FROM
            (
                SELECT DISTINCT ON (relatorio_id)

                    relatorio_id,

                    data_producao,

                    produto,

                    etapa,

                    observacao,

                    (
                        COALESCE(quantidade_p, 0) +
                        COALESCE(quantidade_m, 0) +
                        COALESCE(quantidade_g, 0) +
                        COALESCE(quantidade_gg, 0) +
                        COALESCE(quantidade_xg, 0)
                    ) AS quantidade

                FROM producoes

                WHERE usuario_id = %s

                ORDER BY
                    relatorio_id,
                    data_producao DESC

            ) AS relatorios

            ORDER BY
                data_producao DESC

            LIMIT 5
            """,
            (usuario_id,)
        )

        ultimos_registros = cursor.fetchall()


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
    # ESTRUTURA DE TAMANHOS
    # -----------------------------------------------------

    masculino = {

        "P": 0,
        "M": 0,
        "G": 0,
        "GG": 0,
        "XG": 0
    }


    feminino = {

        "P": 0,
        "M": 0,
        "G": 0,
        "GG": 0,
        "XG": 0
    }


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
            # VALIDA QUANTIDADE
            # ---------------------------------------------

            if quantidade <= 0:

                return jsonify({
                    "erro":
                    "A quantidade deve ser maior que zero."
                }), 400


            # ---------------------------------------------
            # SOMA
            # ---------------------------------------------

            if genero == "Masculino":

                masculino[tamanho] += quantidade

            else:

                feminino[tamanho] += quantidade


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
        # MASCULINO
        # -------------------------------------------------

        cursor.execute(
            query,

            (
                relatorio_id,

                usuario_id,

                data_producao,

                etapa,

                produto,


                observacao,

                "Masculino",

                masculino["P"],

                masculino["M"],

                masculino["G"],

                masculino["GG"],

                masculino["XG"]
            )
        )


        # -------------------------------------------------
        # FEMININO
        # -------------------------------------------------

        cursor.execute(
            query,

            (
                relatorio_id,

                usuario_id,

                data_producao,

                etapa,

                produto,


                observacao,

                "Feminino",

                feminino["P"],

                feminino["M"],

                feminino["G"],

                feminino["GG"],

                feminino["XG"]
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


    # -----------------------------------------------------
    # LIVEReload
    # -----------------------------------------------------

    server = Server(
        app.wsgi_app
    )


    server.watch(
        "templates/"
    )

    server.watch(
        "static/"
    )


    server.serve(
        port=5000
    )