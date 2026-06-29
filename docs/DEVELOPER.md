# Cognify v3.0 Developer Guide

This guide describes the local setup, development conventions, and testing procedures.

---

## 1. Local Setup
Create a virtual environment and install development dependencies:
```bash
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## 2. Running Regression Tests
All modifications must validate against the integration regression suite. Run regression tests:
```bash
python run_regression.py
```
This runs all 27 integration tests (including Memory, APD, NBIRT, Digital Twins, and Hardening validation) and reports baseline benchmarks.

---

## 3. Dynamic API Docs
Start the local server:
```bash
python app.py
```
Navigate to `http://localhost:10000/docs` to access the interactive Swagger UI and review API schemas. Spec changes can be centralizing inside `swagger.py`.
