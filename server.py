import json
import sqlite3
from flask import Flask, request, Response, render_template, url_for, redirect, flash, make_response
from flask_sqlalchemy import SQLAlchemy
import datetime
from flask_login import login_user, login_required, logout_user, UserMixin, LoginManager, current_user
from werkzeug.security import check_password_hash, generate_password_hash

# p2p = QiwiP2P(auth_key="48e7qUxn9T7RyYE1MVZswX1FRSbE6iyCj2gCRwwF3Dnh5XrasNTx3BGPiMsyXQFNKQhvukniQG8RTVhYm3iPrH4qg6CctHzLVenwr6m6GJXyhsr5o485uftHUjq2DuKzoYgd6j3cXSu6PDERn4UdnwWxieEsM4GUCw4jwkYkfrbK7r6UUUFXqUtbgSBng")



app = Flask(__name__)
app.secret_key = 'some secret'
stats = {'attampts':0, 'success':0}
MAX_CONTENT_LENGTH = 1024 * 1024
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///art2.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)
manager = LoginManager(app)
manager.login_view = 'login'
manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///basetovars2.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db3 = SQLAlchemy(app)

# class Article(db.Model):
#     id = db.Column(db.INTEGER, primary_key=True)
#     title = db.Column(db.TEXT, nullable=False)
#     intro = db.Column(db.TEXT, nullable=False)
#     text = db.Column(db.TEXT, nullable=False)
#     date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
#
#     def __repr__(self):
#         return '<Article %r>' % self.id

# class Users(db.Model):
#     id = db.Column(db.INTEGER, primary_key=True)
#     login = db.Column(db.String(20), unique=True)
#     password = db.Column(db.String(12), nullable=False)
#     email = db.Column(db.String(20), unique=True)
#     date_create = db.Column(db.DateTime, default=datetime.datetime.utcnow)
#
#     def __repr__(self):
#         return f"<users {self.id}>"

# class Tovars(db3.Model):
#     id = db.Column(db.INTEGER, nullable=False)
#     name = db.Column(db.TEXT, nullable=False)
#     price = db.Column(db.INTEGER, primary_key=True)
#     descr = db.Column(db.TEXT, nullable=False)
#     date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
#
#     def __repr__(self):
#         return f"<Tovars {self.id}>"
#
class User(db.Model, UserMixin):
    id = db.Column(db.INTEGER, primary_key=True)
    login = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(12), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    surname = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), unique=True)
    img = db.Column(db.BLOB)

@manager.user_loader
def user_load(user_id):
    return User.query.get(user_id)

id = 0

@app.route('/login', methods=['GET', 'POST'])
def login():
    flash("Для начала нужно войти в аккаунт!", 'success')
    global id
    if current_user.is_authenticated:
        id = current_user.get_id()
        user = User.query.get(id)
        login = user.login
        return redirect(url_for('profile', login = login))


    email = request.form.get('email')
    password = request.form.get('password')

    if email and password:
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            rm = True if request.form.get('remember-me') else False
            login_user(user, remember=rm)
            id = current_user.get_id()
            user = User.query.get(id)
            login = user.login
            return redirect(request.args.get("next") or url_for('profile', login=login))
        else:
            flash('Логин/Пароль введен(-ы) неверно!')
    else:
        flash('Логин и пароль не введены!')
    return render_template('login.html')

@app.route('/index')
def ind():
    return render_template('index.html')

@app.route('/logout')
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect("/login")

@app.route('/login/register', methods=['POST', "GET"])
def reg():
    if request.method=="POST":
        login = request.form['login']
        email = request.form['email']
        name = request.form['name']
        surname = request.form['surname']
        password = request.form['password']
        password2 = request.form['password2']
        if not (login or password2 or password or email or name or surname):
            flash('Пожалуйста, заполняйте все поля!')
        elif password != password2:
            flash('Пароли не совпадают!')
        else:
            hash_pwd = generate_password_hash(password)
            user = User(login=login, password=hash_pwd, email=email, name=name, surname=surname)
            db.session.add(user)
            db.session.commit()
            return redirect('/login')

    return render_template('auth.html')

@app.route('/<string:login>')
@login_required
def profile(login):
    id = current_user.get_id()
    user = User.query.get(id)
    return render_template("post_dateil.html", user=user, login=login)

def verifyExt(self, filename):
    ext = filename.rsplit('.', 1)[1]
    if ext == 'png' or ext == 'PNG':
        return True
    return False

def upua(self, img, user_id):
    if not img:
        return False

    try:
        binary = sqlite3.Binary(img)
        self.cur.execute(f"UPDATE user set img = ? where id = ?", (binary, user_id))
        self.db.commit()
    except sqlite3.Error as e:
        print("Ошибка обновления фото профиля в БД:"+str(e))
        return False
    return True

@app.route('/upload')
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and verifyExt(file.filename):
            try:
                img = file.read()
                binary = sqlite3.Binary(img)
                flash("Фото профиля обновлено!", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла!", "error")
        else:
            flash("Ошибка обновления фото профиля", "error")
    return redirect(url_for('reg'))

def a():
    id = current_user.get_id()
    user = User.query.get(id)
    img = user.img
    return img


@app.route('/userava')
@login_required
def userava():
    img = a()

    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = 'image/default.png'
    return h


@app.route('/')
def hello():
    # tovars = Tovars.query.order_by(Tovars.date.desc()).all()
    return render_template("index.html") #tovars=tovars


@app.route('/about')
def about():
    return render_template("about.html")\



# @app.route('/buy/<int:id>')
# def buy(id):
#     item = Tovars.query.get(id)
#     api = Api(merchant_id=1396424,
#               secret_key='test')
#     checkout = Checkout(api=api)
#     data = {
#         "currency":"RUB",
#         "amount":str(item.price) + 00
#     }
#     url = checkout.url(data).get('checkout_url')
#     return redirect(url)

# @app.route('/posts')
# @login_required
# def posts():
#     articles = Article.query.order_by(Article.date.desc()).all()
#     return render_template("posts.html", articles=articles)
#
# @app.route('/posts/<int:id>')
# def post_dateil(id):
#     article = Article.query.get(id)
#     return render_template("post_dateil.html", article=article)
#
# @app.route('/posts/<int:id>/delete')
# def post_delete(id):
#     article = Article.query.get_or_404(id)
#
#     try:
#         db.session.delete(article)
#         db.session.commit()
#         return redirect("/posts")
#     except:
#         return "При удалении статьи возникла ошибка"
#
# @app.route('/posts/<int:id>/update', methods=['POST', 'GET'])
# def post_update(id):
#     article = Article.query.get(id)
#     if request.method == "POST":
#         article.title = request.form['title']
#         article.intro = request.form['intro']
#         article.text = request.form['text']
#
#         article = Article(title=article.title, intro=article.intro, text=article.text)
#
#         try:
#             db.session.commit()
#             return redirect('/posts')
#         except:
#             return "При добавлении статьи возникла ошибка"
#     else:
#         return render_template("post_update.html", article=article)
#
# @app.route('/create-arcticle', methods=['POST', 'GET'])
# @login_required
# def create_arcticle():
#     if request.method == "POST":
#         title = request.form['title']
#         intro = request.form['intro']
#         text = request.form['text']
#
#         article = Article(title=title, intro=intro, text=text)
#
#         try:
#             db.session.add(article)
#             db.session.commit()
#             return redirect('/posts')
#         except:
#             return "При добавлении статьи возникла ошибка"
#     else:
#         return render_template("create-arcticle.html")

@app.route('/auth', methods = ['POST'])
def auth():
    stats['attampts']+=1
    data = request.json
    login = data['login']
    password = data['password']
    print(login,password)
    with open('users.json') as users_file:
        users = json.load(users_file)
    if login in users and users[login] == password:
        status_code=200
        stats['success']+=1
    else:
        status_code=401
    return Response(status=status_code)

if __name__=="__main__":
    app.run(debug=True)
