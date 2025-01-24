from flask import Flask, request, render_template, jsonify, url_for
import os
import sqlite3
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)
UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
db_name = "document_index.db"

# Configuración de la base de datos
conn = sqlite3.connect(db_name, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS document_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT,
    page_number INTEGER,
    content TEXT,
    UNIQUE(file_name, page_number)
)
""")
conn.commit()


def index_pdf(file_path, file_name):
    """Extraer texto de un PDF y guardarlo en la base de datos"""
    reader = PdfReader(file_path)
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        cursor.execute(
            "INSERT OR IGNORE INTO document_index (file_name, page_number, content) VALUES (?, ?, ?)",
            (file_name, page_number, text)
        )
    conn.commit()


def index_docx(file_path, file_name):
    """Extraer texto de un archivo .docx y guardarlo en la base de datos"""
    doc = Document(file_path)
    text = '\n'.join([para.text for para in doc.paragraphs])
    cursor.execute(
        "INSERT OR IGNORE INTO document_index (file_name, page_number, content) VALUES (?, ?, ?)",
        (file_name, 1, text)
    )
    conn.commit()


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        files = request.files.getlist("files")
        folder_files = request.files.getlist("folder")

        if not files and not folder_files:
            return jsonify({"message": "No se seleccionaron archivos o carpetas."}), 400

        # Procesar archivos
        for file in files:
            if file:
                file_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(file_path)
                if file.filename.endswith(".pdf"):
                    index_pdf(file_path, file.filename)
                elif file.filename.endswith(".docx"):
                    index_docx(file_path, file.filename)

        # Procesar carpetas
        for file in folder_files:
            if file:
                relative_path = file.filename
                file_path = os.path.join(UPLOAD_FOLDER, relative_path)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                if relative_path.endswith(".pdf"):
                    index_pdf(file_path, relative_path)
                elif relative_path.endswith(".docx"):
                    index_docx(file_path, relative_path)

        return jsonify({"message": "Archivos y carpetas cargados e indexados con éxito."}), 200

    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search():
    keyword = request.args.get("keyword", "")
    if keyword:
        query = "SELECT file_name, page_number, content FROM document_index WHERE content LIKE ?"
        cursor.execute(query, (f"%{keyword}%",))
        results = cursor.fetchall()
        return jsonify([{
            "file_name": file_name,
            "page_number": page_number,
            "content": content[:200]
        } for file_name, page_number, content in results])
    return jsonify([])


@app.route("/view_pdf", methods=["GET"])
def view_pdf():
    file_name = request.args.get("file_name")
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if os.path.exists(file_path):
        return jsonify({"url": url_for('static', filename=f"uploaded_files/{file_name}")})
    return jsonify({"message": "Archivo no encontrado."}), 404


if __name__ == "__main__":
    app.run(debug=True)
