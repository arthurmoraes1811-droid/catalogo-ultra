from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = '123456'

UPLOAD_FOLDER = 'static/imagens'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Criar banco
def init_db():

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            nome TEXT,
            descricao TEXT,
            categoria TEXT,
            imagem TEXT

        )
    ''')

    conn.commit()
    conn.close()

init_db()

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        usuario = request.form['usuario']
        senha = request.form['senha']

        if usuario == 'admin' and senha == '123':

            session['usuario'] = usuario

            return redirect('/')

    return render_template('login.html')

# LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# Página inicial
@app.route('/')
def index():

    if 'usuario' not in session:
        return redirect('/login')

    busca = request.args.get('busca')
    categoria = request.args.get('categoria')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    query = "SELECT * FROM produtos WHERE 1=1"
    valores = []

    if busca:

        query += " AND (nome LIKE ? OR codigo LIKE ?)"

        valores.append('%' + busca + '%')
        valores.append('%' + busca + '%')

    if categoria:

        query += " AND categoria = ?"

        valores.append(categoria)

    cursor.execute(query, valores)

    produtos = cursor.fetchall()

    conn.close()

    return render_template(
        'index.html',
        produtos=produtos
    )

# Cadastrar produto
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():

    if 'usuario' not in session:
        return redirect('/login')

    if request.method == 'POST':

        codigo = request.form['codigo']
        nome = request.form['nome']
        descricao = request.form['descricao']
        categoria = request.form['categoria']

        imagem = request.files['imagem']

        nome_arquivo = secure_filename(imagem.filename)

        caminho = os.path.join(
            app.config['UPLOAD_FOLDER'],
            nome_arquivo
        )

        imagem.save(caminho)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO produtos
            (codigo, nome, descricao,
             categoria, imagem)

            VALUES (?, ?, ?, ?, ?)
        """, (
            codigo,
            nome,
            descricao,
            categoria,
            nome_arquivo
        ))

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('cadastrar.html')

# Editar produto
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):

    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':

        codigo = request.form['codigo']
        nome = request.form['nome']
        descricao = request.form['descricao']
        categoria = request.form['categoria']

        cursor.execute("""
            UPDATE produtos

            SET
                codigo = ?,
                nome = ?,
                descricao = ?,
                categoria = ?

            WHERE id = ?
        """, (
            codigo,
            nome,
            descricao,
            categoria,
            id
        ))

        conn.commit()
        conn.close()

        return redirect('/')

    cursor.execute(
        "SELECT * FROM produtos WHERE id = ?",
        (id,)
    )

    produto = cursor.fetchone()

    conn.close()

    return render_template(
        'editar.html',
        produto=produto
    )

# Deletar produto
@app.route('/deletar/<int:id>')
def deletar(id):

    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Buscar imagem
    cursor.execute(
        "SELECT imagem FROM produtos WHERE id = ?",
        (id,)
    )

    produto = cursor.fetchone()

    # Apagar imagem da pasta
    if produto:

        caminho_imagem = os.path.join(
            app.config['UPLOAD_FOLDER'],
            produto[0]
        )

        if os.path.exists(caminho_imagem):
            os.remove(caminho_imagem)

    # Apagar produto do banco
    cursor.execute(
        "DELETE FROM produtos WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)