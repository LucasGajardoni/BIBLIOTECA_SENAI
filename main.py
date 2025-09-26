from flask import Flask, render_template, request, flash, redirect, url_for, session, send_from_directory
from flask_bcrypt import generate_password_hash, check_password_hash
import fdb


app = Flask(__name__)

host = 'localhost'
database = r'C:\Users\Aluno\Desktop\BANCO.FDB'
user = 'sysdba'
password = 'sysdba'

app.secret_key = 'qualquercoisa'

con = fdb.connect(host=host, database=database, user=user, password=password)

@app.route('/')
def home():
    return render_template('home.html', titulo = "home")


@app.route("/logout")
def logout():
    if "id_usuario" not in session:
        flash("voce precisa estar logado")
        return redirect(url_for('nlogin'))
    session.pop("id_usuario", None)
    return redirect(url_for('home'))


@app.route('/livro')
def index():
    cursor = con.cursor()
    cursor.execute("SELECT ID_LIVRO, TITULO, AUTOR, ANO_PUBLICACAO FROM LIVROS")
    livros = cursor.fetchall()
    cursor.execute("SELECT ID_USUARIO, NOME, EMAIL, SENHA FROM USUARIOS")
    usuarios = cursor.fetchall()
    cursor.close()

    return render_template('livros.html',livros=livros, usuarios=usuarios)

@app.route('/cadastro')
def cadastro():
    cursor = con.cursor()
    cursor.execute("SELECT ID_USUARIO, NOME, EMAIL, SENHA FROM USUARIOS")
    usuarios = cursor.fetchall()
    cursor.close()

    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/novo')
def novo():
    return render_template('novo.html', titulo = "Novo Livro")


@app.route('/nlogin')
def nlogin():
    return render_template('login.html', titulo = "Novo usuario")

@app.route('/login', methods=["POST"])
def login():
    email = request.form['email'].strip().lower()
    senha = request.form['senha'].strip()

    print(f"Email {email}")
    print(f"Senha {senha}")

    cursor = con.cursor()
    cursor.execute(
        'SELECT ID_USUARIO, NOME, EMAIL, SENHA FROM USUARIOS WHERE LOWER(EMAIL) = ?',
        (email,)
    )
    usuario = cursor.fetchone()
    cursor.close()

    if usuario is None:
        flash("Usuário não encontrado")
        return redirect(url_for('nlogin'))

    senha_hash = usuario[3]

    if check_password_hash(senha_hash, senha):
        session["id_usuario"] = usuario[0]
        flash(f'Usuário logado com sucesso!')
        return redirect(url_for('index'))
    else:
        flash("Senha incorreta")
        return redirect(url_for('nlogin'))


@app.route('/novousuario')
def novousuario():
    return render_template('novousuario.html', titulo = "Novo usuario")

@app.route('/usuarios')
def usuarios():
    return render_template('usuarios.html', titulo = "Novo usuario")

@app.route('/criar', methods=["POST"])
def criar():
    if "id_usuario" not in session:
        flash("voce precisa estar logado")
        return redirect(url_for('nlogin'))
    titulo = request.form['titulo']
    autor = request.form['autor']
    ano_publicacao = request.form['ano_publicacao']

    cursor = con.cursor()
    try:
        cursor.execute('SELECT 1 FROM livros WHERE livros.TITULO = ?', (titulo,))
        if cursor.fetchall(): #se existe livro
            flash('Esse livro Já está cadastrado')
            return redirect(url_for('novo'))
        cursor.execute('INSERT INTO LIVROS(TITULO, AUTOR, ANO_PUBLICACAO)VALUES( ?, ?, ?) RETURNING id_livro',(titulo, autor, ano_publicacao))
        id_livro = cursor.fetchone()[0]
        con.commit()

        # Salvar o arquivo de capa
        arquivo = request.files['arquivo']
        arquivo.save(f'uploads/capa{id_livro}.jpg')
    finally:
        cursor.close()
    flash('o livro foi cadastrado com sucesso')
    return redirect(url_for('index'))

@app.route('/uploads/<nome_arquivo>')
def imagem(nome_arquivo):
    return send_from_directory('uploads', nome_arquivo)

@app.route('/criarusuario', methods=["POST"])
def criarusuario():
    nome = request.form['nome'].strip()
    email = request.form['email'].strip().lower()
    senha = request.form['senha'].strip()

    senha_cripto = generate_password_hash(senha).decode('utf-8')

    cursor = con.cursor()
    try:
        cursor.execute('SELECT 1 FROM USUARIOS WHERE LOWER(EMAIL) = ?', (email,))
        if cursor.fetchone():
            flash('Esse usuário já está cadastrado')
            return redirect(url_for('novousuario'))

        cursor.execute(
            'INSERT INTO USUARIOS (NOME, EMAIL, SENHA) VALUES (?, ?, ?)',
            (nome, email, senha_cripto)
        )
        con.commit()
    finally:
        cursor.close()

    flash('Usuário cadastrado com sucesso')
    return redirect(url_for('cadastro'))

@app.route('/atualizar')
def atualizar():
    return render_template('editar.html', titulo='Editar livro')

@app.route('/atualizarusuario')
def atualizarusuario():
    return render_template('editarusuario.html', titulo='Editar usuario')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if "id_usuario" not in session:
        flash("voce precisa estar logado")
        return redirect(url_for('nlogin'))
    cursor = con.cursor()
    cursor.execute("SELECT ID_LIVRO, TITULO, AUTOR, ANO_PUBLICACAO FROM LIVROS WHERE ID_LIVRO = ?", (id,))
    livro = cursor.fetchone()
    cursor.close()

    if not livro:
        flash("Livro não foi encontrado")
        return redirect(url_for('index'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        ano_publicacao = request.form['ano_publicacao']

        cursor = con.cursor()
        cursor.execute("UPDATE LIVROS SET TITULO = ?, AUTOR = ?, ANO_PUBLICACAO = ? WHERE ID_LIVRO = ?",
                       (titulo, autor, ano_publicacao, id))
        con.commit()
        cursor.close()
        flash("Livro atualizado com sucesso")
        return redirect(url_for('index'))

    return render_template('editar.html', livro=livro, titulo='Editar Livro')

@app.route('/editarusuario/<int:id>', methods=['GET', 'POST'])
def editarusuario(id):
    cursor = con.cursor()
    cursor.execute("SELECT ID_USUARIO, NOME, EMAIL, SENHA FROM USUARIOS WHERE ID_USUARIO = ?", (id,))
    usuario = cursor.fetchone()
    cursor.close()
    if not usuario:
        flash("Usuário não foi encontrado.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        nome = request.form['titulo'].strip()
        email = request.form['autor'].strip().lower()
        senha = request.form['senha'].strip()

        if senha:
            senha_cripto = generate_password_hash(senha).decode('utf-8')
        else:
            senha_cripto = usuario[3]

        cursor = con.cursor()
        cursor.execute(
            "UPDATE USUARIOS SET NOME = ?, EMAIL = ?, SENHA = ? WHERE ID_USUARIO = ?",
            (nome, email, senha_cripto, id)
        )
        con.commit()
        cursor.close()
        flash("Usuário atualizado com sucesso")
        return redirect(url_for('cadastro'))

    return render_template('editarusuario.html', usuario=usuario, titulo='Editar Usuário')


@app.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    if "id_usuario" not in session:
        flash("voce precisa estar logado")
        return redirect(url_for('nlogin'))
    cursor = con.cursor()
    cursor.execute("DELETE FROM LIVROS WHERE ID_LIVRO = ?", (id,))
    con.commit()
    cursor.close()
    flash("Livro excluído com sucesso")
    return redirect(url_for('index'))

@app.route('/deletarusuario/<int:id>', methods=['POST'])
def deletarusuario(id):
    cursor = con.cursor()
    cursor.execute("DELETE FROM USUARIOS WHERE ID_USUARIO = ?", (id,))
    con.commit()
    cursor.close()
    flash("Usuario excluído com sucesso")
    return redirect(url_for('cadastro'))

if __name__ == '__main__':
    app.run(debug=True)