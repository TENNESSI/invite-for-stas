# Heartfelt Stories — Flask clone

Этот проект **рендерит страницу-приглашение из экспортированного HTML** (как в файле) и перехватывает отправку формы,
сохраняя ответы в SQLite.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

- http://127.0.0.1:5000/ — приглашение
- http://127.0.0.1:5000/admin — ответы

## Защита админки

```bash
export ADMIN_TOKEN="your-long-token"
```

И заходи: `/admin?token=your-long-token`
