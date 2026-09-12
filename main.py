from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from livereload import Server
import psycopg2
from psycopg2 import OperationalError
import os
import uuid
from datetime import date, timedelta


app = Flask(__name__)
app.secret_key = os.getenv( "FLASK_SECRET_KEY", "chave-temporaria-do-projeto" ) 
# ========================================================= # CONEXÃO COM O BANCO # =========================================================
def get_connection():
    """Abre uma nova conexão PostgreSQL usando variáveis de ambiente."""
    database_url = os.getenv("DATABASE_URL")
    try:
        if database_url:
            return psycopg2.connect(database_url)

        return psycopg2.connect( host="aws-0-sa-east-1.pooler.supabase.com", database="postgres", user="postgres.ytfbetitkfnxgvxcfoew", password="Univesp@201", port=5432, sslmode="require" ) 
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
        # FILTRO DA PRODUÇÃO POR FUNCIONÁRIO
        # -------------------------------------------------

        condicao_data = ""
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

            WHERE usuarios.ativo = TRUE

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
        # CARREGA O HTML
        # -------------------------------------------------

        return render_template(
            "dashboard_adm.html",

            producao_hoje=producao_hoje,

            producao_mes=producao_mes,

            funcionarios_ativos=funcionarios_ativos,

            producao_funcionarios=producao_funcionarios,

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