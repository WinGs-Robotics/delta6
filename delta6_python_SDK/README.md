
## 📘 Quick Start Guide

### 1. Setup Python Environment
```bash
cd delta6_python_SDK
python3.12 -m venv venv

# Activate virtual environment
# On Ubuntu
source venv/bin/activate

# On Windows
source venv/Scripts/activate

pip install -e .
```

### 2. Burn Firmware to Arduino Nano
```bash
python burn_firmware.py --port /dev/ttyACM0
```

### 3. Run Example
```bash
python example.py --port /dev/ttyACM0
```
