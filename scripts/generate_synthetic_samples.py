"""
Synthetic Sample Generator for LedgerLens.
Generates 5 realistic handwritten/printed ledger sheets and receipts (Hindi + English mixed)
along with corresponding ground truth JSON files for evaluation and testing.
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)

# Select fonts
HINDI_FONT_PATH = "C:\\Windows\\Fonts\\mangal.ttf" if os.path.exists("C:\\Windows\\Fonts\\mangal.ttf") else None
ARIAL_FONT_PATH = "C:\\Windows\\Fonts\\arial.ttf" if os.path.exists("C:\\Windows\\Fonts\\arial.ttf") else None

def get_font(size=18, devanagari=False):
    try:
        if devanagari and HINDI_FONT_PATH:
            return ImageFont.truetype(HINDI_FONT_PATH, size)
        elif ARIAL_FONT_PATH:
            return ImageFont.truetype(ARIAL_FONT_PATH, size)
    except Exception:
        pass
    return ImageFont.load_default()

def create_sample_1():
    # Sample 1: Sharma General Store & Kirana
    img = Image.new("RGB", (700, 850), color=(253, 250, 243))
    draw = ImageDraw.Draw(img)
    
    # Title & Header
    draw.rectangle([(20, 20), (680, 830)], outline=(120, 110, 100), width=2)
    title_font = get_font(26)
    sub_font = get_font(16)
    header_font = get_font(18)
    body_font = get_font(18)
    
    draw.text((150, 40), "SHARMA GENERAL STORE", fill=(30, 30, 30), font=title_font)
    draw.text((220, 75), "Main Bazaar, Delhi - Khata Bahi", fill=(80, 80, 80), font=sub_font)
    draw.text((500, 110), "Date: 12/10/2026", fill=(40, 40, 40), font=sub_font)
    draw.line([(30, 135), (670, 135)], fill=(120, 120, 120), width=2)
    
    # Table headers
    draw.text((40, 145), "Item / Description", fill=(30, 30, 30), font=header_font)
    draw.text((360, 145), "Qty", fill=(30, 30, 30), font=header_font)
    draw.text((430, 145), "Rate", fill=(30, 30, 30), font=header_font)
    draw.text((550, 145), "Amount", fill=(30, 30, 30), font=header_font)
    draw.line([(30, 175), (670, 175)], fill=(150, 150, 150), width=1)
    
    # Rows
    rows = [
        ("Atta (Wheat Flour) 10kg", "1", "380", "380.00"),
        ("Mustard Oil (Sarson Tel)", "2", "160", "320.00"),
        ("Sugar (Cheeni) 5kg", "5", "44", "220.00"),
        ("Shop Electricity Bill (Bijli)", "1", "1450", "1450.00"),
    ]
    
    y = 200
    for item, qty, rate, amt in rows:
        draw.text((40, y), item, fill=(20, 20, 20), font=body_font)
        draw.text((370, y), qty, fill=(20, 20, 20), font=body_font)
        draw.text((440, y), rate, fill=(20, 20, 20), font=body_font)
        draw.text((550, y), f"Rs {amt}", fill=(20, 20, 20), font=body_font)
        draw.line([(30, y + 35), (670, y + 35)], fill=(220, 220, 220), width=1)
        y += 55

    img_path = os.path.join(SAMPLES_DIR, "sample_1_kiranastore.png")
    img.save(img_path)
    
    ground_truth = [
        {"date": "2026-10-12", "party": "Sharma General Store", "item": "Atta (Wheat Flour) 10kg", "quantity": 1.0, "amount": 380.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-12", "party": "Sharma General Store", "item": "Mustard Oil (Sarson Tel)", "quantity": 2.0, "amount": 320.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-12", "party": "Sharma General Store", "item": "Sugar (Cheeni) 5kg", "quantity": 5.0, "amount": 220.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-12", "party": "Electricity Board", "item": "Shop Electricity Bill (Bijli)", "quantity": 1.0, "amount": 1450.0, "currency": "INR", "type": "expense", "confidence": 1.0},
    ]
    with open(os.path.join(SAMPLES_DIR, "sample_1_kiranastore.json"), "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

def create_sample_2():
    # Sample 2: Gupta Tea Stall & Snacks (Chai Bill)
    img = Image.new("RGB", (650, 750), color=(255, 252, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(25, 25), (625, 725)], outline=(140, 100, 80), width=2)
    
    title_font = get_font(24)
    body_font = get_font(18)
    sub_font = get_font(16)
    
    draw.text((160, 45), "GUPTA TEA STALL & SNACKS", fill=(80, 40, 10), font=title_font)
    draw.text((220, 80), "Station Road, Lucknow", fill=(100, 70, 40), font=sub_font)
    draw.text((450, 115), "Date: 14-10-2026", fill=(50, 50, 50), font=sub_font)
    draw.line([(40, 140), (610, 140)], fill=(140, 100, 80), width=2)
    
    rows = [
        ("Special Masala Chai", "15", "10", "150.00"),
        ("Samosa", "10", "12", "120.00"),
        ("Milk Supply (Amul)", "10", "62", "620.00"),
        ("LPG Gas Cylinder refill", "1", "950", "950.00"),
    ]
    
    y = 170
    draw.text((50, y), "Description", fill=(30, 30, 30), font=sub_font)
    draw.text((340, y), "Qty", fill=(30, 30, 30), font=sub_font)
    draw.text((420, y), "Rate", fill=(30, 30, 30), font=sub_font)
    draw.text((520, y), "Amount (Rs)", fill=(30, 30, 30), font=sub_font)
    draw.line([(40, y + 25), (610, y + 25)], fill=(180, 150, 130), width=1)
    
    y = 215
    for item, qty, rate, amt in rows:
        draw.text((50, y), item, fill=(20, 20, 20), font=body_font)
        draw.text((350, y), qty, fill=(20, 20, 20), font=body_font)
        draw.text((430, y), rate, fill=(20, 20, 20), font=body_font)
        draw.text((530, y), amt, fill=(20, 20, 20), font=body_font)
        draw.line([(40, y + 35), (610, y + 35)], fill=(230, 215, 200), width=1)
        y += 55

    img_path = os.path.join(SAMPLES_DIR, "sample_2_chai_tea_bill.png")
    img.save(img_path)
    
    ground_truth = [
        {"date": "2026-10-14", "party": "Counter Sales", "item": "Special Masala Chai", "quantity": 15.0, "amount": 150.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-14", "party": "Counter Sales", "item": "Samosa", "quantity": 10.0, "amount": 120.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-14", "party": "Amul", "item": "Milk Supply (Amul)", "quantity": 10.0, "amount": 620.0, "currency": "INR", "type": "expense", "confidence": 1.0},
        {"date": "2026-10-14", "party": "Gas Agency", "item": "LPG Gas Cylinder refill", "quantity": 1.0, "amount": 950.0, "currency": "INR", "type": "expense", "confidence": 1.0},
    ]
    with open(os.path.join(SAMPLES_DIR, "sample_2_chai_tea_bill.json"), "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

def create_sample_3():
    # Sample 3: Hindi Khata (Devanagari handwritten ledger style)
    img = Image.new("RGB", (720, 800), color=(250, 248, 238))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (700, 780)], outline=(100, 100, 120), width=2)
    
    title_font = get_font(24, devanagari=True)
    body_font = get_font(18, devanagari=True)
    sub_font = get_font(16, devanagari=True)
    
    draw.text((220, 35), "दैनिक रोकड़ बही (Roznamcha)", fill=(20, 20, 20), font=title_font)
    draw.text((480, 80), "दिनांक: 15/10/2026", fill=(40, 40, 40), font=sub_font)
    draw.line([(30, 115), (690, 115)], fill=(100, 100, 120), width=2)
    
    rows = [
        ("रमेश किराना - दाल अरहर (Dal)", "3", "420.00", "जमा / Sale"),
        ("राजू भईया - चावल बासमती (Rice)", "10", "750.00", "जमा / Sale"),
        ("टेंपो भाड़ा (Tempo Transport)", "1", "350.00", "खर्चा / Exp"),
        ("दुकान झाड़ू पोछा (Cleaning)", "1", "200.00", "खर्चा / Exp"),
    ]
    
    y = 135
    draw.text((40, y), "विवरण / पार्टी (Description)", fill=(30, 30, 30), font=sub_font)
    draw.text((380, y), "मात्रा", fill=(30, 30, 30), font=sub_font)
    draw.text((460, y), "रुपये (Amt)", fill=(30, 30, 30), font=sub_font)
    draw.text((580, y), "प्रकार (Type)", fill=(30, 30, 30), font=sub_font)
    draw.line([(30, y + 30), (690, y + 30)], fill=(180, 180, 180), width=1)
    
    y = 185
    for item, qty, amt, t in rows:
        draw.text((40, y), item, fill=(20, 20, 20), font=body_font)
        draw.text((390, y), qty, fill=(20, 20, 20), font=body_font)
        draw.text((470, y), amt, fill=(20, 20, 20), font=body_font)
        draw.text((585, y), t, fill=(20, 20, 20), font=body_font)
        draw.line([(30, y + 40), (690, y + 40)], fill=(225, 225, 225), width=1)
        y += 60

    img_path = os.path.join(SAMPLES_DIR, "sample_3_hindi_khata.png")
    img.save(img_path)
    
    ground_truth = [
        {"date": "2026-10-15", "party": "रमेश किराना", "item": "दाल अरहर (Dal)", "quantity": 3.0, "amount": 420.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-15", "party": "राजू भईया", "item": "चावल बासमती (Rice)", "quantity": 10.0, "amount": 750.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-15", "party": "Tempo Driver", "item": "टेंपो भाड़ा (Tempo Transport)", "quantity": 1.0, "amount": 350.0, "currency": "INR", "type": "expense", "confidence": 1.0},
        {"date": "2026-10-15", "party": "Staff", "item": "दुकान झाड़ू पोछा (Cleaning)", "quantity": 1.0, "amount": 200.0, "currency": "INR", "type": "expense", "confidence": 1.0},
    ]
    with open(os.path.join(SAMPLES_DIR, "sample_3_hindi_khata.json"), "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)

def create_sample_4():
    # Sample 4: Kisan Hardware & Electricals (with unusual high expense)
    img = Image.new("RGB", (720, 820), color=(252, 252, 250))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (700, 800)], outline=(50, 70, 90), width=2)
    
    title_font = get_font(24)
    body_font = get_font(18)
    sub_font = get_font(16)
    
    draw.text((160, 40), "KISAN HARDWARE & ELECTRICALS", fill=(30, 40, 60), font=title_font)
    draw.text((260, 75), "GST: 07AAAAA0000A1Z5", fill=(80, 80, 80), font=sub_font)
    draw.text((490, 110), "Date: 16/10/2026", fill=(40, 40, 40), font=sub_font)
    draw.line([(30, 135), (690, 135)], fill=(50, 70, 90), width=2)
    
    rows = [
        ("LED Bulb 9W (Bajaj)", "6", "80", "480.00", "Sale"),
        ("PVC Pipe 1 inch", "4", "160", "640.00", "Sale"),
        ("Wholesale Stock (Sharma Tools)", "1", "18500", "18500.00", "Expense"),
        ("Labour charges (Palledari)", "2", "250", "500.00", "Expense"),
    ]
    
    y = 150
    draw.text((40, y), "Particulars", fill=(30, 30, 30), font=sub_font)
    draw.text((360, y), "Qty", fill=(30, 30, 30), font=sub_font)
    draw.text((430, y), "Rate", fill=(30, 30, 30), font=sub_font)
    draw.text((520, y), "Amount (INR)", fill=(30, 30, 30), font=sub_font)
    draw.line([(30, y + 25), (690, y + 25)], fill=(160, 160, 160), width=1)
    
    y = 190
    for item, qty, rate, amt, t in rows:
        draw.text((40, y), item, fill=(20, 20, 20), font=body_font)
        draw.text((370, y), qty, fill=(20, 20, 20), font=body_font)
        draw.text((440, y), rate, fill=(20, 20, 20), font=body_font)
        draw.text((530, y), amt, fill=(20, 20, 20), font=body_font)
        draw.line([(30, y + 35), (690, y + 35)], fill=(220, 220, 220), width=1)
        y += 55

    img_path = os.path.join(SAMPLES_DIR, "sample_4_hardware_invoice.png")
    img.save(img_path)
    
    ground_truth = [
        {"date": "2026-10-16", "party": "Counter Customer", "item": "LED Bulb 9W (Bajaj)", "quantity": 6.0, "amount": 480.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-16", "party": "Counter Customer", "item": "PVC Pipe 1 inch", "quantity": 4.0, "amount": 640.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-16", "party": "Sharma Tools", "item": "Wholesale Stock (Sharma Tools)", "quantity": 1.0, "amount": 18500.0, "currency": "INR", "type": "expense", "confidence": 1.0},
        {"date": "2026-10-16", "party": "Labour", "item": "Labour charges (Palledari)", "quantity": 2.0, "amount": 500.0, "currency": "INR", "type": "expense", "confidence": 1.0},
    ]
    with open(os.path.join(SAMPLES_DIR, "sample_4_hardware_invoice.json"), "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

def create_sample_5():
    # Sample 5: Daily Ledger Mixed (Hindi/English)
    img = Image.new("RGB", (720, 800), color=(254, 251, 244))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (700, 780)], outline=(80, 80, 80), width=2)
    
    title_font = get_font(24, devanagari=True)
    body_font = get_font(18, devanagari=True)
    sub_font = get_font(16, devanagari=True)
    
    draw.text((230, 40), "Daily Khata Bahi (दैनिक खाता)", fill=(30, 30, 30), font=title_font)
    draw.text((500, 80), "Date: 18-10-2026", fill=(50, 50, 50), font=sub_font)
    draw.line([(30, 115), (690, 115)], fill=(100, 100, 100), width=2)
    
    rows = [
        ("Vikram - Mobile Recharge", "1", "499.00", "Jama (Sale)"),
        ("Sunil - Spices Masala Packets", "8", "360.00", "Jama (Sale)"),
        ("Stationery (bill book & pen)", "2", "180.00", "Kharch (Exp)"),
        ("Shop Rent advance (दुकान किराया)", "1", "8000.00", "Kharch (Exp)"),
    ]
    
    y = 140
    draw.text((40, y), "Party / Particulars", fill=(40, 40, 40), font=sub_font)
    draw.text((380, y), "Qty", fill=(40, 40, 40), font=sub_font)
    draw.text((470, y), "Amount (Rs)", fill=(40, 40, 40), font=sub_font)
    draw.text((600, y), "Type", fill=(40, 40, 40), font=sub_font)
    draw.line([(30, y + 25), (690, y + 25)], fill=(170, 170, 170), width=1)
    
    y = 180
    for item, qty, amt, t in rows:
        draw.text((40, y), item, fill=(20, 20, 20), font=body_font)
        draw.text((390, y), qty, fill=(20, 20, 20), font=body_font)
        draw.text((475, y), amt, fill=(20, 20, 20), font=body_font)
        draw.text((600, y), t, fill=(20, 20, 20), font=body_font)
        draw.line([(30, y + 35), (690, y + 35)], fill=(225, 225, 225), width=1)
        y += 55

    img_path = os.path.join(SAMPLES_DIR, "sample_5_daily_ledger_mixed.png")
    img.save(img_path)
    
    ground_truth = [
        {"date": "2026-10-18", "party": "Vikram", "item": "Mobile Recharge", "quantity": 1.0, "amount": 499.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-18", "party": "Sunil", "item": "Spices Masala Packets", "quantity": 8.0, "amount": 360.0, "currency": "INR", "type": "sale", "confidence": 1.0},
        {"date": "2026-10-18", "party": "Stationery Shop", "item": "bill book & pen", "quantity": 2.0, "amount": 180.0, "currency": "INR", "type": "expense", "confidence": 1.0},
        {"date": "2026-10-18", "party": "Landlord", "item": "Shop Rent advance (दुकान किराया)", "quantity": 1.0, "amount": 8000.0, "currency": "INR", "type": "expense", "confidence": 1.0},
    ]
    with open(os.path.join(SAMPLES_DIR, "sample_5_daily_ledger_mixed.json"), "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("Generating 5 synthetic sample ledger/receipt images and ground truth JSON files...")
    create_sample_1()
    create_sample_2()
    create_sample_3()
    create_sample_4()
    create_sample_5()
    print("All 5 synthetic samples generated successfully in:", SAMPLES_DIR)
