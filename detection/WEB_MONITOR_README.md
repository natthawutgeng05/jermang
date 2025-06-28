# 📱 Web-based Insect Detection Monitor

Real-time insect detection system accessible from any device with web browser, including mobile phones for remote monitoring.

## 🚀 Features

### 📱 Mobile-First Design
- **Mobile-optimized interface** for smartphones and tablets
- **Responsive design** adapts to any screen size
- **Touch-friendly controls** for mobile devices
- **Real-time video streaming** with optimized bandwidth

### 🌐 Remote Access
- **Access from anywhere** on your network
- **Multiple device support** - monitor from computer and phone simultaneously
- **Real-time updates** using WebSocket technology
- **No app installation required** - works in any web browser

### 🔧 Advanced Features
- **YOLO11 auto-loading** for best performance
- **Live statistics** and detection counts
- **Detection history** with timestamps
- **Adjustable settings** (confidence threshold, camera selection)
- **Session timing** and monitoring analytics

## 🛠️ Setup & Usage

### 1. Quick Start
```bash
# Run the batch file
run_web_monitor.bat

# Or start manually
cd detection
python web_monitor.py
```

### 2. Access URLs
- **Desktop/Computer**: `http://localhost:5000`
- **Mobile/Phone**: `http://[your-ip-address]:5000/mobile`
- **Settings**: Available through web interface

### 3. Find Your IP Address
```cmd
# Windows Command Prompt
ipconfig

# Look for "IPv4 Address" under your active network adapter
# Example: 192.168.1.100
```

### 4. Mobile Access
1. Connect your phone to the **same WiFi network** as your computer
2. Open web browser on your phone
3. Go to: `http://192.168.1.100:5000/mobile` (replace with your actual IP)
4. Start monitoring remotely!

## 📱 Mobile Interface

### Main Features
- **Live video feed** with detection overlays
- **One-tap start/stop** detection
- **Real-time statistics** display
- **Detection history** with recent alerts
- **Settings panel** for adjustments
- **Session timer** to track monitoring time

### Touch Controls
- **Tap Start/Stop** to control detection
- **Tap Settings (⚙️)** to open settings panel
- **Tap Clear (🗑️)** to reset detection history
- **Pull to refresh** detection feed

## 🔧 Configuration

### Camera Settings
- **Camera ID**: Select which camera to use (0, 1, 2, ...)
- **Confidence Threshold**: Adjust sensitivity (0.1 to 0.9)
- **Auto-save settings** across sessions

### Network Settings
Default configuration:
- **Host**: `0.0.0.0` (accessible from other devices)
- **Port**: `5000`
- **Protocol**: HTTP with WebSocket for real-time updates

### Custom Configuration
```bash
# Start with custom settings
python web_monitor.py --host 0.0.0.0 --port 8080

# Access at: http://your-ip:8080
```

## 🎯 Use Cases

### 🏡 Home Monitoring
- **Garden pest detection** from inside the house
- **24/7 monitoring** without staying at the computer
- **Check from bed** using your phone

### 🏢 Research & Field Work
- **Remote field station monitoring** 
- **Multiple researcher access** to same detection system
- **Data collection** from multiple locations

### 🎓 Educational
- **Classroom demonstrations** on student devices
- **Remote learning** support
- **Real-time collaboration** on insect identification

## 📊 Real-time Features

### Live Video Stream
- **30 FPS video** with detection overlays
- **Adaptive quality** based on network speed
- **Automatic reconnection** if connection drops

### Detection Analytics
- **Total detection count** for current session
- **Per-class statistics** showing which insects detected
- **Session duration** tracking
- **Recent detection history** with timestamps

### Notifications
- **New detection alerts** appear instantly
- **Connection status** indicators
- **Visual feedback** for all actions

## 🔒 Security Notes

### Network Access
- **Local network only** by default (WiFi/LAN)
- **No internet access required** for basic operation
- **Firewall friendly** - uses standard HTTP port

### Privacy
- **No data uploaded** to external servers
- **Local processing only** - all detection happens on your computer
- **Your camera stays private** - only accessible within your network

## 🛠️ Troubleshooting

### Common Issues

#### Can't Access from Mobile
1. **Check WiFi**: Ensure phone and computer on same network
2. **Check IP**: Use `ipconfig` to find correct IP address
3. **Check Firewall**: Windows may block incoming connections
4. **Try different port**: `python web_monitor.py --port 8080`

#### Video Not Loading
1. **Check camera**: Make sure camera works in other apps
2. **Camera permissions**: Ensure Python can access camera
3. **Try different camera ID**: Change in settings (0, 1, 2...)

#### Slow Performance
1. **Reduce quality**: Lower confidence threshold
2. **Close other apps**: Free up system resources
3. **Check network**: Ensure good WiFi signal

### Advanced Troubleshooting
```bash
# Check if Flask dependencies installed
pip install flask flask-socketio eventlet

# Test camera access
python -c "import cv2; print('Camera test:', cv2.VideoCapture(0).isOpened())"

# Check network connectivity
ping [your-computer-ip]
```

## 🔧 Development

### API Endpoints
- `GET /api/status` - System status
- `POST /api/detection/start` - Start detection
- `POST /api/detection/stop` - Stop detection
- `GET/POST /api/settings` - Manage settings
- `GET /api/history` - Detection history

### WebSocket Events
- `connect/disconnect` - Connection management
- `frame` - Video frame updates
- `stats_update` - Statistics updates
- `new_detection` - Real-time detection alerts

## 📈 Future Enhancements

- [ ] **Push notifications** to mobile devices
- [ ] **Multi-camera support** 
- [ ] **Recording capabilities** 
- [ ] **Cloud storage integration**
- [ ] **User authentication**
- [ ] **Dark/Light theme toggle**

---

**🐛 Happy Remote Bug Monitoring! 📱**
