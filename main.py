from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import re
from datetime import datetime, date, timedelta
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news_blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация SQLAlchemy
db = SQLAlchemy(app)


# Функция для получения текущей даты в правильном часовом поясе
def get_local_datetime():
    """Возвращает текущую дату и время в локальном часовом поясе"""
    return datetime.now()


# Модель User
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    hashed_password = db.Column(db.String(200), nullable=False)
    created_date = db.Column(db.DateTime, default=get_local_datetime)

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
    created_date = db.Column(db.DateTime, default=get_local_datetime)  # ИСПРАВЛЕНО: используем локальную функцию
    category = db.Column(db.String(50), nullable=False, default='Разное')
    excerpt = db.Column(db.Text)

    # Внешний ключ для связи с User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Связь "один ко многим" с Comment
    comments = db.relationship('Comment', backref='article', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Article {self.title}>'


# Модель Comment
class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=get_local_datetime)  # ИСПРАВЛЕНО: используем локальную функцию
    author_name = db.Column(db.String(100), nullable=False)

    # Внешний ключ для связи с Article
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)

    def __repr__(self):
        return f'<Comment {self.id} by {self.author_name}>'


# Создание таблиц при запуске
with app.app_context():
    # Пересоздаем все таблицы
    try:
        db.drop_all()
        db.create_all()
        print("✅ Таблицы успешно созданы")
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")

    # Создаем тестовых пользователей, если их нет
    if not User.query.first():
        print("🔄 Создаем тестовых пользователей...")
        users_to_create = [
            {'name': 'Петя Пупкин', 'email': 'petya@meowblog.ru'},
            {'name': 'Кай Ангел', 'email': 'kai@meowblog.ru'},
            {'name': 'Людка Тетка', 'email': 'lyudka@meowblog.ru'},
            {'name': 'Кузя Лакомкин', 'email': 'kuzya@meowblog.ru'}
        ]

        for user_data in users_to_create:
            if not User.query.filter_by(email=user_data['email']).first():
                user = User(name=user_data['name'], email=user_data['email'])
                user.set_password('password123')
                db.session.add(user)

        try:
            db.session.commit()
            print("✅ Пользователи созданы")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка при создании пользователей: {e}")

        # Создаем демо-статьи в БД
        users = User.query.all()
        if users and not Article.query.first():
            print("🔄 Создаем тестовые статьи...")
            # Статьи с СЕГОДНЯШНЕЙ датой (используем локальное время)
            article1 = Article(
                title='Новая картина Бэнкси',
                text='Может завтра нарисует?',
                category='Искусство',
                excerpt='пока не нарисована...',
                user_id=users[0].id
            )
            article2 = Article(
                title='Я новость',
                text='Да блин нуууу :(((',
                category='Разное',
                excerpt='не открывай меня',
                user_id=users[1].id if len(users) > 1 else users[0].id
            )
            article3 = Article(
                title='Новый показ Victoria`s Secret',
                text='Красотки, умницы, молодцы! Так держать девчонки!',
                category='Мода',
                excerpt='Возвращение легендарных ангелов на подиум',
                user_id=users[2].id if len(users) > 2 else users[0].id
            )
            # Статья со ВЧЕРАШНЕЙ датой для теста
            yesterday = get_local_datetime() - timedelta(days=1)
            article4 = Article(
                title='Старая статья',
                text='Это старая статья для тестирования',
                category='Разное',
                excerpt='старая статья...',
                user_id=users[0].id,
                created_date=yesterday  # Вчерашняя дата
            )
            db.session.add(article1)
            db.session.add(article2)
            db.session.add(article3)
            db.session.add(article4)

            try:
                db.session.commit()
                print("✅ Статьи созданы")

                # Создаем тестовые комментарии
                print("🔄 Создаем тестовые комментарии...")
                comment1 = Comment(
                    text='Отличная статья! Жду продолжения.',
                    author_name='Анонимный читатель',
                    article_id=article1.id
                )
                comment2 = Comment(
                    text='Интересно, а когда будет новая картина?',
                    author_name='Любитель искусства',
                    article_id=article1.id
                )
                comment3 = Comment(
                    text='Очень смешно 😄',
                    author_name='Весельчак',
                    article_id=article2.id
                )

                db.session.add(comment1)
                db.session.add(comment2)
                db.session.add(comment3)
                db.session.commit()
                print("✅ Комментарии созданы")

            except Exception as e:
                db.session.rollback()
                print(f"❌ Ошибка при создании статей/комментариев: {e}")

# Обновленные категории
CATEGORIES = [
    'Искусство',
    'Мода',
    'Разное',
    'Политика'
]


# Вспомогательная функция для преобразования статьи из БД в формат для шаблонов
def article_to_dict(article):
    return {
        'id': article.id,
        'title': article.title,
        'date': article.created_date.strftime('%d %B %Y'),
        'excerpt': article.excerpt or article.text[:100] + '...',
        'content': f'<p>{article.text}</p>',
        'author_id': article.user_id,
        'category': article.category
    }


# Вспомогательная функция для преобразования комментария из БД в формат для шаблонов
def comment_to_dict(comment):
    return {
        'id': comment.id,
        'text': comment.text,
        'date': comment.date.strftime('%d.%m.%Y %H:%M'),
        'author_name': comment.author_name,
        'article_id': comment.article_id
    }


# Обновленные авторы (для совместимости со старым кодом)
AUTHORS = [
    {'id': 1, 'name': 'Петя Пупкин', 'email': 'petya@meowblog.ru'},
    {'id': 2, 'name': 'Кай Ангел', 'email': 'kai@meowblog.ru'},
    {'id': 3, 'name': 'Людка Тетка', 'email': 'lyudka@meowblog.ru'},
    {'id': 4, 'name': 'Кузя Лакомкин', 'email': 'kuzya@meowblog.ru'}
]


# ИСПРАВЛЕННАЯ функция проверки сегодняшней статьи
def is_today_article(article_date):
    """
    Проверяет, является ли дата статьи сегодняшней.
    Принимает объект datetime или строку с датой.
    """
    try:
        # Если передана строка (из article_to_dict)
        if isinstance(article_date, str):
            # Парсим строку в формате "20 December 2024"
            article_datetime = datetime.strptime(article_date, '%d %B %Y')
            return article_datetime.date() == date.today()

        # Если передан объект datetime (напрямую из БД)
        elif isinstance(article_date, datetime):
            return article_date.date() == date.today()

        return False

    except (ValueError, AttributeError) as e:
        print(f"Ошибка при проверке даты: {e}")
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


def validate_comment_form(author_name, text):
    errors = {}

    if not author_name.strip():
        errors['author_name'] = 'Имя обязательно для заполнения'
    elif len(author_name.strip()) < 2:
        errors['author_name'] = 'Имя должно содержать минимум 2 символа'

    if not text.strip():
        errors['text'] = 'Текст комментария обязателен для заполнения'
    elif len(text.strip()) < 5:
        errors['text'] = 'Комментарий должен содержать минимум 5 символов'

    return errors


# Маршруты
@app.route('/')
def index():
    # Получаем статьи из БД
    articles = Article.query.order_by(Article.created_date.desc()).all()
    today_articles = [article for article in articles if is_today_article(article.created_date)]
    return render_template('index.html',
                           today_articles=[article_to_dict(article) for article in today_articles],
                           current_date=date.today())


@app.route('/news')
def news():
    # Получаем все статьи из БД
    articles = Article.query.order_by(Article.created_date.desc()).all()
    articles_dict = [article_to_dict(article) for article in articles]

    # Отладочная информация
    print("=== ОТЛАДОЧНАЯ ИНФОРМАЦИЯ ===")
    print(f"Сегодня: {date.today()}")
    print(f"Всего статей: {len(articles)}")
    for article in articles:
        print(
            f"Статья '{article.title}': {article.created_date.date()} (сегодняшняя: {is_today_article(article.created_date)})")
    print("=============================")

    return render_template('news.html',
                           articles=articles_dict,
                           is_today_article=is_today_article,
                           current_date=date.today())


@app.route('/news/<int:id>', methods=['GET', 'POST'])
def news_article(id):
    article = Article.query.get(id)

    if request.method == 'POST':
        # Обработка формы комментария
        author_name = request.form.get('author_name', '').strip()
        text = request.form.get('text', '').strip()

        print(f"🔄 Получен комментарий от {author_name}: {text[:50]}...")

        errors = validate_comment_form(author_name, text)

        if errors:
            # Если есть ошибки, показываем статью снова с ошибками
            author = next((author for author in AUTHORS if author['id'] == article.user_id), None)
            comments = Comment.query.filter_by(article_id=id).order_by(Comment.date.desc()).all()
            return render_template('news_article.html',
                                   article=article_to_dict(article),
                                   author=author,
                                   comments=[comment_to_dict(comment) for comment in comments],
                                   is_today_article=is_today_article,
                                   current_date=date.today(),
                                   errors=errors,
                                   author_name=author_name,
                                   text=text)
        else:
            # Создаем новый комментарий
            try:
                new_comment = Comment(
                    text=text,
                    author_name=author_name,
                    article_id=id
                )

                db.session.add(new_comment)
                db.session.commit()

                print(f"✅ Комментарий сохранен в БД, ID: {new_comment.id}")
                flash('Комментарий успешно добавлен!', 'success')
                return redirect(url_for('news_article', id=id))

            except Exception as e:
                db.session.rollback()
                print(f"❌ Ошибка при сохранении комментария: {e}")
                flash(f'Ошибка при добавлении комментария: {str(e)}', 'error')
                return redirect(url_for('news_article', id=id))

    # GET запрос - показываем статью и комментарии
    if article:
        author = next((author for author in AUTHORS if author['id'] == article.user_id), None)
        # Получаем все комментарии к статье
        comments = Comment.query.filter_by(article_id=id).order_by(Comment.date.desc()).all()

        print(f"📝 Статья {id}: {len(comments)} комментариев")

        return render_template('news_article.html',
                               article=article_to_dict(article),
                               author=author,
                               comments=[comment_to_dict(comment) for comment in comments],
                               is_today_article=is_today_article,
                               current_date=date.today())
    else:
        return render_template('news_article.html',
                               article={'id': id, 'title': f'Статья {id}',
                                        'date': datetime.now().strftime('%d %B %Y'),
                                        'content': f'<p>Статья с ID {id} находится в разработке. Скоро здесь появится интересный контент!</p>'},
                               comments=[],
                               is_today_article=is_today_article,
                               current_date=date.today())


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

        print(f"🔄 Создание статьи: {title}")

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
            # СОХРАНЯЕМ СТАТЬЮ В БАЗУ ДАННЫХ
            try:
                # Находим пользователя по ID
                user = User.query.get(int(author_id))
                if not user:
                    flash('Автор не найден!', 'error')
                    return redirect(url_for('create_article'))

                # Создаем новую статью
                new_article = Article(
                    title=title,
                    text=content,
                    excerpt=excerpt or content[:100] + '...',
                    category=category,
                    user_id=int(author_id)
                    # created_date автоматически установится из default=get_local_datetime
                )

                db.session.add(new_article)
                db.session.commit()

                print(f"✅ Статья сохранена в БД, ID: {new_article.id}")
                flash('Статья успешно создана!', 'success')
                return redirect(url_for('news_article', id=new_article.id))

            except Exception as e:
                db.session.rollback()
                print(f"❌ Ошибка при сохранении статьи: {e}")
                flash(f'Ошибка при создании статьи: {str(e)}', 'error')
                return redirect(url_for('create_article'))

    return render_template('create_article.html',
                           authors=AUTHORS,
                           categories=CATEGORIES)


# Редактирование статьи
@app.route('/edit-article/<int:id>', methods=['GET', 'POST'])
def edit_article(id):
    article = Article.query.get(id)

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
                                   article=article_to_dict(article),
                                   title=title,
                                   content=content,
                                   author_id=author_id,
                                   category=category,
                                   excerpt=excerpt,
                                   errors=errors,
                                   authors=AUTHORS,
                                   categories=CATEGORIES)
        else:
            try:
                # Обновляем статью в БД
                article.title = title
                article.text = content
                article.excerpt = excerpt or content[:100] + '...'
                article.category = category
                article.user_id = int(author_id)

                db.session.commit()

                flash('Статья успешно обновлена!', 'success')
                return redirect(url_for('news_article', id=id))

            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при обновлении статьи: {str(e)}', 'error')
                return redirect(url_for('edit_article', id=id))

    # GET запрос - показываем форму с текущими данными
    return render_template('edit_article.html',
                           article=article_to_dict(article),
                           title=article.title,
                           content=article.text,
                           author_id=article.user_id,
                           category=article.category,
                           excerpt=article.excerpt,
                           authors=AUTHORS,
                           categories=CATEGORIES)


# Удаление статьи
@app.route('/delete-article/<int:id>')
def delete_article(id):
    try:
        article = Article.query.get(id)

        if article:
            db.session.delete(article)
            db.session.commit()
            flash('Статья успешно удалена!', 'success')
        else:
            flash('Статья не найдена!', 'error')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении статьи: {str(e)}', 'error')

    return redirect(url_for('news'))


# Демонстрация работы с моделями
@app.route('/demo-db')
def demo_db():
    """Страница для демонстрации работы с моделями"""

    # Получаем всех пользователей и статьи из БД
    users = User.query.all()
    articles = Article.query.all()
    comments = Comment.query.all()

    return render_template('demo_db.html', users=users, articles=articles, comments=comments)


# Маршрут для фильтрации по категориям
@app.route('/category/<category_name>')
def category_news(category_name):
    """Показывает статьи определенной категории"""
    articles = Article.query.filter_by(category=category_name).order_by(Article.created_date.desc()).all()

    return render_template('category_news.html',
                           articles=[article_to_dict(article) for article in articles],
                           category_name=category_name,
                           is_today_article=is_today_article,
                           current_date=date.today())


if __name__ == '__main__':
    app.run(debug=True)