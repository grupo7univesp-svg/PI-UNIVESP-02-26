from flask import Flask, render_template
import psycopg2
app = Flask(__name__)

@app.route("/")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)

def get_connection():
    

    print ( "Entrou na função")
    try:
        return psycopg2.connect(
            host="db.ytfbetitkfnxgvxcfoew.supabase.co",
            database= "postgres",
            user= "postgres",
            password= "Univesp@201",
            port= 5432
             )
        print("conectado ao banco de dados")
        
    except Exception as erro:
        print("Erro na conexão.")
        print(repr(erro))
        return None


conn = get_connection()