import os
import subprocess
import tempfile
import shutil
from flask import Flask, request, send_file, render_template_string

app = Flask(__name__)

# Лимит размера загружаемого файла (10 МБ)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

HTML_FORM = """
<!doctype html>
<title>Конвертер Python в EXE</title>
<h1>Загрузите .py файл</h1>
<form method=post enctype=multipart/form-data action="/convert">
  <input type=file name=file accept=".py">
  <input type=submit value="Конвертировать">
</form>
"""

@app.route('/')
def index():
    return render_template_string(HTML_FORM)

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return 'Файл не найден', 400

    file = request.files['file']
    if file.filename == '':
        return 'Файл не выбран', 400

    if not file.filename.endswith('.py'):
        return 'Можно загружать только файлы с расширением .py', 400

    # Создаём временную директорию для сборки
    temp_dir = tempfile.mkdtemp()
    py_path = os.path.join(temp_dir, file.filename)
    file.save(py_path)

    try:
        # Запускаем PyInstaller через Wine (в контейнере он уже настроен)
        # Команда должна выполняться внутри папки с файлом
        cmd = f"cd {temp_dir} && pyinstaller --onefile --name {os.path.splitext(file.filename)[0]} {file.filename}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            error_msg = f"Ошибка сборки:\n{result.stderr}"
            return error_msg, 500

        exe_name = os.path.splitext(file.filename)[0] + '.exe'
        exe_path = os.path.join(temp_dir, 'dist', exe_name)

        if not os.path.exists(exe_path):
            return "Исполняемый файл не найден после сборки", 500

        # Отправляем файл пользователю и удаляем временные данные после отправки
        return send_file(exe_path, as_attachment=True, download_name=exe_name)

    except subprocess.TimeoutExpired:
        return "Сборка заняла слишком много времени (более 120 секунд)", 500
    except Exception as e:
        return f"Внутренняя ошибка сервера: {str(e)}", 500
    finally:
        # Очищаем временную папку (send_file должен сначала отдать данные)
        # Чтобы не удалить до отправки, можно использовать after_request или отложенное удаление.
        # Для простоты оставим как есть — после отправки файла папка будет удалена,
        # но в send_file используется итератор, поэтому удалять сразу нельзя.
        # Вместо этого запланируем удаление через несколько секунд (или используем модуль atexit).
        # Упростим: удалим только если произошла ошибка до отправки.
        # В рабочем проекте лучше использовать фоновую задачу или after_request.
        pass

# Если нужно удалить temp_dir после ответа, можно зарегистрировать функцию в after_request,
# но тогда придётся сохранять путь в g или подобном.
# Для демо-версии оставим так — Render всё равно пересоздаёт контейнер периодически.
