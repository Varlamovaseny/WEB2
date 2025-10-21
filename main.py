from flask import Flask, render_template, request, redirect, url_for, flash
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Заглушка для базы данных новостей
NEWS_ARTICLES = [
    {
        'id': 1,
        'title': 'Новая статья о котиках',
        'date': '20 декабря 2024',
        'excerpt': 'Сегодня мы расскажем вам о самых интересных породах кошек и их особенностях...',
        'content': '''
            <p>Кошки - удивительные создания, которые уже тысячи лет живут рядом с человеком. 
            В этой статье мы рассмотрим различные породы кошек и их уникальные особенности.</p>

            <h2>Популярные породы кошек</h2>
            <p>Среди самых популярных пород можно выделить мейн-кунов, сиамских, британских 
            и шотландских вислоухих кошек. Каждая порода имеет свои характерные черты 
            и особенности поведения.</p>

            <h2>Уход за кошками</h2>
            <p>Правильный уход за кошкой включает в себя сбалансированное питание, 
            регулярные визиты к ветеринару и, конечно же, любовь и внимание хозяина.</p>
        '''
    },
    {
        'id': 2,
        'title': 'Обновление дизайна сайта',
        'date': '15 декабря 2024',
        'excerpt': 'Мы рады сообщить о полном обновлении дизайна нашего блога...',
        'content': '''
            <p>Дорогие читатели! Мы запустили полностью обновленный дизайн нашего блога, 
            который стал более современным и удобным для использования.</p>

            <h2>Новые возможности</h2>
            <p>Теперь сайт адаптирован для мобильных устройств, добавлена система 
            комментариев и улучшена навигация между разделами.</p>

            <h2>Будущие обновления</h2>
            <p>В ближайших планах - добавление системы рейтинга статей и возможности 
            создавать личные кабинеты для пользователей.</p>
        '''
    },
    {
        'id': 3,
        'title': 'Интересные факты о кошачьем поведении',
        'date': '10 декабря 2024',
        'excerpt': 'Почему кошки мурлыкают и что означают их различные позы?',
        'content': '''
            <p>Кошачье поведение полно загадок. В этой статье мы разберем самые 
            интересные аспекты поведения наших пушистых друзей.</p>

            <h2>Язык тела кошек</h2>
            <p>Положение ушей, хвоста и усов может многое рассказать о настроении кошки. 
            Например, поднятый хвост обычно означает дружелюбие, а распушенный - испуг.</p>

            <h2>Мурлыкание</h2>
            <p>Ученые до сих пор не пришли к единому мнению о том, как именно кошки 
            издают мурлыкающие звуки. Известно, что они могут мурлыкать как от удовольствия, 
            так и от боли или стресса.</p>
        '''
    }
]


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
    return render_template('index.html')


@app.route('/news')
def news():
    return render_template('news.html', articles=NEWS_ARTICLES)


@app.route('/news/<int:id>')
def news_article(id):
    # Ищем статью по ID
    article = next((article for article in NEWS_ARTICLES if article['id'] == id), None)

    if article:
        return render_template('news_article.html', article=article)
    else:
        # Если статья не найдена, показываем заглушку
        return render_template('news_article.html',
                               article={'id': id, 'title': f'Статья {id}',
                                        'date': datetime.now().strftime('%d %B %Y'),
                                        'content': f'<p>Статья с ID {id} находится в разработке. Скоро здесь появится интересный контент!</p>'})


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