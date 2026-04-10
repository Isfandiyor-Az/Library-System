# 📚 Library Management System API

A RESTful API for managing a digital library system with role-based access control, built using **Django** and **Django REST Framework**.

---

## 🚀 Features

* 🔐 JWT Authentication (Login/Register)
* 👥 Role-based access (Admin, Operator, User)
* 📚 Book management
* 📦 Order (borrowing) system
* 📌 Reservation system (auto-expire in 1 day)
* ⭐ Rating system (0–5 stars)
* 💸 Automatic penalty calculation for late returns
* ⏰ Scheduled task to delete expired reservations
* 📖 Swagger API documentation

---

## 🧠 Roles & Permissions

### 👑 Admin

* Full access to all endpoints

### 🧑‍💼 Operator

* Add / update / delete books
* View and manage orders
* Accept and process orders

### 👤 User

* View books
* Reserve books (expires in 1 day)
* Rate books after reading

---

## ⚙️ Tech Stack

* Python
* Django
* Django REST Framework
* JWT Authentication
* SQLite (or PostgreSQL)
* Swagger (drf-yasg / drf-spectacular)

---

## 📂 Project Structure

```
library-system/
│
├── config/
├── library/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── management/
│   │   └── commands/
│   │       └── delete_expired_reservations.py
│
├── manage.py
```

---

## 🔐 Authentication

### Register

```
POST /api/register/
```

### Login (JWT)

```
POST /api/token/
```

Use token in headers:

```
Authorization: Bearer <your_token>
```

---

## 📚 Main Endpoints

### Books

```
GET    /api/books/
POST   /api/books/
PUT    /api/books/{id}/
DELETE /api/books/{id}/
```

### Orders

```
GET    /api/orders/
POST   /api/orders/
PUT    /api/orders/{id}/
POST   /api/orders/{id}/accept_order/
```

### Reservations

```
POST   /api/reservations/
```

### Ratings

```
POST   /api/ratings/
```

---

## 💸 Penalty Logic

If a book is returned late:

Penalty = daily_price × 1% × overdue_days

Example:

* daily_price = 1000 so’m
* 3 days late → penalty = 30 so’m

---

## ⏰ Auto-delete Expired Reservations

Run command manually:

```
python manage.py delete_expired_reservations
```

Or automate with cron job.

---

## 📖 Swagger Documentation

Available at:

```
/swagger/
```

---

## ▶️ Run Project

```bash
git clone https://github.com/your-username/library-system.git
cd library-system

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

---

## 🧪 Testing

Use:

* Postman
* Swagger UI

---

## 📌 Author

* Your Name

---

## ⭐ Notes

This project demonstrates:

* REST API design
* Role-based authentication
* Real-world business logic
* Backend automation

---
