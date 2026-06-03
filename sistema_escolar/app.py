from flask import Flask, render_template, request, redirect, session
import sqlite3
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import styles

app = Flask(__name__)

app.secret_key = "minha_chave_secreta"

# CRIAR BANCO DE DADOS E TABELA PRINCIPAL
conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    cargo TEXT NOT NULL
)
""")

# ADMIN
cursor.execute("""
INSERT OR IGNORE INTO usuarios
(nome, usuario, senha, cargo)

VALUES
('Administrador',
'admin',
'123456',
'admin')
""")

conn.commit()
conn.close()

# TABELA DE ALUNOS
conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS alunos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    matricula TEXT UNIQUE NOT NULL,
    nascimento TEXT NOT NULL,
    turma TEXT
)
""")

conn.commit()
conn.close()

# TABELA DE PROFESSORES
conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS professores(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    disciplina TEXT NOT NULL,
    telefone TEXT,
    email TEXT
)
""")

conn.commit()
conn.close()

# TABELA DE TURMAS
conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS turmas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    serie TEXT NOT NULL,
    sala TEXT,
    professor_id INTEGER
)
""")

conn.commit()
conn.close()

# TABELA DE NOTAS
conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS notas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL,
    disciplina TEXT NOT NULL,
    nota1 REAL,
    nota2 REAL,
    nota3 REAL,
    nota4 REAL
)
""")

conn.commit()
conn.close()

 # CRIAR TABELA FREQUENCIA

conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS frequencia(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    status TEXT NOT NULL
)
""")

conn.commit()
conn.close()

# VERIFICAÇÃO DE CARGOS
def verificar_cargo(cargos_permitidos):

    if "usuario" not in session:
        return False
    
    if session["cargo"] not in cargos_permitidos:
        return False
    
    return True

# LOGIN PRINCIPAL
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        senha = request.form["senha"]

        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND senha=?",
            (usuario, senha)
        )

        usuario_encontrado = cursor.fetchone()

        conn.close()

        if usuario_encontrado:

            session["usuario"] = usuario
            session["cargo"] = usuario_encontrado[4]

            if session["cargo"] == "admin":
                return redirect("/dashboard")

            elif session["cargo"] == "professor":
                return redirect("/dashboard_professor")

            elif session["cargo"] == "secretaria":
                return redirect("/dashboard_secretaria")

            elif session["cargo"] == "aluno":
                return redirect("/dashboard_aluno")

        return "Usuário ou senha incorretos"

    return render_template("index.html")

# DASHBOARD PRINCIPAL
# DASHBOARD ADMIN
@app.route("/dashboard")
def dashboard():

    if not verificar_cargo(["admin"]):
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    # TOTAIS

    cursor.execute(
        "SELECT COUNT(*) FROM usuarios"
    )
    total_usuarios = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM alunos"
    )
    total_alunos = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM professores"
    )
    total_professores = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM turmas"
    )
    total_turmas = cursor.fetchone()[0]


    # ÚLTIMOS ALUNOS CADASTRADOS

    cursor.execute("""
    SELECT nome, matricula
    FROM alunos
    ORDER BY id DESC
    LIMIT 5
    """)

    ultimos_alunos = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",

        usuario=session["usuario"],
        total_usuarios=total_usuarios,
        total_alunos=total_alunos,
        total_professores=total_professores,
        total_turmas=total_turmas,
        ultimos_alunos=ultimos_alunos
    )

# DASHBOARD PROFESSOR
@app.route("/dashboard_professor")
def dashboard_professor():

    if not verificar_cargo(["professor"]):
        return redirect("/")

    return render_template(
        "dashboard_professor.html"
    )

# DASHBOARD SECRETARIA
@app.route("/dashboard_secretaria")
def dashboard_secretaria():

    if not verificar_cargo(["secretaria"]):
        return redirect("/")

    return render_template(
        "dashboard_secretaria.html"
    )

# DASHBOARD ALUNO
@app.route("/dashboard_aluno")
def dashboard_aluno():

    if not verificar_cargo(["aluno"]):
        return redirect("/")

    return render_template(
        "dashboard_aluno.html"
    )

# LISTA DE USUÁRIOS
@app.route("/usuarios")
def usuarios():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios")

    lista_usuarios = cursor.fetchall()

    conn.close()

    return render_template(
        "usuarios.html",
        usuarios=lista_usuarios
    )

# CADASTRO DE USUÁRIOS
@app.route("/cadastrar_usuario", methods=["GET", "POST"])
def cadastrar_usuario():

    if "usuario" not in session:
        return redirect("/")

    if request.method == "POST":

        nome = request.form["nome"]
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        cargo = request.form["cargo"]

        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO usuarios
            (nome, usuario, senha, cargo)

            VALUES (?, ?, ?, ?)
            """, (
                nome,
                usuario,
                senha,
                cargo
            ))

            conn.commit()
            conn.close()

            return redirect("/usuarios")

        except sqlite3.IntegrityError:

            conn.close()

            return "Usuário já cadastrado"

    return render_template(
        "cadastrar_usuario.html"
    )

# EDITAR USUÁRIOS
@app.route("/editar_usuario/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    if request.method == "POST":

        nome = request.form["nome"]
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        cargo = request.form["cargo"]

        try:

            cursor.execute("""
            UPDATE usuarios

            SET
            nome=?,
            usuario=?,
            senha=?,
            cargo=?

            WHERE id=?
            """,(
                nome,
                usuario,
                senha,
                cargo,
                id
            ))

            conn.commit()
            conn.close()

            return redirect("/usuarios")

        except sqlite3.IntegrityError:

            conn.close()

            return "Esse usuário já existe"

    cursor.execute(
        "SELECT * FROM usuarios WHERE id=?",
        (id,)
    )

    usuario = cursor.fetchone()

    conn.close()

    return render_template(
        "editar_usuario.html",
        usuario=usuario
    )

# EXCLUIR USUÁRIOS
@app.route("/excluir_usuario/<int:id>")
def excluir_usuario(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM usuarios WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/usuarios")

# LISTA DE ALUNOS
@app.route("/alunos")
def alunos():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM alunos"
    )

    lista_alunos = cursor.fetchall()

    conn.close()

    return render_template(
        "alunos.html",
        alunos=lista_alunos
    )

# PESQUISAR ALUNOS
@app.route("/pesquisar_aluno", methods=["GET"])
def pesquisar_aluno():

    if "usuario" not in session:
        return redirect("/")

    busca = request.args.get("busca","")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *
    FROM alunos

    WHERE nome LIKE ?
    OR matricula LIKE ?

    """,(
        "%" + busca + "%",
        "%" + busca + "%"
    ))

    alunos = cursor.fetchall()

    conn.close()

    return render_template(
        "alunos.html",
        alunos=alunos
    )

# CADASTRO DE ALUNOS
@app.route("/cadastrar_aluno", methods=["GET","POST"])
def cadastrar_aluno():

    if "usuario" not in session:
        return redirect("/")

    if request.method == "POST":

        nome = request.form["nome"]
        matricula = request.form["matricula"]
        nascimento = request.form["nascimento"]
        turma = request.form["turma"]

        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO alunos
            (nome, matricula, nascimento, turma)

            VALUES(?,?,?,?)
            """, (
                nome,
                matricula,
                nascimento,
                turma
            ))

            conn.commit()
            conn.close()

            return redirect("/alunos")

        except sqlite3.IntegrityError:

            conn.close()

            return "Matrícula já cadastrada"

    return render_template(
        "cadastrar_aluno.html"
    )

# EDITAR ALUNOS
@app.route("/editar_aluno/<int:id>", methods=["GET", "POST"])
def editar_aluno(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    if request.method == "POST":

        nome = request.form["nome"]
        matricula = request.form["matricula"]
        nascimento = request.form["nascimento"]
        turma = request.form["turma"]

        try:

            cursor.execute("""
            UPDATE alunos

            SET
            nome=?,
            matricula=?,
            nascimento=?,
            turma=?

            WHERE id=?
            """,(
                nome,
                matricula,
                nascimento,
                turma,
                id
            ))

            conn.commit()
            conn.close()

            return redirect("/alunos")

        except sqlite3.IntegrityError:

            conn.close()

            return "Matrícula já cadastrada"

    cursor.execute(
        "SELECT * FROM alunos WHERE id=?",
        (id,)
    )

    aluno = cursor.fetchone()

    conn.close()

    return render_template(
        "editar_aluno.html",
        aluno=aluno
    )

# EXCLUIR ALUNOS
@app.route("/excluir_aluno/<int:id>")
def excluir_aluno(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM alunos WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/alunos")

# LISTA DE PROFESSORES
@app.route("/professores")
def professores():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM professores"
    )

    lista_professores = cursor.fetchall()

    conn.close()

    return render_template(
        "professores.html",
        professores=lista_professores
    )

# CADASTRO DE PROFESSORES
@app.route("/cadastrar_professor", methods=["GET","POST"])
def cadastrar_professor():

    if "usuario" not in session:
        return redirect("/")

    if request.method == "POST":

        nome = request.form["nome"]
        disciplina = request.form["disciplina"]
        telefone = request.form["telefone"]
        email = request.form["email"]

        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO professores
        (nome, disciplina, telefone, email)

        VALUES(?,?,?,?)
        """, (
            nome,
            disciplina,
            telefone,
            email
        ))

        conn.commit()
        conn.close()

        return redirect("/professores")

    return render_template(
        "cadastrar_professor.html"
    )

# EDITAR PROFESSOR
@app.route("/editar_professor/<int:id>", methods=["GET","POST"])
def editar_professor(id):

    if not verificar_cargo(["admin"]):
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    if request.method == "POST":

        nome = request.form["nome"]
        disciplina = request.form["disciplina"]
        telefone = request.form["telefone"]
        email = request.form["email"]

        # VALIDAÇÃO
        if nome.strip() == "":
            conn.close()
            return "Nome não pode ficar vazio"

        try:

            cursor.execute("""

            UPDATE professores

            SET
            nome=?,
            disciplina=?,
            telefone=?,
            email=?

            WHERE id=?

            """,(
                nome,
                disciplina,
                telefone,
                email,
                id
            ))

            conn.commit()
            conn.close()

            return redirect("/professores")

        except Exception:

            conn.close()

            return "Erro ao atualizar professor"


    cursor.execute(
        "SELECT * FROM professores WHERE id=?",
        (id,)
    )

    professor = cursor.fetchone()

    conn.close()

    return render_template(
        "editar_professor.html",
        professor=professor
    )

# EXCLUIR PROFESSORES
@app.route("/excluir_professor/<int:id>")
def excluir_professor(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM professores WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/professores")

# LISTA DE TURMAS
@app.route("/turmas")
def turmas():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT turmas.*, professores.nome
    FROM turmas

    LEFT JOIN professores
    ON turmas.professor_id = professores.id
    """)

    lista_turmas = cursor.fetchall()

    conn.close()

    return render_template(
        "turmas.html",
        turmas=lista_turmas
    )

# CADASTRO DA TURMA
@app.route("/cadastrar_turma", methods=["GET","POST"])
def cadastrar_turma():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    if request.method == "POST":
        nome         = request.form.get("nome", "").strip()
        serie        = request.form.get("serie", "").strip()
        sala         = request.form.get("sala", "").strip()

        # Validação
        if not nome or not serie:
            conn.close()
            return render_template(
                "cadastrar_turma.html",
                erro="Nome e série são obrigatórios."
            )

        cursor.execute("""
            INSERT INTO turmas (nome, serie, sala)
            VALUES (?, ?, ?)
        """, (nome, serie, sala))

        conn.commit()
        conn.close()
        return redirect("/turmas")

    conn.close()
    return render_template("cadastrar_turma.html")


# EDITAR TURMA
@app.route("/editar_turma/<int:id>", methods=["GET","POST"])
def editar_turma(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    if request.method == "POST":

        nome = request.form["nome"]
        serie = request.form["serie"]
        sala = request.form["sala"]

        # Validação
        if nome.strip() == "" or serie.strip() == "":
            conn.close()
            return "Nome e série são obrigatórios"

        try:

            cursor.execute("""
                UPDATE turmas
                SET nome=?, serie=?, sala=?
                WHERE id=?
            """, (nome, serie, sala, id))

            conn.commit()
            conn.close()

            return redirect("/turmas")

        except Exception as e:

            conn.close()
            return f"Erro ao atualizar turma: {e}"

    # GET
    cursor.execute("SELECT * FROM turmas WHERE id=?", (id,))
    turma = cursor.fetchone()

    conn.close()

    return render_template("editar_turma.html", turma=turma)

# EXCLUIR TURMAS
@app.route("/excluir_turma/<int:id>")
def excluir_turma(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM turmas WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/turmas")

# LISTA DE NOTAS
@app.route("/notas")
def notas():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT notas.*, alunos.nome
    FROM notas

    JOIN alunos
    ON notas.aluno_id = alunos.id
    """)

    lista_notas = cursor.fetchall()

    conn.close()

    return render_template(
        "notas.html",
        notas=lista_notas
    )

# CADASTRO DE NOTAS
@app.route("/cadastrar_notas", methods=["GET","POST"])
def cadastrar_notas():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    if request.method == "POST":

        aluno_id = request.form["aluno_id"]
        disciplina = request.form["disciplina"]
        nota1 = request.form["nota1"]
        nota2 = request.form["nota2"]
        nota3 = request.form["nota3"]
        nota4 = request.form["nota4"]

        cursor.execute("""
        INSERT INTO notas
        (aluno_id, disciplina, nota1, nota2, nota3, nota4)

        VALUES(?,?,?,?,?,?)
        """, (
            aluno_id,
            disciplina,
            nota1,
            nota2,
            nota3,
            nota4
        ))

        conn.commit()
        conn.close()

        return redirect("/notas")

    cursor.execute(
        "SELECT * FROM alunos"
    )

    alunos = cursor.fetchall()

    conn.close()

    return render_template(
        "cadastrar_notas.html",
        alunos=alunos
    )

# EDITAR NOTAS
@app.route("/editar_notas/<int:id>", methods=["GET","POST"])
def editar_notas(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    if request.method == "POST":

        disciplina = request.form["disciplina"]

        nota1 = float(request.form["nota1"])
        nota2 = float(request.form["nota2"])
        nota3 = float(request.form["nota3"])
        nota4 = float(request.form["nota4"])

        # VALIDAÇÃO
        notas = [nota1, nota2, nota3, nota4]

        for nota in notas:

            if nota < 0 or nota > 10:

                conn.close()

                return "As notas devem estar entre 0 e 10"

        try:

            cursor.execute("""

            UPDATE notas

            SET
            disciplina=?,
            nota1=?,
            nota2=?,
            nota3=?,
            nota4=?

            WHERE id=?

            """,(
                disciplina,
                nota1,
                nota2,
                nota3,
                nota4,
                id
            ))

            conn.commit()
            conn.close()

            return redirect("/notas")

        except Exception:

            conn.close()

            return "Erro ao atualizar notas"


    cursor.execute(
        "SELECT * FROM notas WHERE id=?",
        (id,)
    )

    nota = cursor.fetchone()

    conn.close()

    return render_template(
        "editar_notas.html",
        nota=nota
    )

# EXCLUIR NOTAS
@app.route("/excluir_notas/<int:id>")
def excluir_notas(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM notas WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/notas")

# LISTA DE FREQUÊNCIA
@app.route("/frequencia")
def frequencia():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT frequencia.*, alunos.nome
    FROM frequencia

    JOIN alunos
    ON frequencia.aluno_id = alunos.id
    """)

    lista_frequencia = cursor.fetchall()

    conn.close()

    return render_template(
        "frequencia.html",
        frequencia=lista_frequencia
    )

# CADASTRO DE FREQUÊNCIA
@app.route("/cadastrar_frequencia", methods=["GET", "POST"])
def cadastrar_frequencia():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    if request.method == "POST":

        aluno_id = request.form["aluno_id"]
        data = request.form["data"]
        status = request.form["status"]

        cursor.execute("""
        INSERT INTO frequencia
        (aluno_id, data, status)

        VALUES(?,?,?)
        """, (
            aluno_id,
            data,
            status
        ))

        conn.commit()
        conn.close()

        return redirect("/frequencia")

    cursor.execute(
        "SELECT * FROM alunos"
    )

    alunos = cursor.fetchall()

    conn.close()

    return render_template(
        "cadastrar_frequencia.html",
        alunos=alunos
    )

# EDITAR FREQUÊNCIA
@app.route("/editar_frequencia/<int:id>", methods=["GET","POST"])
def editar_frequencia(id):

    if not verificar_cargo(["admin","professor"]):
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    if request.method == "POST":

        aluno_id = request.form["aluno_id"]
        data = request.form["data"]
        status = request.form["status"]

        # VALIDAÇÃO
        if status not in ["Presente", "Falta"]:

            conn.close()

            return "Status inválido"

        try:

            cursor.execute("""

            UPDATE frequencia

            SET
            aluno_id=?,
            data=?,
            status=?

            WHERE id=?

            """,(
                aluno_id,
                data,
                status,
                id
            ))

            conn.commit()
            conn.close()

            return redirect("/frequencia")

        except Exception:

            conn.close()

            return "Erro ao atualizar frequência"


    cursor.execute(
        "SELECT * FROM frequencia WHERE id=?",
        (id,)
    )

    frequencia = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM alunos"
    )

    alunos = cursor.fetchall()

    conn.close()

    return render_template(
        "editar_frequencia.html",
        frequencia=frequencia,
        alunos=alunos
    )

# EXCLUIR FREQUÊNCIA
@app.route("/excluir_frequencia/<int:id>")
def excluir_frequencia(id):

    if not verificar_cargo(["admin","professor"]):
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM frequencia WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/frequencia")

# RELATÓRIO DE ALUNOS
@app.route("/relatorio_alunos")
def relatorio_alunos():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM alunos
    """)

    alunos = cursor.fetchall()

    conn.close()

    return render_template(
        "relatorio_alunos.html",
        alunos=alunos
    )

# RELATÓRIO DE NOTAS
@app.route("/relatorio_notas")
def relatorio_notas():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT notas.*, alunos.nome
    FROM notas

    JOIN alunos
    ON notas.aluno_id = alunos.id
    """)

    notas = cursor.fetchall()

    conn.close()

    return render_template(
        "relatorio_notas.html",
        notas=notas
    )

# RELATÓRIO DE FREQUÊNCIA
@app.route("/relatorio_frequencia")
def relatorio_frequencia():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT frequencia.*, alunos.nome
    FROM frequencia

    JOIN alunos
    ON frequencia.aluno_id = alunos.id
    """)

    frequencia = cursor.fetchall()

    conn.close()

    return render_template(
        "relatorio_frequencia.html",
        frequencia=frequencia
    )

# BOLETIM DO ALUNO
@app.route("/boletim")
def boletim():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT
                   alunos.nome,
                   notas.disciplina,
                   notas.nota1,
                   notas.nota2,
                   notas.nota3,
                   notas.nota4
                   FROM notas
                   JOIN alunos
                   ON notas.aluno_id = alunos.id
                   """)
    notas = cursor.fetchall()

    boletim = []

    for nota in notas:

        media = (
            nota[2] +
            nota[3] +
            nota[4] +
            nota[5]
        ) / 4

        if media >= 7:
            situacao = "Aprovado"

        elif media >= 5:
            situacao = "Recuperação"

        else:
            situacao = "Reprovado"

        boletim.append(
            (
                nota[0],
                nota[1],
                nota[2],
                nota[3],
                nota[4],
                nota[5],
                round(media,2),
                situacao
            )
        )

    conn.close()

    return render_template(
        "boletim.html",
        boletim=boletim
    )

# RELATÓRIO COMPLETO ALUNO
@app.route("/perfil_aluno/<int:id>")
def perfil_aluno(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    # DADOS DO ALUNO
    cursor.execute(
        "SELECT * FROM alunos WHERE id=?",
        (id,)
    )

    aluno = cursor.fetchone()

    # NOTAS
    cursor.execute("""
    SELECT disciplina,
    nota1,
    nota2,
    nota3,
    nota4

    FROM notas

    WHERE aluno_id=?
    """,(id,))

    notas = cursor.fetchall()

    # FREQUÊNCIA
    cursor.execute("""
    SELECT COUNT(*)
    FROM frequencia
    WHERE aluno_id=?
    AND status='Falta'
    """,(id,))

    faltas = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM frequencia
    WHERE aluno_id=?
    """,(id,))

    total_aulas = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "perfil.html",
        aluno=aluno,
        notas=notas,
        faltas=faltas,
        total_aulas=total_aulas
    )

# GERAR PDF DO BOLETIM
@app.route("/gerar_pdf/<int:id>")
def gerar_pdf(id):

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
    alunos.nome,
    notas.disciplina,
    notas.nota1,
    notas.nota2,
    notas.nota3,
    notas.nota4

    FROM notas

    JOIN alunos
    ON notas.aluno_id = alunos.id

    WHERE alunos.id=?
    """,(id,))

    dados = cursor.fetchall()

    conn.close()

    documento = SimpleDocTemplate(
        f"boletim_{id}.pdf"
    )

    estilo = styles.getSampleStyleSheet()

    conteudo = []

    conteudo.append(
        Paragraph(
        "Boletim Escolar",
        estilo["Title"]
        )
    )

    conteudo.append(
        Spacer(1,20)
    )

    for linha in dados:

        texto = f"""
        Aluno: {linha[0]} <br/>
        Disciplina: {linha[1]} <br/>
        Nota 1: {linha[2]} <br/>
        Nota 2: {linha[3]} <br/>
        Nota 3: {linha[4]} <br/>
        Nota 4: {linha[5]}
        """
        conteudo.append(
            Paragraph(
            texto,
            estilo["BodyText"]
            )
        )

        conteudo.append(
            Spacer(1,15)
        )

    documento.build(conteudo)

    return "PDF gerado com sucesso"

# PERFIL
@app.route("/perfil")
def perfil():

    if "usuario" not in session:
        return redirect("/")

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM usuarios WHERE usuario=?",
        (session["usuario"],)
    )

    usuario = cursor.fetchone()

    conn.close()

    return render_template(
        "perfil.html",
        usuario=usuario
    )

@app.route("/agenda")
def agenda():
    return render_template("agenda.html")

# LOGOUT
@app.route("/logout")
def logout():

    session.pop("usuario", None)
    session.pop("cargo", None)

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)