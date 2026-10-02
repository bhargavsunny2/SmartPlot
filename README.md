# 🏡 SmartPlot

SmartPlot is a web-based real-estate plot finder and buyer-seller connection platform.

It allows buyers to search and compare available plots, view complete property details, save favorite plots, contact owners, and send inquiries.

Sellers can publish their plots, upload property photos, manage listing availability, receive buyer inquiries, and view listing statistics.

---

## 🌐 Live Demo

**Live Website:**

https://smartplot-hxzv.onrender.com

---

## 📌 Project Overview

SmartPlot is designed to make the process of finding and selling plots easier through a simple web platform.

### 👤 Buyers can:

- Create a buyer account
- Login securely
- Search for available plots
- Filter plots by location
- Filter by minimum and maximum area
- Filter by minimum and maximum price
- Filter by property type
- Sort plots by price or area
- View complete plot details
- View plot photos
- Calculate/view price per sq.ft.
- Save plots to favorites
- View favorite plots
- View approximate map location
- Open the location in Google Maps
- Contact the owner by phone
- Contact the owner through WhatsApp
- Send inquiries to sellers

### 🏠 Sellers can:

- Create a seller account
- Login securely
- Add new plot listings
- Add plot location
- Add plot area
- Add selling price
- Add road width
- Select property type
- Select plot facing
- Add landmark
- Add description
- Upload plot images
- View their listings
- Change listing status
- Mark properties as available
- Mark properties as reserved
- Mark properties as sold
- Delete listings
- Receive buyer inquiries
- Mark inquiries as read
- View seller statistics

---

## ⭐ Main Features

### 🔍 Plot Search

Buyers can search available plots using:

- Location
- Plot area
- Price range
- Property type

---

### 📊 Sorting

Plots can be sorted by:

- Newest listings
- Lowest price
- Highest price
- Lowest area
- Highest area

---

### ❤️ Favorites

Buyers can save interesting plots to their favorites.

Each buyer has their own favorites list.

---

### 📷 Plot Images

Sellers can upload up to 5 images for each plot listing.

Supported formats:

- JPG
- JPEG
- PNG
- WEBP

---

### 🗺️ Location

Each plot contains a location and landmark.

Buyers can open the location in Google Maps.

---

### 🔔 Buyer-Seller Inquiry System

Buyers can send inquiries directly to plot owners.

Sellers can:

- View buyer name
- View buyer email
- View buyer phone
- Read the inquiry message
- Mark inquiries as read

---

### 📈 Seller Statistics

Sellers can view information such as:

- Total listings
- Available listings
- Reserved listings
- Sold listings
- Total inquiries
- New inquiries
- Read inquiries
- Total favorites
- Total available property value
- Average property price
- Recent listings

---

## 🔐 Security Features

SmartPlot includes several security features:

- Password hashing
- Login authentication
- Buyer and seller role-based access
- Secure session cookies
- HTTP-only cookies
- SameSite cookies
- Production HTTPS cookie support
- Security response headers
- Content Security Policy
- X-Content-Type-Options
- X-Frame-Options
- Referrer Policy
- File extension validation
- Secure uploaded filenames
- Unique filenames for uploaded images
- Request size limitation
- SQL parameterized queries

---

## 🛠️ Technologies Used

### Backend

- Python
- Flask
- SQLite

### Frontend

- HTML
- CSS
- Jinja2 Templates

### Security

- Werkzeug Password Hashing
- Flask Sessions

### Deployment

- GitHub
- Render

---

## 🗄️ Database

SmartPlot uses SQLite.

### Database Tables

#### Users

Stores:

- User ID
- Name
- Email
- Phone
- Password
- Role

Roles:

- Buyer
- Seller

#### Plots

Stores:

- Plot ID
- Seller ID
- Title
- Location
- Area
- Price
- Road width
- Property type
- Facing
- Landmark
- Description
- Status
- Created date

#### Plot Images

Stores uploaded plot images.

#### Favorites

Stores the plots saved by buyers.

#### Inquiries

Stores communication between buyers and sellers.

---

## 📁 Project Structure

```text
SmartPlot/
│
├── app.py
├── requirements.txt
├── README.md
│
├── database/
│   └── smartplot.db
│
├── uploads/
│   └── plots/
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── forgot_password.html
│   ├── dashboard.html
│   ├── add_plot.html
│   ├── my_listings.html
│   ├── plots.html
│   ├── favorites.html
│   ├── plot_details.html
│   ├── inquiries.html
│   ├── seller_statistics.html
│   ├── modify_account.html
│   └── 404.html
│
└── static/
    └── ...
