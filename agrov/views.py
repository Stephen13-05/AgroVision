from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .model_loader import predict_disease, predict_pest  # Import both functions

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
            prediction = predict_disease(fs.path(file_path))
        elif prediction_type == "pest":
            prediction = predict_pest(fs.path(file_path))
        else:
            prediction = {"label": "Invalid selection", "confidence": "N/A"}

        return render(request, "agrov/upload.html", {
            "file_url": file_url,
            "prediction_label": prediction["label"],
            "prediction_confidence": prediction["confidence"]
        })

    return render(request, "agrov/upload.html")
