from flask import Flask, request, render_template, send_file 
import os 
import pdfplumber
import docx 
import csv
from werkzeug.utils import secure_filename 
import google.generativeai as genai
from fpdf import FPDF 


# Set your API Key 
os.environ["GOOGLE_API_KEY"] = "AIzaSyAM2Y8W5a6-OOPa7rLU6TjqfV2gfhosmUk"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.5-pro")

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads/"
app.config["RESULTS_FOLDER"] = "results/"
app.config["ALLOWED_EXTENSIONS"] = {'pdf','txt','docx'}

# custom functions 
def allowed_file(filename):
    # burhan.pdf in this filename burhan is at index zero and pdf at index 1 so i want to cheq index 1
    return "." in filename and filename.rsplit(".",1)[1].lower() in app.config["ALLOWED_EXTENSIONS"] # make pdf, txt ot doc extension in lowercase before passing into code
    
def extract_text_from_file(file_path):
    # burhan.docx
    ext = file_path.rsplit(".",1)[1].lower()
    if ext == "pdf":
        with pdfplumber.open(file_path) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages])
        return text
    elif ext == "docx":
        doc__ = docx.Document(file_path)
        text = "".join([para.text for para in doc.paragraphs])
        return text 
    elif ext == "txt":
        with open(file_path, "r") as file:
            return file.read()
    else:
        return None 

def  Question_mcqs_generator(input_text, num_questions):
    prompt = f""" 
    You are an AI Assistant helping the user generate multiple-choice questions (MCQs) based on the following
    '{input_text}'
    Please generate {num_questions} MCQs from the text. Each Question should have:
    - A clear question 
    - Four answer options (labeled A, B, C, D)
    - The Correct answer clearly indicated
    Format:
    ## MCQ
    Question: [question]
    A) [option A]
    B) [option B]
    C) [option C]
    D) [option D]
    Correct Answer: [correct option]
    """
    response = model.generate_content(prompt).text.strip()
    return response

def save_mcqs_to_file(mcqs, filename):
    results_path = os.path.join(app.config["RESULTS_FOLDER"], filename)
    with open(results_path,'w') as file:
        file.write(mcqs)
    return results_path


def create_pdf(mcqs, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    for mcq in mcqs.split("## MCQ"):
        if mcq.strip():
            pdf.multi_cell(0,10, mcq.strip())
            pdf.ln(5)
            
    pdf_path = os.path.join(app.config["RESULTS_FOLDER"], filename)
    pdf.output(pdf_path)
    return pdf_path
        
    

# python main 
@app.route("/")
def index():
    return render_template("index.html")


# python main 
@app.route("/generate", methods=["POST"])
def generate():
    if 'file' not in request.files:
        return "File must be sumbitted"
    file = request.files["file"]
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        
        # pdf, txt, docx
        text = extract_text_from_file(file_path)
        
        if text:
            num_questions = int(request.form["num_questions"])
            mcqs = Question_mcqs_generator(text, num_questions)
            
            # save the generated MCQs to a file
            txt_filename = f"generated_mcqs_{filename.rsplit('.',1)[0]}.txt"
            pdf_filename = f"generated_mcqs_{filename.rsplit('.',1)[0]}.pdf"
            save_mcqs_to_file(mcqs, txt_filename)
            create_pdf(mcqs, pdf_filename)
            
            # Display and allow downloading
            # print(f"\n\n{mcqs}")
            
            return render_template("results.html", mcqs=mcqs, txt_filename=txt_filename, pdf_filename=pdf_filename)
        return "Invalid file format"

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(app.config["RESULTS_FOLDER"], "output.pdf")  # Ensure this is a file
    return send_file(file_path, as_attachment=True)


if __name__ =="__main__":
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])
    if not os.path.exists(app.config["RESULTS_FOLDER"]):
        os.makedirs(app.config["RESULTS_FOLDER"])        
    app.run(debug=True)