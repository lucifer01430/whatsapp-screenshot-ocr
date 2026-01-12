import os
import uuid
import pandas as pd

from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .ocr import extract_contacts


def dashboard(request):
    return render(request, "dashboard.html")


@require_http_methods(["GET", "POST"])
def upload(request):
    if request.method == "GET":
        return render(request, "upload.html")

    images = request.FILES.getlist("images")

    print("FILES keys:", list(request.FILES.keys()))
    print("Images count:", len(images))

    if not images:
        messages.error(request, "No files received. Please select images and try again.")
        return render(request, "upload.html")

    upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
    export_dir = os.path.join(settings.MEDIA_ROOT, "exports")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(export_dir, exist_ok=True)

    rows = []
    failed = 0
    total_contacts = 0

    for idx, f in enumerate(images, start=1):
        try:
            ext = os.path.splitext(f.name)[1].lower() or ".jpg"
            fname = f"{uuid.uuid4().hex}{ext}"
            fpath = os.path.join(upload_dir, fname)

            # save image
            with open(fpath, "wb") as out:
                for chunk in f.chunks():
                    out.write(chunk)

            print(f"[{idx}/{len(images)}] OCR: {f.name}")

            contacts = extract_contacts(fpath)  # list of {Name, Mobile}
            if not contacts:
                print(f"[{idx}/{len(images)}] No contacts detected: {f.name}")
                continue

            total_contacts += len(contacts)

            for c in contacts:
                rows.append({
                    "Name": c.get("Name", "").strip(),
                    "Mobile": c.get("Mobile", "").strip(),
                    "SourceFile": f.name
                })

            print(f"[{idx}/{len(images)}] Found {len(contacts)} contacts.")

        except Exception as e:
            failed += 1
            print(f"❌ ERROR on {f.name}: {e}")
            continue

    print("TOTAL ROWS:", len(rows))
    print("FAILED IMAGES:", failed)

    # ✅ IMPORTANT: avoid blank excel silently
    if not rows:
        messages.error(
            request,
            "0 contacts extracted from batch. Please try smaller batch (10-20) or check screenshot clarity."
        )
        return render(request, "upload.html")

    df = pd.DataFrame(rows)

    out_name = f"contacts_{uuid.uuid4().hex}.xlsx"
    out_path = os.path.join(export_dir, out_name)
    df.to_excel(out_path, index=False)

    messages.success(
        request,
        f"Done! Images: {len(images)}, Contacts: {total_contacts}, Failed images: {failed}. Downloading Excel…"
    )
    return redirect("download", filename=out_name)


def download(request, filename):
    path = os.path.join(settings.MEDIA_ROOT, "exports", filename)
    if not os.path.exists(path):
        return HttpResponse("File not found", status=404)

    return FileResponse(open(path, "rb"), as_attachment=True, filename=filename)
