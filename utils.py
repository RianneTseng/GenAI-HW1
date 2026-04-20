import PyPDF2
import base64

def process_file(uploaded_file):
    """Process uploaded PDF or Image into a model-readable format."""
    if uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
        return f"\n[PDF Content]: {text}"
    elif uploaded_file.type in ["image/png", "image/jpeg"]:
        base64_image = base64.b64encode(uploaded_file.read()).decode("utf-8")
        return {
            "type": "image_url", 
            "image_url": {"url": f"data:{uploaded_file.type};base64,{base64_image}"}
        }
    return None