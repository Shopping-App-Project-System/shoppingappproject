from flask import Flask, request, render_template_string, url_for
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# 上傳資料夾
UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 允許的副檔名
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# 確保資料夾存在
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def upload_file():
    image_url = None
    message = ""

    if request.method == "POST":
        file = request.files.get("avatar")

        if file is None:
            message = "沒有收到檔案"
        elif file.filename == "":
            message = "你沒有選擇檔案"
        elif not allowed_file(file.filename):
            message = "只允許上傳 png、jpg、jpeg、gif"
        else:
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            # 產生給前端顯示的路徑
            image_url = url_for("static", filename=f"uploads/{filename}")
            message = "上傳成功"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="UTF-8">
        <title>Flask 圖片上傳</title>
        <style>
            body {
                font-family: Arial, "Microsoft JhengHei", sans-serif;
                max-width: 700px;
                margin: 50px auto;
                padding: 20px;
            }
            .box {
                padding: 20px;
                border: 1px solid #ccc;
                border-radius: 12px;
            }
            img {
                margin-top: 20px;
                max-width: 300px;
                border-radius: 12px;
                border: 1px solid #ddd;
            }
            .msg {
                margin-top: 15px;
                color: #333;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>上傳圖片</h1>

            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="avatar">
                <button type="submit">上傳</button>
            </form>

            {% if message %}
                <div class="msg">{{ message }}</div>
            {% endif %}

            {% if image_url %}
                <h3>上傳後顯示：</h3>
                <img src="{{ image_url }}" alt="uploaded image">
                <p>{{ image_url }}</p>
            {% endif %}
        </div>
    </body>
    </html>
    """, image_url=image_url, message=message)


if __name__ == "__main__":
    app.run()