from flask import Flask, render_template
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')


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

if __name__=='__main__':
    app.run(debug=True)


# Import OS module to work with file paths and directories
import os
# Import time module to measure inference time
import time
# Import numpy for numerical operations
import numpy as np
# Import OpenCV for image processing
import cv2
# Import PyTorch core library
import torch
# Import neural network module from PyTorch
import torch.nn as nn
# Import functional utilities like interpolation
import torch.nn.functional as F
# Import Flask framework for web app
from flask import Flask, render_template, request, redirect, url_for
# Import pretrained models and transforms from torchvision
from torchvision import models, transforms
# Import PIL for image handling
from PIL import Image
# Create Flask app instance
app = Flask(__name__)
# Set folder where uploaded images will be saved
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
# Set folder where result images will be saved
app.config['RESULT_FOLDER'] = os.path.join('static', 'results')
# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# Create result folder if it doesn't exist
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)
# ---------------------------------------------------------
# 1. MODEL DEFINITION
# ---------------------------------------------------------
# Function to create two convolution layers with batch norm and ReLU
def double_conv(in_channels, out_channels):
 return nn.Sequential(
 # First convolution layer
 nn.Conv2d(in_channels, out_channels, 3, padding=1),
 # Normalize outputs
 nn.BatchNorm2d(out_channels),
 # Apply activation
 nn.ReLU(inplace=True),
 # Second convolution layer
 nn.Conv2d(out_channels, out_channels, 3, padding=1),
 # Normalize again
 nn.BatchNorm2d(out_channels),
 # Activation again
 nn.ReLU(inplace=True)
 )
# Define custom ResNet + U-Net model
class ResNetUNet(nn.Module):
 # Constructor function
 def __init__(self, n_class):
 super().__init__()
 # Load ResNet18 model without pretrained weights
 self.base_model = models.resnet18(pretrained=False)
 # Convert model layers into list
 self.base_layers = list(self.base_model.children())
 # Initial layers
 self.layer0 = nn.Sequential(*self.base_layers[:3])
 # Next layers
 self.layer0_1 = nn.Sequential(*self.base_layers[3:5])
 # Encoder layers
 self.layer1 = self.base_layers[5]
 self.layer2 = self.base_layers[6]
 self.layer3 = self.base_layers[7]
 # Upsampling layer
 self.upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
 # Decoder layers with skip connections
 self.conv_up3 = double_conv(512 + 256, 256)
 self.conv_up2 = double_conv(256 + 128, 128)
 self.conv_up1 = double_conv(128 + 64, 64)
 self.conv_up0 = double_conv(64 + 64, 32)
 # Final output layer
 self.conv_last = nn.Conv2d(32, n_class, 1)
 # Forward pass
 def forward(self, x):
# Encoder forward pass
 l0 = self.layer0(x)
 l0_1 = self.layer0_1(l0)
 l1 = self.layer1(l0_1)
 l2 = self.layer2(l1)
 l3 = self.layer3(l2)
 # Decoder with skip connections
 x = self.upsample(l3)
 x = torch.cat([x, l2], dim=1)
 x = self.conv_up3(x)
 x = self.upsample(x)
 x = torch.cat([x, l1], dim=1)
 x = self.conv_up2(x)
 x = self.upsample(x)
 # Resize to match earlier layer
 x = F.interpolate(x, size=l0_1.size()[2:], mode='bilinear', align_corners=True)
 x = torch.cat([x, l0_1], dim=1)
 x = self.conv_up1(x)
 x = self.upsample(x)
 # Resize again
 x = F.interpolate(x, size=l0.size()[2:], mode='bilinear', align_corners=True)
 x = torch.cat([x, l0], dim=1)
 x = self.conv_up0(x)
 # Final output
 out = self.upsample(self.conv_last(x))
 return out
# ---------------------------------------------------------
# 2. CLASS CONFIGURATION
# ---------------------------------------------------------
# Dictionary mapping class IDs to labels
CLASS_LABELS = {
 0: "Unlabeled", 1: "Paved Area", 2: "Dirt", 3: "Grass",
 4: "Gravel", 5: "Water", 6: "Rocks", 7: "Pool",
 8: "Vegetation", 9: "Roof", 10: "Wall", 11: "Window",
 12: "Door", 13: "Fence", 14: "Fence Pole", 15: "Person",
 16: "Dog", 17: "Car", 18: "Bicycle", 19: "Tree",
 20: "Bald Tree", 21: "Arid Vegetation", 22: "Obstacle"
}
# Define colors for each class (RGB)
COLOR_MAP = np.array([
 (0, 0, 0), (128, 128, 128), (150, 75, 0), (0, 154, 23), (192, 192, 192),
 (0, 0, 255), (105, 105, 105), (0, 255, 255), (0, 255, 0), (255, 0, 0),
 (165, 42, 42), (0, 191, 255), (255, 165, 0), (218, 165, 32), (184, 134, 11),
 (255, 192, 203), (255, 20, 147), (255, 255, 0), (127, 0, 255), (34, 139, 34),
 (210, 180, 140), (255, 215, 0), (128, 0, 0)
], dtype=np.uint8)
# ---------------------------------------------------------
# 3. LOAD MODEL
# ---------------------------------------------------------
# Use GPU if available, otherwise CPU
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# Create model with 23 classes
model = ResNetUNet(23).to(DEVICE)
# Check if trained model file exists
if os.path.exists('resnetunet_aerial.pth'):
 # Load saved weights
 sd = torch.load('resnetunet_aerial.pth', map_location=DEVICE)
 # Remove "module." prefix (if trained on multi-GPU)
 model.load_state_dict({k.replace('module.', ''): v for k, v in sd.items()})
 # Set model to evaluation mode
 model.e
 # Define image preprocessing steps
transform = transforms.Compose([
 # Resize image to 512x512
 transforms.Resize((512, 512)),
 # Convert image to tensor
 transforms.ToTensor(),
 # Normalize image
 transforms.Normalize(mean=[0.485, 0.456, 0.406],
 std=[0.229, 0.224, 0.225])
])
# ---------------------------------------------------------
# 4. ROUTES
# ---------------------------------------------------------
# Home page route
@app.route('/')
def index():
 return render_template('index.html')
# Prediction route
@app.route('/predict', methods=['POST'])
def predict():
 # Get uploaded file
 file = request.files.get('file')
 # If no file, redirect to home
 if not file:
 return redirect('/')
 # Get filename
 filename = file.filename
 # Create file path
 filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
 # Save uploaded image
 file.save(filepath)
 # Open image using PIL and convert to RGB
 img_pil = Image.open(filepath).convert('RGB')
 # Get original size
 orig_w, orig_h = img_pil.size
 # Apply preprocessing and add batch dimension
 input_tensor = transform(img_pil).unsqueeze(0).to(DEVICE)
 # Start timing
 start = time.time()
 # Disable gradient calculation for faster inference
 with torch.no_grad():
 # Get model output
 output = model(input_tensor)
 # Get predicted class for each pixel
 mask = torch.argmax(output, dim=1).squeeze(0).cpu().numpy()
 # Calculate inference time in ms
 inf_time = round((time.time() - start) * 1000, 2)
 # Generate stats
 unique_labels, counts = np.unique(mask, return_counts=True)
 total_pixels = mask.size
 stats = []
 for lbl, count in zip(unique_labels, counts):
 # Calculate percentage
 pct = round((count / total_pixels) * 100, 1)
 # Get color for class
 color = COLOR_MAP[lbl]
 # Convert to hex
 hex_color = '#%02x%02x%02x' % (color[0], color[1], color[2])
 # Add to stats
 stats.append({
 'name': CLASS_LABELS.get(lbl, "Other"),
 'pct': pct,
 'color': hex_color
 })
 # Sort by highest percentage
 stats = sorted(stats, key=lambda x: x['pct'], reverse=True)
 # Convert mask to RGB image
 mask_rgb = COLOR_MAP[mask]
 # Resize mask to original size
 mask_img = cv2.resize(mask_rgb, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
 # Convert original image to OpenCV format
 orig_img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
 # Create overlay (blend original + mask)
 overlay = cv2.addWeighted(orig_img, 0.6,cv2.cvtColor(mask_img, cv2.COLOR_RGB2BGR),
 0.4, 0)
 # Save mask image
 cv2.imwrite(os.path.join(app.config['RESULT_FOLDER'], 'mask_' + filename),
 cv2.cvtColor(mask_img, cv2.COLOR_RGB2BGR))
 # Save overlay image
 cv2.imwrite(os.path.join(app.config['RESULT_FOLDER'], 'overlay_' + filename),
 overlay)
 # Render result page
 return render_template('predict.html',
 filename=filename,
 time=inf_time,
 stats=stats)
# Run the Flask app
if __name__ == '__main__':
 app.run(debug=True, port=5000)