---
sidebar_position: 1
---

# Installing the SDK ⚙️

This section explains how to install and set up the Delta6 Python SDK environment.

---

## 1. Download the Repository

First, clone the Delta6 project repository:

```bash
git clone https://github.com/ttopeor/Delta6_Doc.git
```

---

## 2. Set Up a Python Virtual Environment

Navigate to the Python SDK folder:

```bash
cd delta6_python_SDK
```

Create a new Python 3.12 virtual environment:

```bash
python3.12 -m venv venv
```

Activate the virtual environment:

- **On Ubuntu:**
  ```bash
  source venv/bin/activate
  ```

- **On Windows:**
  ```bash
  source venv/Scripts/activate
  ```

> 📌 **Tip:**  
Make sure you have **Python 3.12** installed.  
You can verify by running:

```bash
python3 --version
```

---

## 3. Install Dependencies

Install all required Python packages:

```bash
pip install -e .
```

This command installs the SDK in **editable mode**, which allows you to modify the code without reinstalling the package.

---

## 4. Verifying Installation

To verify that the SDK is installed correctly, simply run:

```bash
python -c "import sensor_interface"
```

If no errors are shown, the installation is successful! 🎉

---

🎯 **Congratulations!**  
You are now ready to proceed with connecting the hardware and using the Delta6 system.
