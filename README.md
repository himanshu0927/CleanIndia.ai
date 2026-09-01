# EcoVision AI

EcoVision AI is an AI-based cleanliness complaint reporting system built using Django. Citizens can report garbage, overflowing bins, illegal dumping, drainage issues, and other cleanliness problems with images and location details. Authority users can manage complaints, update statuses, upload cleanup proof, review citizen feedback, and export reports.

## Objective

The objective of this project is to support cleaner cities by making cleanliness issue reporting faster, smarter, and more transparent using web technology, image upload, location tracking, AI-based demo classification, and authority-side complaint workflow management.

## Features

- User signup, login, and logout
- Citizen complaint submission
- Image upload for complaint proof
- Location, latitude, and longitude support
- Google Maps location link
- AI-based demo classification
- AI confidence score
- Citizen My Complaints page
- Authority-only dashboard
- Staff-only status management
- Complaint status: Pending, In Progress, Resolved
- Complaint detail page
- Status timeline
- Before and after cleanup proof images
- Citizen feedback and rating
- Feedback analytics for authority
- Search and filter complaints
- Export complaints to CSV
- Django admin panel

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python, Django
- Database: SQLite
- Authentication: Django Auth
- Image Handling: Pillow
- Maps: Google Maps location link
- AI: Demo classification logic
- Export: CSV report generation

## Important URLs

- Home: http://127.0.0.1:8000/
- Signup: http://127.0.0.1:8000/signup/
- Login: http://127.0.0.1:8000/login/
- Report Complaint: http://127.0.0.1:8000/report/
- My Complaints: http://127.0.0.1:8000/my-complaints/
- Authority Dashboard: http://127.0.0.1:8000/dashboard/
- Admin Panel: http://127.0.0.1:8000/admin/

## Folder Structure

```text
EcoVision AI/
├── manage.py
├── swachhai/
│   ├── db.sqlite3
│   ├── swachhai/
│   │   ├── settings.py
│   │   ├── urls.py
│   ├── complaints/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── admin.py
│   ├── templates/
│   │   ├── home.html
│   │   ├── report.html
│   │   ├── dashboard.html
│   │   ├── my_complaints.html
│   │   ├── complaint_detail.html
│   │   ├── feedback.html
│   │   ├── resolve_with_proof.html
│   ├── static/
│   │   └── css/
│   │       └── style.css
│   ├── media/
│   │   ├── garbage_images/
│   │   └── resolved_images/
├── README.md
├── PROJECT_REPORT.md
├── requirements.txt
```

## How To Run

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Open in browser:

```text
http://127.0.0.1:8000/
```

## Final Testing Checklist

- [ ] Normal user signup works
- [ ] Normal user login works
- [ ] Normal user can submit complaint
- [ ] Normal user can see My Complaints
- [ ] Normal user cannot open Authority Dashboard
- [ ] Staff user can open Authority Dashboard
- [ ] Staff user can update status
- [ ] Staff user can resolve with proof image
- [ ] Complaint detail page works
- [ ] Timeline works
- [ ] Feedback works after resolved
- [ ] CSV export works
- [ ] Admin panel works

## Future Scope

- Real YOLO/CNN image classification
- OpenStreetMap dashboard
- Ward-wise complaint assignment
- SMS/email notification
- Municipal authority panel with ward mapping
- Deployment on Render, Railway, or Vercel-compatible hosting

## Submission Note

For submission, send code files and `requirements.txt`. Do not include the `venv` folder.

