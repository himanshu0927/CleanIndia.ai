# CleanIndia.ai Project Report

## 1. Introduction

CleanIndia.ai is a web-based cleanliness complaint reporting system. It helps citizens report garbage, overflowing bins, illegal dumping, drainage issues, and other cleanliness-related problems. The project supports the idea of a cleaner India through citizen participation, authority workflow management, location support, and smart demo AI classification.

## 2. Problem Statement

In many cities, cleanliness problems are noticed by citizens but are not reported properly. Even when complaints are submitted, tracking and resolving them can be slow. Citizens also may not know whether their complaint is pending, in progress, or resolved. There is a need for a simple platform where users can submit complaints with images and location details, and authorities can manage the complaint lifecycle transparently.

## 3. Proposed Solution

CleanIndia.ai provides a digital platform where users can report cleanliness issues by filling a form, uploading an image, and adding location details. The system stores complaints in a database and displays them on an authority-only dashboard. It provides AI-based demo classification, confidence score, status timeline, cleanup proof image, feedback collection, analytics, and CSV export.

## 4. Objectives

- To create a web platform for cleanliness complaint reporting
- To allow image-based complaint submission
- To provide dashboard-based complaint tracking
- To show AI-based classification result
- To support location and map-based complaint viewing
- To allow status updates from Pending to In Progress to Resolved
- To allow authorities to upload cleanup proof
- To collect citizen rating and feedback after resolution
- To export complaint records for reporting

## 5. Technology Used

Frontend: HTML, CSS, JavaScript  
Backend: Python and Django  
Database: SQLite  
Authentication: Django Auth  
Image Upload: Pillow  
Maps: Google Maps link  
AI Module: Demo image classification logic  
Export: CSV report generation

## 6. Modules

### User Module

The user can open the website, sign up, log in, report a complaint, upload an image, add location details, view personal complaints, and submit feedback after resolution.

### Complaint Module

This module stores complaint details such as name, location, latitude, longitude, category, description, image, status, AI result, AI confidence, cleanup proof image, feedback, and rating.

### Dashboard Module

The dashboard displays total complaints, pending complaints, in-progress complaints, resolved complaints, complaint images, AI result, map links, feedback analytics, search, filters, and CSV export.

### Authority Module

The authority user can access a protected dashboard, view all complaints, update complaint status, resolve complaints with proof image, view citizen feedback, and export complaint records as CSV.

### Admin Module

The admin can manage complaints from the Django admin panel and update complaint records.

### AI Module

The AI module gives a demo classification result based on the selected complaint category. In future, it can be replaced with YOLO, CNN, or TensorFlow model.

### Feedback Module

Citizens can submit rating and feedback after their complaint is resolved. This helps authorities understand public satisfaction.

### Timeline Module

The system stores submitted, in-progress, and resolved timestamps to track the progress of each complaint.

## 7. Features

- User signup, login, and logout
- Complaint form
- Image upload
- My Complaints page
- Authority-only dashboard
- Status tracking
- Status timeline
- Resolve with proof image
- AI result
- AI confidence score
- Search and filter
- Google Maps link
- Citizen feedback and rating
- Feedback analytics
- CSV export
- Django admin panel

## 8. Future Scope

In the future, the project can be improved by adding real AI image classification, OpenStreetMap integration, ward-wise complaint assignment, SMS/email notification, authority role assignment by area, and deployment on cloud platforms.

## 9. Conclusion

CleanIndia.ai is a useful and practical project that combines web development, authentication, image upload, location support, authority workflow, AI-based demo classification, feedback analytics, and report export. It can help citizens and authorities work together for cleaner cities and supports the vision of Swachh Bharat.

## 10. Final Testing Checklist

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
