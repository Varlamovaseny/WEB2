from flask import Flask, render_template, request, redirect, url_for, flash
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

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
    return render_template('base.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        # Валидируем данные
        errors = validate_form(name, email, message)
        
        if errors:
            # Если есть ошибки, показываем форму снова с сообщениями об ошибках
            return render_template('feedback.html', 
                                 name=name, 
                                 email=email, 
                                 message=message, 
                                 errors=errors)
        else:
            # Если данные валидны, сохраняем и показываем страницу успеха
            flash('Сообщение успешно отправлено!', 'success')
            return render_template('feedback_success.html', 
                                 name=name, 
                                 email=email, 
                                 message=message)
    
    # GET запрос - показываем пустую форму
    return render_template('feedback.html')

if __name__ == '__main__':
    app.run(debug=True)