from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import re
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news_blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация SQLAlchemy
db = SQLAlchemy(app)


# Модель User
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    hashed_password = db.Column(db.String(200), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь "один ко многим" с Article
    articles = db.relationship('Article', backref='author', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def __repr__(self):
        return f'<User {self.name}>'


# Модель Article
class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Внешний ключ для связи с User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Article {self.title}>'


# Создание таблиц при запуске
with app.app_context():
    db.create_all()

    # Создаем тестовых пользователей, если их нет (с проверкой на уникальность)
    if not User.query.first():  # Проверяем, есть ли вообще пользователи
        users_to_create = [
            {'name': 'Петя Пупкин', 'email': 'petya@meowblog.ru'},
            {'name': 'Кай Ангел', 'email': 'kai@meowblog.ru'},
            {'name': 'Людка Тетка', 'email': 'lyudka@meowblog.ru'},
            {'name': 'Кузя Лакомкин', 'email': 'kuzya@meowblog.ru'}
        ]

        for user_data in users_to_create:
            # Проверяем, не существует ли уже пользователь с таким email
            if not User.query.filter_by(email=user_data['email']).first():
                user = User(name=user_data['name'], email=user_data['email'])
                user.set_password('password123')
                db.session.add(user)

        db.session.commit()

# Обновленные категории
CATEGORIES = [
    'Искусство',
    'Мода',
    'Разное',
    'Политика'
]

# Обновленные статьи с новыми авторами
NEWS_ARTICLES = [
    {
        'id': 1,
        'title': 'Новая картина Бэнкси',
        'date': date.today().strftime('%d %B %Y'),
        'excerpt': 'пока не нарисована...',
        'content': '''<p>Может завтра нарисует?</p>''',
        'author_id': 1,
        'category': 'Искусство'
    },
    {
        'id': 2,
        'title': 'Я новость',
        'date': '25 марта 2025',
        'excerpt': 'не открывай меня',
        'content': '''<p>Да блин нуууу :(((</p>''',
        'author_id': 2,
        'category': 'Разное'
    },
    {
        'id': 3,
        'title': 'Новый показ Victoria`s Secret',
        'date': date.today().strftime('%d %B %Y'),
        'excerpt': 'Возвращение легендарных ангелов на подиум',
        'content': '''<p>Красотки, умницы, молодцы! Так держать девчонки!</p>''',
        'author_id': 3,
        'category': 'Мода'
    }
]

# Обновленные авторы (для совместимости со старым кодом)
AUTHORS = [
    {'id': 1, 'name': 'Петя Пупкин', 'email': 'petya@meowblog.ru'},
    {'id': 2, 'name': 'Кай Ангел', 'email': 'kai@meowblog.ru'},
    {'id': 3, 'name': 'Людка Тетка', 'email': 'lyudka@meowblog.ru'},
    {'id': 4, 'name': 'Кузя Лакомкин', 'email': 'kuzya@meowblog.ru'}
]


def is_today_article(article_date):
    try:
        article_datetime = datetime.strptime(article_date, '%d %B %Y')
        return article_datetime.date() == date.today()
    except ValueError:
        return False


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_form(name, email, message):
    errors = {}

    if not name.strip():
        errors['name'] = 'Имя обязательно для заполнения'

    if not email.strip():
        errors['email'] = 'Email обязателен для заполнения'
    elif not validate_email(email):
        errors['email'] = 'Введите корректный email адрес'

    if not message.strip():
        errors['message'] = 'Сообщение обязательно для заполнения'
    elif len(message.strip()) < 10:
        errors['message'] = 'Сообщение должно содержать минимум 10 символов'

    return errors


def validate_article_form(title, content, author_id, category):
    errors = {}

    if not title.strip():
        errors['title'] = 'Заголовок обязателен для заполнения'
    elif len(title.strip()) < 5:
        errors['title'] = 'Заголовок должен содержать минимум 5 символов'

    if not content.strip():
        errors['content'] = 'Содержание статьи обязательно'
    elif len(content.strip()) < 50:
        errors['content'] = 'Статья должна содержать минимум 50 символов'

    if not author_id:
        errors['author_id'] = 'Необходимо выбрать автора'

    if not category.strip():
        errors['category'] = 'Необходимо выбрать категорию'

    return errors


# Маршруты
@app.route('/')
def index():
    today_articles = [article for article in NEWS_ARTICLES if is_today_article(article['date'])]
    return render_template('index.html', today_articles=today_articles)


@app.route('/news')
def news():
    return render_template('news.html', articles=NEWS_ARTICLES, is_today_article=is_today_article)


@app.route('/news/<int:id>')
def news_article(id):
    article = next((article for article in NEWS_ARTICLES if article['id'] == id), None)

    if article:
        author = next((author for author in AUTHORS if author['id'] == article['author_id']), None)
        return render_template('news_article.html', article=article, author=author, is_today_article=is_today_article)
    else:
        return render_template('news_article.html',
                               article={'id': id, 'title': f'Статья {id}',
                                        'date': datetime.now().strftime('%d %B %Y'),
                                        'content': f'<p>Статья с ID {id} находится в разработке. Скоро здесь появится интересный контент!</p>'},
                               is_today_article=is_today_article)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        errors = validate_form(name, email, message)

        if errors:
            return render_template('feedback.html',
                                   name=name,
                                   email=email,
                                   message=message,
                                   errors=errors)
        else:
            flash('Сообщение успешно отправлено!', 'success')
            return render_template('feedback_success.html',
                                   name=name,
                                   email=email,
                                   message=message)

    return render_template('feedback.html')


@app.route('/create-article', methods=['GET', 'POST'])
def create_article():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        author_id = request.form.get('author_id')
        category = request.form.get('category', '').strip()
        excerpt = request.form.get('excerpt', '').strip()

        errors = validate_article_form(title, content, author_id, category)

        if errors:
            return render_template('create_article.html',
                                   title=title,
                                   content=content,
                                   author_id=author_id,
                                   category=category,
                                   excerpt=excerpt,
                                   errors=errors,
                                   authors=AUTHORS,
                                   categories=CATEGORIES)
        else:
            new_article = {
                'id': len(NEWS_ARTICLES) + 1,
                'title': title,
                'content': f'<p>{content}</p>',
                'excerpt': excerpt or content[:100] + '...' if content else '',
                'date': date.today().strftime('%d %B %Y'),
                'author_id': int(author_id),
                'category': category
            }

            NEWS_ARTICLES.append(new_article)
            flash('Статья успешно создана!', 'success')
            return redirect(url_for('news_article', id=new_article['id']))

    return render_template('create_article.html',
                           authors=AUTHORS,
                           categories=CATEGORIES)


# Редактирование статьи
@app.route('/edit-article/<int:id>', methods=['GET', 'POST'])
def edit_article(id):
    article = next((article for article in NEWS_ARTICLES if article['id'] == id), None)

    if not article:
        flash('Статья не найдена!', 'error')
        return redirect(url_for('news'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        author_id = request.form.get('author_id')
        category = request.form.get('category', '').strip()
        excerpt = request.form.get('excerpt', '').strip()

        errors = validate_article_form(title, content, author_id, category)

        if errors:
            return render_template('edit_article.html',
                                   article=article,
                                   title=title,
                                   content=content,
                                   author_id=author_id,
                                   category=category,
                                   excerpt=excerpt,
                                   errors=errors,
                                   authors=AUTHORS,
                                   categories=CATEGORIES)
        else:
            # Обновляем статью
            article['title'] = title
            article['content'] = f'<p>{content}</p>'
            article['excerpt'] = excerpt or content[:100] + '...' if content else ''
            article['author_id'] = int(author_id)
            article['category'] = category

            flash('Статья успешно обновлена!', 'success')
            return redirect(url_for('news_article', id=id))

    # GET запрос - показываем форму с текущими данными
    return render_template('edit_article.html',
                           article=article,
                           title=article['title'],
                           content=article['content'].replace('<p>', '').replace('</p>', ''),
                           author_id=article['author_id'],
                           category=article['category'],
                           excerpt=article['excerpt'],
                           authors=AUTHORS,
                           categories=CATEGORIES)


# Удаление статьи
@app.route('/delete-article/<int:id>')
def delete_article(id):
    global NEWS_ARTICLES
    article = next((article for article in NEWS_ARTICLES if article['id'] == id), None)

    if article:
        NEWS_ARTICLES = [article for article in NEWS_ARTICLES if article['id'] != id]
        flash('Статья успешно удалена!', 'success')
    else:
        flash('Статья не найдена!', 'error')

    return redirect(url_for('news'))


# Демонстрация работы с моделями
@app.route('/demo-db')
def demo_db():
    """Страница для демонстрации работы с моделями"""

    # Получаем всех пользователей и статьи из БД
    users = User.query.all()
    articles = Article.query.all()

    return render_template('demo_db.html', users=users, articles=articles)


# Маршрут для фильтрации по категориям
@app.route('/category/<category_name>')
def category_news(category_name):
    """Показывает статьи определенной категории"""
    category_articles = [article for article in NEWS_ARTICLES if article['category'] == category_name]

    return render_template('category_news.html',
                           articles=category_articles,
                           category_name=category_name,
                           is_today_article=is_today_article)


if __name__ == '__main__':
    app.run(debug=True)