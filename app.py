from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

import sqlite3

conexao = sqlite3.connect("database.db")
cursor = conexao.cursor()

app = Flask(__name__)

app.secret_key = '123456'

UPLOAD_FOLDER = 'static/imagens'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/favoritos")
def favoritos():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT produtos.* FROM produtos INNER JOIN favoritos ON produtos.id = favoritos.produto_id "
    )

    produtos = cursor.fetchall()

    conn.close()

    return render_template(
        "favoritos.html",
        produtos=produtos
    )

@app.route("/favoritar/<int:id>")
def favoritar(id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # verifica se já existe nos favoritos
    cursor.execute(
        "SELECT * FROM favoritos WHERE produto_id=?",
        (id,)
    )

    favorito = cursor.fetchone()

    # se já existe, remove
    if favorito:

        cursor.execute(
            "DELETE FROM favoritos WHERE produto_id=?",
            (id,)
        )

    # se não existe, adiciona
    else:

        cursor.execute(
            "INSERT INTO favoritos (produto_id) VALUES (?)",
            (id,)
        )

    conn.commit()
    conn.close()

    return redirect("/")

# CRIAR BANCO

def init_db():

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # TABELA PRODUTOS

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

    # TABELA FAVORITOS

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favoritos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER

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

            flash('Login realizado com sucesso!')

            return redirect('/')

    return render_template('login.html')

# LOGOUT

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# PÁGINA INICIAL

@app.route('/')
def index():

    if 'usuario' not in session:
        return redirect('/login')

    busca = request.args.get('busca')
    categoria = request.args.get('categoria')

    pagina = request.args.get(
        'pagina',
        1,
        type=int
    )

    por_pagina = 6

    offset = (pagina - 1) * por_pagina

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    query = """
    SELECT produtos.*,

    CASE
    WHEN favoritos.produto_id IS NOT NULL
    THEN 1
    ELSE 0
    END as favorito

    FROM produtos

    LEFT JOIN favoritos
    ON produtos.id = favoritos.produto_id

    WHERE 1=1
    """

    valores = []

    if busca:

        query += " AND (nome LIKE ? OR codigo LIKE ?)"

        valores.append('%' + busca + '%')
        valores.append('%' + busca + '%')

    if categoria:

        query += " AND categoria = ?"

        valores.append(categoria)

    # CONTAR PRODUTOS

    cursor.execute(query, valores)

    total_produtos = len(cursor.fetchall())

    # PAGINAÇÃO

    query += " LIMIT ? OFFSET ?"

    valores.append(por_pagina)
    valores.append(offset)

    cursor.execute(query, valores)

    produtos = cursor.fetchall()

    total_paginas = (
        total_produtos + por_pagina - 1
    ) // por_pagina

    conn.close()

    return render_template(
        'index.html',
        produtos=produtos,
        pagina=pagina,
        total_paginas=total_paginas
    )

# VISUALIZAR PRODUTO

@app.route('/produto/<int:id>')
def produto(id):

    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM produtos WHERE id = ?",
        (id,)
    )

    produto = cursor.fetchone()

    conn.close()

    return render_template(
        'produto.html',
        produto=produto
    )
    # REMOVE OU ADICIONA

    if favorito:

        cursor.execute(
            "DELETE FROM favoritos WHERE produto_id = ?",
            (id,)
        )

        flash('Produto removido dos favoritos!')

    else:

        cursor.execute(
            "INSERT INTO favoritos (produto_id) VALUES (?)",
            (id,)
        )

        flash('Produto favoritado!')

    conn.commit()
    conn.close()

    return redirect('/')

# CADASTRAR PRODUTO

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

        flash('Produto cadastrado com sucesso!')

        return redirect('/')

    return render_template('cadastrar.html')

# EDITAR PRODUTO

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

        flash('Produto editado com sucesso!')

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

# DELETAR PRODUTO

@app.route('/deletar/<int:id>')
def deletar(id):

    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # BUSCAR IMAGEM

    cursor.execute(
        "SELECT imagem FROM produtos WHERE id = ?",
        (id,)
    )

    produto = cursor.fetchone()

    # APAGAR IMAGEM

    if produto:

        caminho_imagem = os.path.join(
            app.config['UPLOAD_FOLDER'],
            produto[0]
        )

        if os.path.exists(caminho_imagem):

            os.remove(caminho_imagem)

    # APAGAR FAVORITO

    cursor.execute(
        "DELETE FROM favoritos WHERE produto_id = ?",
        (id,)
    )

    # APAGAR PRODUTO

    cursor.execute(
        "DELETE FROM produtos WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash('Produto deletado com sucesso!')

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
