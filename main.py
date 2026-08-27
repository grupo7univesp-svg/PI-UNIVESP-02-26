from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)


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
            url_for("producao")
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

    app.run(debug=True)