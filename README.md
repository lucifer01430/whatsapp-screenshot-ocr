# WhatsApp OCR Admin Dashboard by Harsh Pandey

A Django-based admin tool that converts WhatsApp chat screenshots into clean, structured Excel sheets. Built for fast uploads, reliable OCR extraction, and easy review in an admin-friendly dashboard.

---

## Overview

This project helps admins:
- Upload batches of WhatsApp screenshots and extract names and mobile numbers.
- Export results to Excel for further processing.
- Work faster with a clean admin UI and a light/dark theme toggle.

---

## App Screenshots

Below are sample WhatsApp screenshots used as OCR inputs in this project.

### Sample Input 1
![Sample Input 1]([media/uploads/0bd0b607c5ed47d68749cf3d35a6ece1.jpeg](https://raw.githubusercontent.com/lucifer01430/whatsapp-screenshot-ocr/refs/heads/main/media/screenshots/1.jpeg))

### Sample Input 2
![Sample Input 2]([media/uploads/200de40d926c48ac983875a3795a7531.jpeg](https://raw.githubusercontent.com/lucifer01430/whatsapp-screenshot-ocr/refs/heads/main/media/screenshots/2.jpeg))

### Sample Input 3
![Sample Input 3]([media/uploads/59f5a048cbc74b7eb723bf7ee8762892.jpeg](https://raw.githubusercontent.com/lucifer01430/whatsapp-screenshot-ocr/refs/heads/main/media/screenshots/3.jpeg))

---

## Tech Stack

- Python 3 + Django
- EasyOCR + OpenCV for text extraction
- Pandas + OpenPyXL for Excel export
- AdminLTE (CDN) for admin UI

---

## Features

- Batch upload of WhatsApp screenshots
- OCR-based name and phone extraction
- Excel export for processed data
- Admin dashboard with improved overview and quick actions
- Light/dark theme toggle with persistence

---

## Project Structure
```
whatsapp_ocr/
├── app/
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   └── upload.html
│   ├── ocr.py
│   ├── views.py
│   └── urls.py
├── config/
│   ├── settings.py
│   └── urls.py
├── media/
│   ├── uploads/        # Sample input screenshots
│   └── exports/        # Generated Excel exports
├── manage.py
└── README.md
```

---

## How to Run Locally

### 1) Create and activate a virtual environment
```
python -m venv venv
venv\Scripts\activate
```

### 2) Install dependencies
```
pip install -r requirements.txt
```

### 3) Apply migrations
```
python manage.py migrate
```

### 4) Start the server
```
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

---

## About the Developer

Hi, I am Harsh Pandey. I build practical admin tools and automation workflows focused on clarity, speed, and reliable data output.

---

## Connect

- Instagram: https://www.instagram.com/sasta_developer0143
- Personal Instagram: https://www.instagram.com/lucifer__1430
- Portfolio: https://lucifer01430.github.io/Portfolio
- Email: harshpandeylucifer@gmail.com

---

If this project helps you, consider starring the repository.
