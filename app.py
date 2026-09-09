from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLUSH & GLOW | Студия эстетики ногтей</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&family=Playfair+Display:ital,wght@0,600;1,400&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #fff5f7;
            --card-bg: rgba(255, 255, 255, 0.85);
            --primary: #f2849e;
            --primary-dark: #d96280;
            --text-dark: #3a2e39;
            --text-muted: #85727e;
            --shadow: 0 15px 35px rgba(242, 132, 158, 0.18);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Montserrat', sans-serif;
            background: linear-gradient(135deg, #fff1f4 0%, #fde4eb 50%, #fff7f9 100%);
            color: var(--text-dark);
            min-height: 100vh;
            overflow-x: hidden;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 24px 8%;
            backdrop-filter: blur(10px);
            background: rgba(255, 255, 255, 0.5);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 4px 15px rgba(242, 132, 158, 0.1);
        }

        .logo {
            font-family: 'Playfair Display', serif;
            font-size: 26px;
            font-weight: 600;
            letter-spacing: 2px;
            color: var(--primary-dark);
            text-decoration: none;
        }

        nav ul {
            list-style: none;
            display: flex;
            gap: 30px;
        }

        nav a {
            text-decoration: none;
            color: var(--text-dark);
            font-weight: 600;
            font-size: 15px;
            transition: color 0.3s ease;
        }

        nav a:hover {
            color: var(--primary-dark);
        }

        .hero {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding: 90px 20px 60px;
            animation: fadeInDown 1s ease-out;
            margin-bottom: 40px;
        }

        .hero h1 {
            font-family: 'Playfair Display', serif;
            font-size: 48px;
            margin-bottom: 18px;
            color: #2b1f28;
        }

        .hero p {
            font-size: 18px;
            color: var(--text-muted);
            max-width: 580px;
            line-height: 1.6;
            margin-bottom: 30px;
        }

        .btn {
            background: linear-gradient(45deg, var(--primary), var(--primary-dark));
            color: white;
            border: none;
            padding: 16px 40px;
            font-size: 15px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 10px 25px rgba(242, 132, 158, 0.4);
            transition: all 0.3s ease;
        }

        .btn:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 15px 30px rgba(242, 132, 158, 0.55);
        }

        .container {
            max-width: 1140px;
            margin: 0 auto;
            padding: 40px 20px 80px;
        }

        .section-title {
            text-align: center;
            font-family: 'Playfair Display', serif;
            font-size: 34px;
            margin-bottom: 45px;
            position: relative;
        }

        .section-title::after {
            content: '';
            display: block;
            width: 60px;
            height: 3px;
            background: var(--primary);
            margin: 12px auto 0;
            border-radius: 2px;
        }

        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
        }

        .card {
            background: var(--card-bg);
            border-radius: 24px;
            padding: 35px 25px;
            box-shadow: var(--shadow);
            border: 1px solid rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(8px);
            transition: transform 0.4s ease, box-shadow 0.4s ease;
            position: relative;
            overflow: hidden;
        }

        .card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(242, 132, 158, 0.3);
        }

        .card h3 {
            font-family: 'Playfair Display', serif;
            font-size: 22px;
            margin-bottom: 12px;
        }

        .card p {
            font-size: 14px;
            color: var(--text-muted);
            line-height: 1.6;
            margin-bottom: 24px;
        }

        .price {
            font-size: 20px;
            font-weight: 700;
            color: var(--primary-dark);
            margin-bottom: 20px;
            display: block;
        }

        .card-btn {
            width: 100%;
            padding: 12px;
            background: transparent;
            border: 1.5px solid var(--primary);
            color: var(--primary-dark);
            border-radius: 30px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .card-btn:hover {
            background: var(--primary);
            color: white;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(58, 46, 57, 0.4);
            backdrop-filter: blur(6px);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .modal-content {
            background: white;
            padding: 40px 30px;
            border-radius: 28px;
            max-width: 420px;
            width: 90%;
            text-align: center;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
            animation: scaleUp 0.3s ease;
        }

        .modal-content input, .modal-content select {
            width: 100%;
            padding: 14px;
            margin: 10px 0;
            border: 1px solid #ffd3de;
            background: #fffbfe;
            border-radius: 12px;
            font-family: inherit;
            outline: none;
        }

        .modal-content input:focus {
            border-color: var(--primary);
        }

        .close-btn {
            float: right;
            cursor: pointer;
            font-size: 22px;
            color: var(--text-muted);
        }

        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes scaleUp {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
    </style>
</head>
<body>

    <header>
        <a href="#home" class="logo">BLUSH & GLOW</a>
        <nav>
            <ul>
                <li><a href="#home">Главная</a></li>
                <li><a href="#services">Услуги</a></li>
                <li><a href="#about">О нас</a></li>
                <li><a href="#contact">Контакты</a></li>
            </ul>
        </nav>
        <button class="btn" style="padding: 10px 24px; font-size: 13px;" onclick="openModal('Общая запись')">Записаться</button>
    </header>

    <section class="hero" id="home">
        <h1>Эстетика ваших рук и ног</h1>
        <p>Идеальное покрытие, премиальные спа-ритуалы и бережный уход в атмосфере легкости и вдохновения.</p>
        <button class="btn" onclick="openModal('Первый визит')">Выбрать время</button>
    </section>

    <div class="container" id="services">
        <h2 class="section-title">Меню услуг</h2>
        <div class="services-grid">
            <div class="card">
                <h3>Smart-педикюр & SPA</h3>
                <p>Аппаратная обработка стоп с органическими маслами, скрабирование и массаж для бархатной кожи.</p>
                <span class="price">3 200 ₽</span>
                <button class="card-btn" onclick="openModal('Smart-педикюр')">Записаться</button>
            </div>

            <div class="card">
                <h3>Комплекс «All Inclusive»</h3>
                <p>Снятие покрытия, комбинированный маникюр, выравнивание базой, цветное гель-лак покрытие и дизайн.</p>
                <span class="price">2 700 ₽</span>
                <button class="card-btn" onclick="openModal('Комплекс All Inclusive')">Записаться</button>
            </div>

            <div class="card">
                <h3>Японский эко-маникюр</h3>
                <p>Натуральный глянец и укрепление слабой ногтевой пластины минеральной пастой и пчелиным воском.</p>
                <span class="price">2 100 ₽</span>
                <button class="card-btn" onclick="openModal('Японский маникюр')">Записаться</button>
            </div>

            <div class="card">
                <h3>Экспресс-маникюр</h3>
                <p>Быстрый уход для поддержания красоты рук: придание формы, обработка кутикулы и легкий массаж.</p>
                <span class="price">1 500 ₽</span>
                <button class="card-btn" onclick="openModal('Экспресс-маникюр')">Записаться</button>
            </div>

            <div class="card">
                <h3>Наращивание ногтей</h3>
                <p>Создание идеальной длины и формы с использованием современных материалов и техник.</p>
                <span class="price">от 3 500 ₽</span>
                <button class="card-btn" onclick="openModal('Наращивание ногтей')">Записаться</button>
            </div>

            <div class="card">
                <h3>Дизайн любой сложности</h3>
                <p>Воплощение ваших идей в уникальных рисунках, градиентах и акцентах на ваших ногтях.</p>
                <span class="price">от 500 ₽</span>
                <button class="card-btn" onclick="openModal('Дизайн ногтей')">Записаться</button>
            </div>
        </div>
    </div>

    <section class="container" id="about">
        <h2 class="section-title">О нас</h2>
        <p style="text-align: center; max-width: 800px; margin: 0 auto 40px; font-size: 16px; color: var(--text-muted);">
            BLUSH & GLOW — это больше, чем просто студия эстетики ногтей. Это место, где красота встречается с заботой.
            Мы верим, что каждая женщина заслуживает идеального ухода, поэтому используем только премиальные материалы,
            передовые техники и создаем атмосферу, в которой вы можете расслабиться и почувствовать себя особенной.
            Наши мастера — это настоящие художники, готовые воплотить в жизнь любую вашу идею, будь то классический маникюр
            или смелый авторский дизайн. Приходите и убедитесь сами!
        </p>
    </section>

    <section class="container" id="contact">
        <h2 class="section-title">Контакты</h2>
        <div style="text-align: center; font-size: 16px; line-height: 1.8;">
            <p><strong>Адрес:</strong> г. Москва, ул. Красоты, д. 10, офис 3</p>
            <p><strong>Телефон:</strong> <a href="tel:+74951234567" style="color: var(--primary-dark); text-decoration: none;">+7 (495) 123-45-67</a></p>
            <p><strong>Email:</strong> <a href="mailto:info@blushandglow.ru" style="color: var(--primary-dark); text-decoration: none;">info@blushandglow.ru</a></p>
            <p style="margin-top: 20px;">Мы работаем для вас ежедневно с 10:00 до 21:00.</p>
        </div>
    </section>

    <footer style="background: var(--primary-dark); color: white; text-align: center; padding: 30px 20px; margin-top: 60px;">
        <p>&copy; 2026 BLUSH & GLOW. Все права защищены.</p>
        <p style="font-size: 14px; margin-top: 10px;">С любовью к вашим рукам и ногам.</p>
    </footer>

    <!-- Модальное окно записи -->
    <div class="modal" id="bookingModal">
        <div class="modal-content">
            <span class="close-btn" onclick="closeModal()">&times;</span>
            <h3 style="margin-bottom: 15px; font-family: 'Playfair Display', serif;">Онлайн-запись</h3>
            <p id="serviceName" style="color: var(--primary-dark); font-weight: 600; margin-bottom: 15px;"></p>
            <input type="text" id="clientName" placeholder="Ваше имя" required>
            <input type="tel" id="clientPhone" placeholder="+7 (999) 000-00-00" required>
            <button class="btn" style="width: 100%; margin-top: 10px;" onclick="submitBooking()">Подтвердить запись</button>
        </div>
    </div>

    <script>
        let currentService = '';

        function openModal(service) {
            currentService = service;
            document.getElementById('serviceName').innerText = service;
            document.getElementById('bookingModal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('bookingModal').style.display = 'none';
        }

        window.onclick = function(event) {
            const modal = document.getElementById('bookingModal');
            if (event.target === modal) {
                closeModal();
            }
        }

        // Плавная прокрутка для навигации
        document.querySelectorAll('nav a').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();

                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });

        function submitBooking() {
            const name = document.getElementById('clientName').value;
            const phone = document.getElementById('clientPhone').value;

            if (!name || !phone) {
                alert('Пожалуйста, заполните имя и телефон.');
                return;
            }

            fetch('/api/book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service: currentService, name: name, phone: phone })
            })
            .then(res => res.json())
            .then(data => {
                alert('Спасибо, ' + name + '! Мы свяжемся с вами в течение 10 минут.');
                closeModal();
                document.getElementById('clientName').value = '';
                document.getElementById('clientPhone').value = '';
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/book', methods=['POST'])
def book():
    data = request.get_json()
    print(f"[Новая заявка] Услуга: {data.get('service')} | Клиент: {data.get('name')} | Телефон: {data.get('phone')}")
    return jsonify({"status": "success", "message": "Запись принята!"})

if __name__ == '__main__':
    print("✨ Сайт студии запущен: http://127.0.0.1:5000")
    app.run(debug=True)
