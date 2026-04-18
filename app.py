from flask import Flask, render_template, url_for, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
<<<<<<< HEAD

app = Flask(__name__)

app = Flask(__name__)
app.secret_key = 'secretkey'  #secret key for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #to suppress a warning from SQLAlchemy
db = SQLAlchemy(app) #initialize the database

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

# Database initialization with app context
with app.app_context(): 
    db.create_all()

@app.route('/login', methods=['GET', 'POST']) # register page
def signup():
    if request.method == 'POST':
        # Determine whether this POST is a registration (has fullname) or a login
        if request.form.get('fullname'):
            fullname = request.form.get('fullname', '').strip()
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password')

            # Basic validation
            if not (fullname and username and email and password):
                flash('Please fill all required fields for registration.', 'error')
                return redirect(url_for('signup'))
            
             #password must be at least 8 characters long and a combination of letters and numbers and special characters
            if len(password)<8 or not any(char.isdigit() for char in password)\
              or not any(char.isalpha() for char in password) or not any(not char.isalnum()\
                                                                          for char in password):
                flash('Password must be at least 8 characters long and contain letters, \
                  numbers, and special characters.', 'error')
                return redirect(url_for('signup'))
        
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('signup'))

            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists!', 'error')
                return redirect(url_for('signup'))

            # Hash the password
            password_hash = generate_password_hash(password)

            # Create new user
            new_user = User(
                fullname=fullname,
                username=username,
                email=email,
                password_hash=password_hash
            )

            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please sign in.', 'success')
                # Redirect back to the same login page so the sign-in form is shown
                return redirect(url_for('signup'))

            except Exception:
                db.session.rollback()
                flash('Registration failed!', 'error')
                return redirect(url_for('signup'))

        else:
            # Login flow
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not (username and password):
                flash('Please provide username and password.', 'error')
                return redirect(url_for('signup'))

            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                session["user_id"]=user.id
                session["user_name"]=user.username
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials.', 'error')
                return redirect(url_for('signup'))

    return render_template("login.html")

# Import OS module to work with file paths and directories
=======
from flask_login import login_required as flask_login_required, login_user, logout_user, LoginManager, UserMixin
>>>>>>> 5a33b949ee5f7f5e62e18974069b4b7239cb7602
import os
import time
import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
from functools import wraps

# -------------------- FLASK SETUP --------------------
app = Flask(__name__)
app.secret_key = 'secret_key'

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Upload & Result folders
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['RESULT_FOLDER'] = os.path.join('static', 'results')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

# -------------------- LOGIN SETUP --------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100))
    email    = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# -------------------- CUSTOM LOGIN REQUIRED --------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------- MODEL --------------------
def double_conv(in_channels, out_channels):
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, 3, padding=1),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_channels, out_channels, 3, padding=1),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True)
    )

class ResNetUNet(nn.Module):
    def __init__(self, n_class):
        super().__init__()
        self.base_model = models.resnet18(pretrained=False)
        self.base_layers = list(self.base_model.children())

        self.layer0 = nn.Sequential(*self.base_layers[:3])
        self.layer0_1 = nn.Sequential(*self.base_layers[3:5])
        self.layer1 = self.base_layers[5]
        self.layer2 = self.base_layers[6]
        self.layer3 = self.base_layers[7]

        self.upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)

        self.conv_up3 = double_conv(512 + 256, 256)
        self.conv_up2 = double_conv(256 + 128, 128)
        self.conv_up1 = double_conv(128 + 64, 64)
        self.conv_up0 = double_conv(64 + 64, 32)

        self.conv_last = nn.Conv2d(32, n_class, 1)

    def forward(self, x):
        l0 = self.layer0(x)
        l0_1 = self.layer0_1(l0)
        l1 = self.layer1(l0_1)
        l2 = self.layer2(l1)
        l3 = self.layer3(l2)

        x = self.upsample(l3)
        x = torch.cat([x, l2], dim=1)
        x = self.conv_up3(x)

        x = self.upsample(x)
        x = torch.cat([x, l1], dim=1)
        x = self.conv_up2(x)

        x = self.upsample(x)
        x = F.interpolate(x, size=l0_1.size()[2:], mode='bilinear', align_corners=True)
        x = torch.cat([x, l0_1], dim=1)
        x = self.conv_up1(x)

        x = self.upsample(x)
        x = F.interpolate(x, size=l0.size()[2:], mode='bilinear', align_corners=True)
        x = torch.cat([x, l0], dim=1)
        x = self.conv_up0(x)

        return self.upsample(self.conv_last(x))

# -------------------- LOAD MODEL --------------------
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = ResNetUNet(23).to(DEVICE)

if os.path.exists('resnetunet_aerial.pth'):
    sd = torch.load('resnetunet_aerial.pth', map_location=DEVICE)
    model.load_state_dict({k.replace('module.', ''): v for k, v in sd.items()})
    model.eval()

transform = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# -------------------- ROUTES --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()

        flash('Registered successfully', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            session['user_id'] = user.id
            return redirect(url_for('detector'))

        flash('Invalid credentials', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

# -------------------- PREDICTION --------------------
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    file = request.files.get('file')
    if not file:
        return redirect(url_for('detector'))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    img_pil = Image.open(filepath).convert('RGB')
    orig_w, orig_h = img_pil.size

    input_tensor = transform(img_pil).unsqueeze(0).to(DEVICE)

    start = time.time()
    with torch.no_grad():
        output = model(input_tensor)
        mask = torch.argmax(output, dim=1).squeeze().cpu().numpy()

    inf_time = round((time.time() - start) * 1000, 2)

    mask_rgb = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
    mask_img = cv2.resize(mask_rgb, (orig_w, orig_h))

    overlay = cv2.addWeighted(
        cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR),
        0.6,
        mask_img,
        0.4,
        0
    )

    cv2.imwrite(os.path.join(app.config['RESULT_FOLDER'], 'overlay_' + file.filename), overlay)

    return render_template('predict.html',
                           filename=file.filename,
                           time=inf_time)

@app.route('/detector')
@login_required
def detector():
    return render_template('upload.html')

# -------------------- RUN --------------------
if __name__ == '__main__':
    app.run(debug=True)