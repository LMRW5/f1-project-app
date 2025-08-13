# 🏎️ F1 Prediction App

A sleek, modern Formula 1 prediction web app that uses machine learning to forecast qualifying and race results for upcoming F1 events.
The app presents predictions side-by-side with confidence scores, dynamic driver images, and a responsive, F1-inspired interface.

---

## 🚀 Features

- 🗓 **Upcoming Race Selector** – Choose from upcoming races in the current season.
- 📊 **Dual Predictions Display** – See both Qualifying and Race predictions at the same time.
- 🤖 **ML-Powered Forecasts** – Backend model predicts position, score, standard deviation, and confidence.
- 🌲 **Random Forest Regressor** – Core ML algorithm powering the predictions.
- 🏁 **Driver Hover Images** – Hover over a driver to view their profile image.
- 📱 **Responsive Design** – Optimized for desktop and mobile devices.
- 📊 **High R² values** - around 91%
- 📉 **Low MSE values** - around 2.894

---

## 📦 Dependencies
- numpy
- pandas
- sklearn
- glob
- joblib
- fastf1
- shap
- fastapi
- pydantic
- uvicorn

## 🛠️ Tech Stack

**Frontend**
- React + Vite
- Modern CSS + Flexbox

**Backend**
- Python
- FastAPI
- Pandas / NumPy

**Machine Learning**
- Scikit-learn
- FastF1 API
- Joblib

---
## 📸 Screenshots
### Desktop Home Screen
![home screen image](image-2.png)

### Desktop Predictions View
![example Predictions](image-3.png)

### Mobile Home Screen
![home screen image on mobile](image-7.png)

### Mobile Predictions View
![example predicitons view on mobile](image-6.png)

## ⚡ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/LMRW5/f1-prediction-app.git
cd f1-prediction-app
```

### 2️⃣ Backend setup
```bash
cd API
pip install -r requirements.txt
uvicorn main:app
```

3️⃣ Frontend setup
```bash
cd client
npm install
npm run dev
```
## 📱 Running on Mobile (Local Network)
You can access the app from your phone while developing locally.

### Backend (FastAPI)
Run the backend so it’s visible on your network:
```bash
cd API
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
This allows connections from devices on the same Wi-Fi network.

### Frontend (Vite)
Run the frontend with:

```bash
cd client
npm install
npm run dev -- --host
```
### Find your IP

On your computer, run:

Mac/Linux: ifconfig

Windows: ipconfig

Look for your IPv4 address (e.g., 192.168.0.42).

### Update API URL
in App.jsx inside the client folder:
```jsx
const IP = "192.168.1.9"
```
update IP variable to match IP found in IPV4

### Connect from your phone
On your phone’s browser, go to:
```cpp
http://<your-ip>:5173
```



## 🎯 Usage
1. Start both backend and frontend servers.

2. Open the frontend in your browser (Vite will show you the local dev URL).

3. Select an upcoming race from the dropdown.

4. Click Get Predictions.


## 📬 Contact

Ryan Wu

Email: kkryan42@gmail.com

GitHub: [LMRW5](https://github.com/LMRW5)