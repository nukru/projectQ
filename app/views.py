# -*- coding: utf-8 -*-

from app import app, db, lm, oid
from flask import render_template, flash, redirect, url_for, request, g, session
from forms import PreguntaForm, TipoPreguntaForm, PreguntaSeleccionForm
from models import  User, ROLE_ADMIN, ROLE_RESEARCHER, ROLE_USER
#login
from flask.ext.login import login_user, logout_user, current_user, login_required
from config import basedir

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email = resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname = nickname, email = resp.email, role = ROLE_USER)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('index'))

@app.before_request
def before_request():
    g.user = current_user

    
@app.route('/')
@app.route('/index')
def index():
    f = open(basedir+"/app/static/index.re", "r")
    text =  f.read()
    return render_template('index.html', text = text)


@app.route('/pregunta', methods = ['GET', 'POST'])
#pagina que muestra el tipo de pregunta a generar
def pregunta():
    form = TipoPreguntaForm()
    if form.validate_on_submit():
        flash (form.tipo.data)
        if form.tipo.data == 'S/N':
            return redirect(url_for('s_n'))
        elif form.tipo.data == 'Numerica':
            return redirect(url_for('numerica'))
        elif form.tipo.data == 'Texto':
            return redirect(url_for('texto'))
        elif form.tipo.data == 'Seleccion':
            return redirect(url_for('seleccion'))
        return redirect('/pregunta')
    #    return redirect(url_for('index'))
    return render_template('tipo-pregunta.html', 
            title = 'valiendo',
            form = form)

@app.route('/pregunta/numerica', methods = ['GET', 'POST'])
#pagina para crear una pregunta de tipo numerica
def numerica():
    form = PreguntaForm()
    if form.validate_on_submit():
        flash ('añadiendo en la base de datos')
        pregunta = PreguntaNumerica (texto = form.texto.data,
            obligatoriedad = form.obligatoriedad.data)
        db.session.add(pregunta)
        db.session.commit()
        return redirect ('cuestionario')
    return render_template ('pregunta/numerica.html',
        title = 'Pregunta Numerica',
        form = form)

@app.route('/pregunta/texto', methods = ['GET', 'POST'])
#pagina para crear una pregunta de tipo numerica
def texto():
    form = PreguntaForm()
    if form.validate_on_submit():
        flash ('añadiendo en la base de datos')
        pregunta = PreguntaTexto (texto = form.texto.data,
            obligatoriedad = form.obligatoriedad.data)
        db.session.add(pregunta)
        db.session.commit()
        return redirect ('cuestionario')
    return render_template ('pregunta/texto.html',
        title = 'Pregunta Texto',
        form = form)

@app.route('/pregunta/s-n', methods = ['GET', 'POST'])
#pagina para crear una pregunta de tipo s-n
def s_n():
    form = PreguntaForm()
    if form.validate_on_submit():
        flash ('añadiendo en la base de datos')
        pregunta = PreguntaSN (texto = form.texto.data,
            obligatoriedad = form.obligatoriedad.data)
        db.session.add(pregunta)
        db.session.commit()
        return redirect ('cuestionario')
    return render_template ('pregunta/s-n.html',
        title = 'Pregunta S/N',
        form = form)


@app.route('/pregunta/seleccion', methods = ['GET', 'POST'])
#pagina para crear una pregunta de tipo numerica
def seleccion():
    form = PreguntaForm()
    seleccionForm = PreguntaSeleccionForm()
    if form.validate_on_submit() and seleccionForm.validate_on_submit:
        flash ('añadiendo en la base de datos')
        print seleccionForm.texto1.data
        lista = [seleccionForm.texto1.data,
            seleccionForm.texto2.data,
            seleccionForm.texto3.data,
            seleccionForm.texto4.data,
            seleccionForm.texto5.data,
            seleccionForm.texto6.data,
            seleccionForm.texto7.data,
            seleccionForm.texto8.data,
            seleccionForm.texto9.data]
        print 'antes',lista
        #eliminamos los elementos vacios, se recorre al resve
        for i in reversed( range (len(lista))):
            if lista[i] == '':
                del lista[i]
        print 'despues',lista
        pregunta = PreguntaSeleccion (texto = form.texto.data,
            obligatoriedad = form.obligatoriedad.data,
            opciones = lista)
        db.session.add(pregunta)
        db.session.commit()
        return redirect ('cuestionario')
    return render_template ('pregunta/seleccion.html',
        title = 'Pregunta seleccion',
        form = form,
        seleccionForm = seleccionForm)


@app.route('/pregunta/seleccion2', methods = ['GET', 'POST'])
#pagina para crear una pregunta de tipo numerica
def seleccion2():
    lista = (PreguntaSeleccionForm(),PreguntaSeleccionForm())
    return render_template ('pregunta/seleccion2.html',
        title = 'Pregunta seleccion',
        lista = lista)


@app.route('/cuestionario')
#muestra todas las consultas de la base de datos
def cuestionario():
    #realizar consulta
    #preguntas = Pregunta.query.all()
    preguntas = Pregunta.query.order_by(Pregunta.id.desc())
    #renderizar
    return render_template('cuestionario.html',
        title = 'Cuestionario',
        preguntas = preguntas)




@app.route('/pregunta/eliminar/<int:id>')
#elimina una pregunta de la base de datos
def eliminar(id):
    pregunta = Pregunta.query.get(id)
    db.session.delete(pregunta)
    db.session.commit()
    flash('Your post has been deleted.')
    return redirect(url_for('index'))


@app.route('/pregunta/copiar/<int:id>')
def copiar(id):
  #  pregunta = Pregunta.query.get(id)
    #db.session.delete(post)
    #db.session.commit()
    flash('Pregunta copiada')
    return redirect(url_for('cuestionario'))

@app.route('/pregunta/editar/<int:id>')
#edita una pregunta de la base de datos
def editar(id):
    pregunta = Pregunta.query.get(id)
    form = PreguntaForm(texto = pregunta.texto,
        obligatoriedad = pregunta.obligatoriedad )
    flash('Editando pregunta')
    return render_template ('pregunta/pregunta.html',
        title = 'Editando Pregunta',
        form = form)