from flask import Flask, render_template, request, redirect, url_for, flash
import re
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Заглушка для базы данных новостей
NEWS_ARTICLES = [
    {
        'id': 1,
        'title': 'Новая картина Бэнкси',
        'date': date.today().strftime('%d %B %Y'),  # Сегодняшняя дата
        'excerpt': 'пока не нарисована...',
        'content': ''' <p>Может завтра нарисует?</p>
            
        '''
    },
    {
        'id': 2,
        'title': 'Я новость',
        'date': '25 марта 2025',
        'excerpt': 'не открывай меня',
        'content': ''' <p>Да блин нуууу :((( </p>
        '''
    },
    {
        'id': 3,
        'title': 'Новый показ Victoria`s Secret',
        'date': date.today().strftime('%d %B %Y'),  # Сегодняшняя дата
        'excerpt': 'Возвращение легендарных ангелов на подиум',
        'content': ''' <p>Красотки, умницы, молодцы! Так держать девчонки!</p>
        '''
    }
]

def is_today_article(article_date):
    """Проверяет, является ли дата статьи сегодняшней"""
    try:
        # Парсим дату из строки (формат: "20 December 2024")
        article_datetime = datetime.strptime(article_date, '%d %B %Y')
        return article_datetime.date() == date.today()
    except ValueError:
        return False

def validate_email(email):
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_form(name, email, message):
    """Валидация формы обратной связи"""
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

@app.route('/')
def index():
    # На главной показываем только сегодняшние статьи
    today_articles = [article for article in NEWS_ARTICLES if is_today_article(article['date'])]
    return render_template('index.html', today_articles=today_articles)

@app.route('/news')
def news():
    return render_template('news.html', articles=NEWS_ARTICLES, is_today_article=is_today_article)

@app.route('/news/<int:id>')
def news_article(id):
    # Ищем статью по ID
    article = next((article for article in NEWS_ARTICLES if article['id'] == id), None)

    if article:
        return render_template('news_article.html', article=article, is_today_article=is_today_article)
    else:
        # Если статья не найдена, показываем заглушку
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

if __name__ == '__main__':
    app.run(debug=True)