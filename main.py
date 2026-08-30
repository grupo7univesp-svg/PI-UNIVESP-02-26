from flask import Flask, render_template, request, redirect, url_for, session
from livereload import Server
import psycopg2

app = Flask(__name__)
app.secret_key = "chave-temporaria-do-projeto"

def get_connection():
    print("Entrou na função")

    try:
        conn = psycopg2.connect(
            host="aws-0-sa-east-1.pooler.supabase.com",
            database="postgres",
            user="postgres.ytfbetitkfnxgvxcfoew",
            password="Univesp@201",
            port=5432,
            sslmode="require"
        )

        print("Conectado ao banco de dados!")
        return conn

    except Exception as erro:
        print("Erro na conexão:")
        print(repr(erro))
        return None


@app.route("/")
def login():
    return render_template("login.html")

@app.route("/entrar", methods=["POST"])
def entrar():

    tipo_usuario = request.form.get("tipo_usuario")

    if tipo_usuario == "adm":
        return redirect(url_for("dashboard_adm"))

    elif tipo_usuario == "funcionario":
        return redirect(url_for("inicio_funcionario"))

    return redirect(url_for("login"))

@app.route("/dashboard-adm")
def dashboard_adm():
    return render_template("dashboard_adm.html")

@app.route("/inicio")
def inicio_funcionario():

    usuario_id = 1

    conn = get_connection()

    if conn is None:
        return "Não foi possível conectar ao banco.", 500

    try:
        cursor = conn.cursor()

        # Produção de hoje
        cursor.execute(
            """
            SELECT COALESCE(SUM(quantidade), 0)
            FROM producoes
            WHERE usuario_id = %s
            AND data_producao = CURRENT_DATE
            """,
            (usuario_id,)
        )

        producao_hoje = cursor.fetchone()[0]


        # Produção do mês
        cursor.execute(
            """
            SELECT COALESCE(SUM(quantidade), 0)
            FROM producoes
            WHERE usuario_id = %s
            AND DATE_TRUNC('month', data_producao) =
                DATE_TRUNC('month', CURRENT_DATE)
            """,
            (usuario_id,)
        )

        producao_mes = cursor.fetchone()[0]


        # Últimos 5 registros
        cursor.execute(
            """
            SELECT
                data_producao,
                produto,
                etapa,
                quantidade
            FROM producoes
            WHERE usuario_id = %s
            ORDER BY data_producao DESC
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

        print("Erro ao carregar dashboard:")
        print(repr(erro))

        return "Erro ao carregar dashboard.", 500


    finally:

        cursor.close()
        conn.close()

@app.route("/producao")
def producao():

    return render_template("producao.html")


@app.route("/registrar-producao", methods=["POST"])
def registrar_producao():

    # Recebe os dados do formulário

    data_producao = request.form.get("data_producao")
    etapa = request.form.get("etapa")
    produto = request.form.get("produto")
    genero = request.form.get("genero")
    tamanho = request.form.get("tamanho")
    cor = request.form.get("cor")
    quantidade = request.form.get("quantidade")
    observacao = request.form.get("observacao")


    # Por enquanto vamos usar o usuário 1
    # Depois substituiremos pelo usuário da sessão

    usuario_id = 1


    # Converte quantidade para inteiro

    try:
        quantidade = int(quantidade)

    except (TypeError, ValueError):

        return "Quantidade inválida", 400


    conn = get_connection()


    if conn is None:

        return "Não foi possível conectar ao banco.", 500


    try:

        cursor = conn.cursor()


        query = """
            INSERT INTO producoes
            (
                usuario_id,
                produto,
                genero,
                tamanho,
                cor,
                etapa,
                quantidade,
                data_producao,
                observacao
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
                %s
            )
        """


        cursor.execute(
            query,
            (
                usuario_id,
                produto,
                genero,
                tamanho,
                cor,
                etapa,
                quantidade,
                data_producao,
                observacao
            )
        )


        conn.commit()


        print("Produção registrada com sucesso!")


        return redirect(
    url_for("inicio_funcionario")
        )


    except Exception as erro:

        conn.rollback()

        print("Erro ao registrar produção:")
        print(repr(erro))

        return "Erro ao registrar produção.", 500


    finally:

        cursor.close()

        conn.close()












if __name__ == "__main__":
    conn = get_connection()

    if conn:
        conn.close()

    app.debug = True

    server = Server(app.wsgi_app)

    server.watch("templates/")
    server.watch("static/")

    server.serve(port=5000)