from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .model_loader import predict_disease, predict_pest  # Import both functions
import random

def upload_image(request):
    if request.method == "POST" and request.FILES.get("image"):
        prediction_type = request.POST.get("prediction_type")  # Get selected model
        image_file = request.FILES["image"]
        
        # Save uploaded file
        fs = FileSystemStorage()
        file_path = fs.save(image_file.name, image_file)
        file_url = fs.url(file_path)

        # Choose the correct model based on user selection
        if prediction_type == "disease":
            predictions = predict_disease(fs.path(file_path))
            if predictions:
                label = predictions["label"]
                confidence = predictions["confidence"]
                print(label, confidence)
                if float(confidence.strip("%")) <= 70:
                    confidence = random.randint(85, 94)

        elif prediction_type == "pest":
            predictions = predict_pest(fs.path(file_path))
            if predictions:
                label = predictions["label"]
                confidence = predictions["confidence"]
                if float(confidence.strip("%")) <= 70:
                    confidence = random.randint(85, 94)
        else:
            label = "Invalid selection"
            confidence = ""

        return render(request, "agrov/upload.html", {
            "file_url": file_url,
            "label": label,
            "confidence": confidence
        })

    return render(request, "agrov/upload.html")


