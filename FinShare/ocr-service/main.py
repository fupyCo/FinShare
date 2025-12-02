"""
FinShare OCR Service
Uses Tesseract (FREE) to extract text from receipt images.
No paid APIs required!
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import re
import io
import uuid
from datetime import datetime
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FinShare OCR Service",
    description="Free receipt scanning with Tesseract OCR",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================
# DATA MODELS
# ===========================================

class ReceiptItem(BaseModel):
    description: str
    amount: Optional[float] = None

class ReceiptData(BaseModel):
    merchant: Optional[str] = None
    date: Optional[str] = None
    total: Optional[float] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    tip: Optional[float] = None
    items: List[ReceiptItem] = []
    raw_text: str
    confidence: float

class OCRResponse(BaseModel):
    success: bool
    job_id: str
    data: Optional[ReceiptData] = None
    error: Optional[str] = None

# ===========================================
# IMAGE PREPROCESSING
# ===========================================

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Prepare image for better OCR results.
    This makes a big difference in accuracy!
    """
    # Convert to numpy array for OpenCV
    img_array = np.array(image)
    
    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Remove noise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Increase contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Threshold to get black text on white background
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Convert back to PIL Image
    return Image.fromarray(binary)

def deskew_image(image: Image.Image) -> Image.Image:
    """
    Fix tilted images - receipts are often photographed at an angle.
    """
    img_array = np.array(image)
    
    # Find edges
    edges = cv2.Canny(img_array, 50, 150, apertureSize=3)
    
    # Detect lines
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    
    if lines is not None:
        # Calculate average angle
        angles = []
        for line in lines[:10]:  # Use first 10 lines
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            if abs(angle) < 45:  # Only consider reasonable angles
                angles.append(angle)
        
        if angles:
            avg_angle = np.mean(angles)
            if abs(avg_angle) > 0.5:  # Only rotate if needed
                return image.rotate(avg_angle, fillcolor=255, expand=True)
    
    return image

# ===========================================
# TEXT EXTRACTION (Tesseract)
# ===========================================

def extract_text(image: Image.Image) -> tuple[str, float]:
    """
    Run Tesseract OCR on the image.
    Returns: (extracted_text, confidence_score)
    """
    # Get detailed data including confidence
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
    # Calculate average confidence (excluding -1 values which mean no text)
    confidences = [int(c) for c in data['conf'] if int(c) > 0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    # Get plain text
    text = pytesseract.image_to_string(image)
    
    return text, avg_confidence / 100  # Convert to 0-1 scale

# ===========================================
# DATA PARSING
# ===========================================

def parse_receipt_text(text: str) -> dict:
    """
    Extract structured data from raw OCR text.
    Uses pattern matching - no AI APIs needed!
    """
    result = {
        "merchant": None,
        "date": None,
        "total": None,
        "subtotal": None,
        "tax": None,
        "tip": None,
        "items": []
    }
    
    lines = text.strip().split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # --- Extract Merchant Name ---
    # Usually the first non-empty line or first few lines
    if lines:
        # Skip lines that look like addresses or phone numbers
        for line in lines[:5]:
            if not re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', line):  # Not a phone
                if not re.search(r'\d+\s+\w+\s+(st|street|ave|road|rd|blvd)', line, re.I):  # Not address
                    if len(line) > 2 and not line.replace(' ', '').isdigit():
                        result["merchant"] = line
                        break
    
    # --- Extract Date ---
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or MM-DD-YYYY
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',     # YYYY-MM-DD
        r'(\w{3}\s+\d{1,2},?\s+\d{4})',       # Jan 15, 2024
        r'(\d{1,2}\s+\w{3}\s+\d{4})',         # 15 Jan 2024
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["date"] = match.group(1)
            break
    
    # --- Extract Amounts ---
    # Look for total
    total_patterns = [
        r'total[:\s]*\$?(\d+\.?\d*)',
        r'grand\s*total[:\s]*\$?(\d+\.?\d*)',
        r'amount\s*due[:\s]*\$?(\d+\.?\d*)',
        r'balance[:\s]*\$?(\d+\.?\d*)',
    ]
    
    for pattern in total_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                result["total"] = float(match.group(1))
                break
            except ValueError:
                pass
    
    # Look for subtotal
    subtotal_match = re.search(r'sub\s*total[:\s]*\$?(\d+\.?\d*)', text, re.IGNORECASE)
    if subtotal_match:
        try:
            result["subtotal"] = float(subtotal_match.group(1))
        except ValueError:
            pass
    
    # Look for tax
    tax_patterns = [
        r'tax[:\s]*\$?(\d+\.?\d*)',
        r'sales\s*tax[:\s]*\$?(\d+\.?\d*)',
        r'vat[:\s]*\$?(\d+\.?\d*)',
    ]
    
    for pattern in tax_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                result["tax"] = float(match.group(1))
                break
            except ValueError:
                pass
    
    # Look for tip
    tip_match = re.search(r'tip[:\s]*\$?(\d+\.?\d*)', text, re.IGNORECASE)
    if tip_match:
        try:
            result["tip"] = float(tip_match.group(1))
        except ValueError:
            pass
    
    # --- Extract Line Items ---
    # Look for lines with item name and price
    item_pattern = r'^(.+?)\s+\$?(\d+\.\d{2})\s*$'
    
    for line in lines:
        # Skip lines that are totals/tax/etc
        if re.search(r'(total|tax|tip|subtotal|balance|change|cash|credit|visa|mastercard)', line, re.I):
            continue
        
        match = re.match(item_pattern, line)
        if match:
            item_name = match.group(1).strip()
            item_price = float(match.group(2))
            
            # Skip if it looks like a date or other non-item
            if len(item_name) > 2 and item_price > 0 and item_price < 10000:
                result["items"].append({
                    "description": item_name,
                    "amount": item_price
                })
    
    return result

# ===========================================
# API ENDPOINTS
# ===========================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "FinShare OCR",
        "status": "running",
        "engine": "Tesseract (FREE)",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test Tesseract is installed
        version = pytesseract.get_tesseract_version()
        return {
            "status": "healthy",
            "tesseract_version": str(version),
            "ready": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "ready": False
        }

@app.post("/scan", response_model=OCRResponse)
async def scan_receipt(file: UploadFile = File(...)):
    """
    Scan a receipt image and extract data.
    
    Accepts: JPEG, PNG, WebP images
    Returns: Extracted receipt data (merchant, date, total, items, etc.)
    """
    job_id = str(uuid.uuid4())
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if needed (handles PNGs with transparency)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        logger.info(f"Processing image: {file.filename}, size: {image.size}")
        
        # Preprocess for better OCR
        processed = preprocess_image(image)
        processed = deskew_image(processed)
        
        # Extract text with Tesseract
        raw_text, confidence = extract_text(processed)
        
        logger.info(f"OCR confidence: {confidence:.2%}")
        logger.info(f"Raw text preview: {raw_text[:200]}...")
        
        # Parse the extracted text
        parsed_data = parse_receipt_text(raw_text)
        
        # Build response
        receipt_data = ReceiptData(
            merchant=parsed_data["merchant"],
            date=parsed_data["date"],
            total=parsed_data["total"],
            subtotal=parsed_data["subtotal"],
            tax=parsed_data["tax"],
            tip=parsed_data["tip"],
            items=[ReceiptItem(**item) for item in parsed_data["items"]],
            raw_text=raw_text,
            confidence=confidence
        )
        
        return OCRResponse(
            success=True,
            job_id=job_id,
            data=receipt_data
        )
        
    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        return OCRResponse(
            success=False,
            job_id=job_id,
            error=str(e)
        )

@app.post("/scan/base64", response_model=OCRResponse)
async def scan_receipt_base64(image_data: dict):
    """
    Scan a receipt from base64-encoded image.
    Useful for mobile apps.
    
    Body: {"image": "base64_encoded_string"}
    """
    import base64
    
    job_id = str(uuid.uuid4())
    
    try:
        # Decode base64
        image_bytes = base64.b64decode(image_data.get("image", ""))
        image = Image.open(io.BytesIO(image_bytes))
        
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Same processing as file upload
        processed = preprocess_image(image)
        processed = deskew_image(processed)
        
        raw_text, confidence = extract_text(processed)
        parsed_data = parse_receipt_text(raw_text)
        
        receipt_data = ReceiptData(
            merchant=parsed_data["merchant"],
            date=parsed_data["date"],
            total=parsed_data["total"],
            subtotal=parsed_data["subtotal"],
            tax=parsed_data["tax"],
            tip=parsed_data["tip"],
            items=[ReceiptItem(**item) for item in parsed_data["items"]],
            raw_text=raw_text,
            confidence=confidence
        )
        
        return OCRResponse(
            success=True,
            job_id=job_id,
            data=receipt_data
        )
        
    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        return OCRResponse(
            success=False,
            job_id=job_id,
            error=str(e)
        )

# ===========================================
# RUN SERVER
# ===========================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
