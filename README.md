# ระบบตรวจจับแมลง (Insect Detection System)

โครงการนี้เป็นระบบตรวจจับแมลงที่ใช้ Deep Learning โดยประกอบด้วย 2 ส่วนหลัก:

## 1. Annotation Tool (Desktop Application)

เครื่องมือสำหรับนักวิจัยในการติดป้ายกำกับรูปภาพแมลง เพื่อสร้างข้อมูลสำหรับการ train model

### คุณสมบัติ:

- **Desktop Application** ใช้งานง่าย ไม่ต้องเปิดเว็บเบราว์เซอร์
- รองรับการ bounding box annotation แบบ drag & drop
- การจัดหมวดหมู่ชนิดแมลงได้หลายคลาส
- ระบบ zoom in/out สำหรับการ annotate ที่ละเอียด
- Export ข้อมูล annotation ในรูปแบบ YOLO
- สถิติการ annotate แบบ real-time
- จัดการคลาสแมลงได้ตามต้องการ

## 2. Detection System (Desktop Application)

ระบบตรวจจับแมลงแบบ real-time ที่ใช้ YOLO model

### คุณสมบัติ:

- **Desktop Application** ใช้งานง่าย มี GUI ที่เป็นมิตร
- ตรวจจับแมลงจากกล้องแบบ real-time
- รองรับการตรวจจับจากรูปภาพเดี่ยว วิดีโอ หรือกลุ่มไฟล์
- แสดงผลการตรวจจับพร้อม confidence score และ bounding box
- สถิติการตรวจจับแบบ real-time
- บันทึกเฟรมและผลการตรวจจับได้
- ส่งออกข้อมูลสถิติและประวัติการตรวจจับ

## โครงสร้างโปรเจค

```
detectmang/
├── annotation_tool/             # Desktop annotation application
│   ├── desktop_annotation_tool.py  # โปรแกรม annotation หลัก
│   ├── app.py                   # Flask web app (สำรอง)
│   ├── static/                  # CSS, JS files
│   └── templates/               # HTML templates
├── dataset/                     # ข้อมูลรูปภาพและ annotations
│   ├── images/                  # รูปภาพต้นฉบับ
│   ├── annotations/             # ไฟล์ annotation (YOLO format)
│   └── classes.txt              # รายชื่อคลาสแมลง
├── training/                    # โค้ดสำหรับ train model
│   ├── train_yolo.py            # สคริปต์ train YOLO
│   ├── data.yaml                # การกำหนดค่าข้อมูล
│   └── models/                  # โมเดลที่ train แล้ว
├── detection/                   # ระบบตรวจจับ desktop
│   ├── desktop_detection_tool.py # โปรแกรมตรวจจับหลัก
│   ├── detect_camera.py         # ตรวจจับจากกล้อง (สำรอง)
│   └── detect_image.py          # ตรวจจับจากรูปภาพ (สำรอง)
├── requirements.txt             # Python dependencies
├── setup.py                     # สคริปต์ติดตั้ง
├── install.bat                  # ติดตั้งบน Windows
├── run_annotation_tool.bat      # เรียกใช้ annotation tool
├── run_detection.bat            # เรียกใช้ detection tool
├── run_training.bat             # เรียกใช้ training
└── README.md                    # คู่มือนี้
```

## การติดตั้ง

### วิธี 1: ติดตั้งอัตโนมัติ (Windows)

1. เรียกใช้ไฟล์ `install.bat`
2. รอให้ระบบติดตั้ง dependencies ทั้งหมด

### วิธี 2: ติดตั้งด้วยมือ

1. ติดตั้ง Python 3.8+ จาก [python.org](https://python.org)
2. ติดตั้ง dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. รันสคริปต์เซตอัพ:

   ```bash
   python setup.py
   ```

## การใช้งาน

### 1. เครื่องมือ Annotation (Desktop)

**Windows:**

```bash
run_annotation_tool.bat
```

**Manual:**

```bash
cd annotation_tool
python desktop_annotation_tool.py
```

### 2. การ Training

**Windows:**

```bash
run_training.bat
```

**Manual:**

```bash
cd training
python train_yolo.py
```

### 3. เครื่องมือตรวจจับ (Desktop)

**Windows:**

```bash
run_detection.bat
```

**Manual:**

```bash
cd detection
python desktop_detection_tool.py
```

หรือใช้เครื่องมือ command line:

```bash
# ตรวจจับจากกล้อง
python detect_camera.py --model ../training/models/insect_detector_best.pt

# ตรวจจับจากรูปภาพ
python detect_image.py --model ../training/models/insect_detector_best.pt --input your_image.jpg
```

## คุณสมบัติเพิ่มเติม

### Desktop Annotation Tool

- 🖱️ **Drag & Drop**: วาด bounding box ได้ง่าย
- 🔍 **Zoom**: ขยาย/ย่อภาพสำหรับ annotate ละเอียด
- 📊 **Real-time Stats**: ดูสถิติการ annotate แบบทันที
- 💾 **Auto Save**: บันทึกอัตโนมัติ
- 🏷️ **Class Management**: จัดการคลาสแมลงได้

### Desktop Detection Tool

- 📹 **Multi-source**: รองรับกล้อง, รูปภาพ, วิดีโอ, หลายไฟล์
- ⚡ **Real-time**: ประมวลผลแบบ real-time พร้อม FPS counter
- 📊 **Live Statistics**: สถิติการตรวจจับแบบสด
- 💾 **Export Results**: ส่งออกผลลัพธ์และสถิติ
- 🎯 **Adjustable Confidence**: ปรับระดับความแม่นยำได้

## ชนิดแมลงที่รองรับ

- ผีเสื้อ (Butterfly)
- ผึ้ง (Bee)
- มด (Ant)
- แมลงปอ (Dragonfly)
- ด้วง (Beetle)
- (เพิ่มเติมตามความต้องการ)

## ข้อมูลเพิ่มเติม

สำหรับข้อมูลเพิ่มเติมเกี่ยวกับการใช้งานแต่ละส่วน โปรดดูในโฟลเดอร์ย่อยของแต่ละระบบ
