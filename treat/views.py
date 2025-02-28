import google.generativeai as genai
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
import json
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import numpy as np
# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def get_treatment_recommendations(disease_name):
    prompt = f"""
    Provide a detailed treatment plan for the plant disease: {disease_name}
    Include the following information:
    1. Symptoms (list 3-4 main symptoms)
    2. Causes (list 2-3 main causes)
    3. Treatment steps (list 3-4 steps)
    4. Prevention tips (list 3-4 tips)
    
    Format your response exactly like this example:
    {{
        "disease_name": "{disease_name}",
        "symptoms": [
            "Yellow spots on leaves",
            "Wilting of plants",
            "Brown lesions on stems"
        ],
        "causes": [
            "Fungal infection",
            "High humidity",
            "Poor air circulation"
        ],
        "treatment_steps": [
            "Remove infected plant parts",
            "Apply appropriate fungicide",
            "Improve air circulation"
        ],
        "prevention_tips": [
            "Use resistant varieties",
            "Maintain proper spacing",
            "Avoid overhead watering"
        ]
    }}
    """
    
    response = model.generate_content(prompt)
    
    try:
        # Clean the response text to ensure it's valid JSON
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:-3]  # Remove ```json and ``` if present
        
        treatment_plan = json.loads(cleaned_text)
        
        # Validate the structure
        required_keys = ['disease_name', 'symptoms', 'causes', 'treatment_steps', 'prevention_tips']
        for key in required_keys:
            if key not in treatment_plan:
                treatment_plan[key] = []
                
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response.text}")
        
        # Create a structured response from the raw text
        lines = response.text.split('\n')
        treatment_plan = {
            "disease_name": disease_name,
            "symptoms": [line.strip('- ') for line in lines if 'symptom' in line.lower()],
            "causes": [line.strip('- ') for line in lines if 'cause' in line.lower()],
            "treatment_steps": [line.strip('- ') for line in lines if 'treat' in line.lower()],
            "prevention_tips": [line.strip('- ') for line in lines if 'prevent' in line.lower()]
        }
        
        # Ensure we have at least some content
        for key in treatment_plan:
            if not treatment_plan[key] or len(treatment_plan[key]) == 0:
                treatment_plan[key] = ["Please consult with a local agricultural expert for detailed information."]
    
    return treatment_plan

def create_pdf(treatment_plan, disease_image):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.green,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.darkgreen,
        spaceAfter=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    
    caption_style = ParagraphStyle(
        'CustomCaption',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=1  # Center alignment
    )

    try:
        # Title
        story.append(Paragraph(f"🌱 Disease Name: {treatment_plan['disease_name']}", title_style))
        story.append(Spacer(1, 20))

        # Image (commented out due to accessibility issues)
        # try:
        #     img = Image(disease_image, width=4*inch, height=3*inch)
        #     story.append(img)
        #     story.append(Spacer(1, 20))



        # except Exception as img_error:
        #     print(f"Error adding image: {str(img_error)}")
        #     story.append(Paragraph("Image not available", body_style))


        # Symptoms
        story.append(Paragraph("🔍 Symptoms:", heading_style))
        for symptom in treatment_plan.get('symptoms', []):
            story.append(Paragraph(f"✅ {symptom}", body_style))
        story.append(Spacer(1, 20))

        # Causes
        story.append(Paragraph("⚠️ Causes:", heading_style))
        for cause in treatment_plan.get('causes', []):
            story.append(Paragraph(f"• {cause}", body_style))
        story.append(Spacer(1, 20))

        # Treatment Steps
        story.append(Paragraph("🛠 Treatment Steps:", heading_style))
        for i, step in enumerate(treatment_plan.get('treatment_steps', []), 1):
            story.append(Paragraph(f"{i}. {step}", body_style))
        story.append(Spacer(1, 20))

        # Prevention Tips
        story.append(Paragraph("🚜 Prevention Tips:", heading_style))
        for tip in treatment_plan.get('prevention_tips', []):
            story.append(Paragraph(f"✔ {tip}", body_style))
        story.append(Spacer(1, 20))

        # QR Code
        try:
            qr_code = generate_qr_code("https://example.com/video-tutorial")
            qr_img = Image(BytesIO(qr_code), width=2*inch, height=2*inch)
            story.append(qr_img)
            story.append(Paragraph("Scan this QR code 📲 to watch how to treat the disease", caption_style))
        except Exception as qr_error:
            print(f"Error generating QR code: {str(qr_error)}")
            story.append(Paragraph("QR Code not available", body_style))

        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error in create_pdf: {str(e)}")
        print(traceback.format_exc())
        raise
def disease_input(request):
    return render(request, 'disease.html')   
def pest_input(request):
    return render(request, 'pest.html')     

def treatment_recommendation(request):
    disease_name = request.GET.get('disease', 'Unknown Disease')
    
    # Get treatment recommendations from Gemini
    treatment_plan = get_treatment_recommendations(disease_name)
    
    # For demonstration, using a placeholder image
    disease_image = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/ai%20recomondation-QUFZgxC58cN6TWsieh3agtREuKEIkh.png"
    
    context = {
        'treatment_plan': treatment_plan,
        'disease_image': disease_image,
    }
    
    return render(request, 'treatment_recommendation.html', context)

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

import traceback
from django.http import JsonResponse

def download_pdf(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            treatment_plan = data.get('treatment_plan')
            disease_image = data.get('disease_image')
            
            if not treatment_plan or not disease_image:
                return JsonResponse({"error": "Missing required data"}, status=400)
            
            print("Treatment plan:", treatment_plan)  # Debug print
            print("Disease image:", disease_image)  # Debug print
            
            pdf_buffer = create_pdf(treatment_plan, disease_image)
            
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{treatment_plan["disease_name"]}_treatment.pdf"'
            return response
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            print(traceback.format_exc())  # This will print the full traceback
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

def get_treatment_pest(pest_name):
    prompt = f"""
    Provide a detailed treatment plan for the pest: {pest_name}
    Include the following information:
    1. Attack reasons (list 2-3 main reasons)
    2. Prevention tips (list 3-4 tips)
    3. Natural remedies (list 2-3 remedies)
    4. Chemical control (list 2-3 options)
    
    Format your response exactly like this example:
    {{
        "pest_name": "{pest_name}",
        "attack_reasons": [
            "Warm and humid conditions",
            "Overuse of nitrogen-rich fertilizers"
        ],
        "prevention_tips": [
            "Encourage beneficial insects",
            "Avoid excessive nitrogen fertilizers"
        ],
        "natural_remedies": [
            "Spray neem oil",
            "Use a homemade garlic spray"
        ],
        "chemical_control": [
            "Apply insecticidal soap",
            "Use pyrethrin-based insecticides"
        ],
        "image": "pest_image.jpg",
        "fertilization_strategies": [
            "Use balanced fertilizers during the growing season",
            "Apply organic compost to improve soil health",
            "Follow soil test recommendations for nutrient application"
        ]

    }}
    """
    
    response = model.generate_content(prompt)
    
    try:
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:-3]  # Remove ```json and ``` if present
        
        treatment_plan = json.loads(cleaned_text)
        
        # Validate the structure
        required_keys = ['pest_name', 'attack_reasons', 'prevention_tips', 'natural_remedies', 'chemical_control']
        for key in required_keys:
            if key not in treatment_plan:
                treatment_plan[key] = []
                
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response.text}")
        
        # Fallback to a default response
        treatment_plan = {
            "pest_name": pest_name,
            "attack_reasons": ["No data available."],
            "prevention_tips": ["No prevention tips found."],
            "natural_remedies": ["No remedies available."],
            "chemical_control": ["No chemical treatment recommended."],
            "pest_image": "default_pest.jpg"
        }
    
    return treatment_plan


def pest_pdf(treatment_plan, pest_image):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.green,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.darkgreen,
        spaceAfter=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    
    caption_style = ParagraphStyle(
        'CustomCaption',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=1  # Center alignment
    )

    try:
        # Title
        story.append(Paragraph(f"🌱 Pest Name: {treatment_plan['pest_name']}", title_style))
        story.append(Spacer(1, 20))

        # Image
        try:
            img = Image(pest_image, width=4*inch, height=3*inch)
            story.append(img)
            story.append(Spacer(1, 20))
        except Exception as img_error:
            print(f"Error adding image: {str(img_error)}")
            story.append(Paragraph("Image not available", body_style))

        # Attack Reasons
        story.append(Paragraph("🔍 Attack Reasons:", heading_style))
        for reason in treatment_plan.get('attack_reasons', []):
            story.append(Paragraph(f"✅ {reason}", body_style))
        story.append(Spacer(1, 20))

        # Prevention Tips
        story.append(Paragraph("🚜 Prevention Tips:", heading_style))
        for tip in treatment_plan.get('prevention_tips', []):
            story.append(Paragraph(f"✔ {tip}", body_style))
        story.append(Spacer(1, 20))

        # Natural Remedies
        story.append(Paragraph("🌿 Natural Remedies:", heading_style))
        for remedy in treatment_plan.get('natural_remedies', []):
            story.append(Paragraph(f"🌱 {remedy}", body_style))
        story.append(Spacer(1, 20))

        # Chemical Control
        story.append(Paragraph("🧪 Chemical Control:", heading_style))
        for control in treatment_plan.get('chemical_control', []):
            story.append(Paragraph(f"⚗ {control}", body_style))
        story.append(Spacer(1, 20))

        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error in pest_pdf: {str(e)}")
        raise
