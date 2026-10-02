# 🏡 SmartPlot

SmartPlot is a Flask-based real-estate web application that connects plot buyers and sellers directly.

Buyers can search and filter available plots, view complete property details, save favorite plots, check locations, contact owners, and send inquiries.

Sellers can publish plots, upload photos, manage listings, update availability, receive buyer inquiries, and view seller statistics.

---

## 🚀 Features

### 🛒 Buyer Features

- User registration and login
- Search available plots
- Filter plots by:
  - Location
  - Minimum area
  - Maximum area
  - Minimum price
  - Maximum price
  - Property type
- Sort plots by:
  - Newest
  - Price: Low to High
  - Price: High to Low
  - Area: Low to High
  - Area: High to Low
- View detailed plot information
- View plot photos
- Calculate and display price per sq.ft.
- Save plots to Favorites
- View saved Favorites
- Open plot location in Google Maps
- Call the plot owner
- Contact the owner through WhatsApp
- Send inquiries directly to sellers

---

### 🏡 Seller Features

- Seller registration and login
- Add new plot listings
- Upload plot photos
- Add property information
- Add location and landmark
- Manage personal listings
- Update plot availability
- Mark plots as:
  - Available
  - Reserved
  - Sold
- View buyer inquiries
- View buyer contact information
- Mark inquiries as read
- View seller statistics

---

## 📊 Seller Statistics

The seller dashboard provides statistics such as:

- Total Listings
- Available Listings
- Reserved Listings
- Sold Listings
- Total Buyer Inquiries
- Total Favorites

The Favorites statistic represents the number of times buyers have saved the seller's plots.

---

## 🔐 Security Features

SmartPlot includes several basic security measures:

- Password hashing using Werkzeug
- Secure user sessions
- Role-based access for buyers and sellers
- Parameterized SQL queries
- Secure uploaded filenames
- Uploaded image type validation
- Unique filenames for uploaded images
- Maximum request/upload size limit
- Session-based authentication
- Restricted seller and buyer functionality

---

## 🗺️ Location Feature

Each plot contains location information.

Users can open the approximate plot location using Google Maps.

This helps buyers understand where the property is located before contacting the seller.

---

## 🔔 Buyer-Seller Inquiry System

Buyers can send messages to sellers from the plot details page.

Example:

> Hi, I am interested in this plot. Is it still available?

The inquiry is stored in the database and displayed in the seller's inquiry section.

---

## 🛠️ Technologies Used

### Backend

- Python
- Flask

### Frontend

- HTML5
- CSS3
- Jinja2

### Database

- SQLite

### Security

- Werkzeug Password Hashing
- Secure Filename Handling
- Session Authentication
- Parameterized SQL Queries

---

## 📂 Project Structure

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
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── forgot_password.html
│   ├── dashboard.html
│   ├── plots.html
│   ├── plot_details.html
│   ├── favorites.html
│   ├── add_plot.html
│   ├── my_listings.html
│   ├── inquiries.html
│   ├── seller_statistics.html
│   ├── modify_account.html
│   └── 404.html
│
└── uploads/
    └── plots/