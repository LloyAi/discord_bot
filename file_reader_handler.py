import os
import pdfplumber
from docx import Document

def find_files(base_dir, included_extensions):
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(tuple(included_extensions)):
                yield os.path.join(root, file)

def read_txt_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        return file.read()

def pdf_to_text(file_path):
    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    return full_text

def docx_to_text(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def delete_drawio_files(base_dir):
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.drawio'):
                os.remove(os.path.join(root, file))
                print(f"Deleted {os.path.join(root, file)}")

def add_to_data_dict(file_data, file_name, content):
    if file_name in file_data:
        index = 1
        new_name = f"{file_name}_{index}"
        while new_name in file_data:
            index += 1
            new_name = f"{file_name}_{index}"
        file_data[new_name] = content
    else:
        file_data[file_name] = content

def getFilepath(folderpath):
    base_dir = folderpath  # Replace with the actual path
    file_data = {}

    extensions = [
        ".doc", ".rtf", ".odt", ".tex",
        ".xls", ".xlsx", ".csv", ".ods",
        ".ppt", ".pptx", ".odp",
        ".py", ".java", ".cpp", ".c", ".cs", ".js", ".html", ".css", ".md", ".rb", ".php", ".sh", ".sol", ".go", ".rs",
        ".json", ".yaml", ".yml", ".xml", ".ini", ".cfg", ".conf",
        ".sql", ".db", ".dbf", ".log", ".dat", ".sqlite",
        ".bat", ".ps1", ".vbs", ".ts", ".tsx", ".jsx", ".txt", ".toml"
    ]

    delete_drawio_files(base_dir)

    for file_path in find_files(base_dir, ['.docx']):
        file_name = os.path.basename(file_path)
        content = docx_to_text(file_path)
        add_to_data_dict(file_data, file_name, content)

    for pdf_file_path in find_files(base_dir, ['.pdf']):
        file_name = os.path.basename(pdf_file_path)
        content = pdf_to_text(pdf_file_path)
        add_to_data_dict(file_data, file_name, content)

    for file_path in find_files(base_dir, extensions):
        file_name = os.path.basename(file_path)
        content = read_txt_file(file_path)
        add_to_data_dict(file_data, file_name, content)
    print(f"Processed {len(file_data)} files.")
    return file_data  # Ensure this function returns the file data dictionary
    
   
# if __name__ == '__main__':
#     file_data = getFilepath("Ajna docs") 