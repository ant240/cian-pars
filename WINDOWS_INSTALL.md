# Windows Installation Guide

## Step 1: Check if Python is installed

Double-click **`check-python.bat`**

- If you see "Python is installed correctly" - go to Step 3
- If you see "Python is NOT installed" - continue to Step 2

## Step 2: Install Python (if needed)

1. **Download Python:**
   - Go to: https://www.python.org/downloads/
   - Download the latest Python 3.x version (3.8 or higher)

2. **Install Python:**
   - Run the downloaded installer
   - ⚠️ **IMPORTANT**: Check the box **"Add Python to PATH"** at the bottom!
   - Click "Install Now"
   - Wait for installation to complete

3. **Restart your computer** (important!)

4. **Verify installation:**
   - Double-click **`check-python.bat`** again
   - You should see "Python is installed correctly"

## Step 3: Run the application

**Option A: Automatic (Recommended)**
- Double-click **`start.bat`**
- Wait for dependencies to install (first time only)
- Application will open in your browser

**Option B: Manual installation first**
- Double-click **`install.bat`** (installs dependencies)
- Then double-click **`start-simple.bat`** (runs app)

**Option C: Command line**
- Open folder in File Explorer
- Type `cmd` in address bar and press Enter
- Run: `python -m streamlit run app.py`

## Troubleshooting

### Problem 1: "Python is not recognized"

**Solution:**
- Python is not installed or not in PATH
- Install Python from https://www.python.org/downloads/
- ⚠️ Check "Add Python to PATH" during installation
- Restart computer after installation

### Problem 2: Encoding errors in bat files

**Solution:**
- Use **`check-python.bat`** first
- Then use **`start-simple.bat`** for simple launch
- Or use command line method (Option C above)

### Problem 3: "streamlit is not recognized"

**Solution:**
- Run **`install.bat`** first
- Or manually: `python -m pip install -r requirements.txt`
- Then run **`start.bat`** or **`start-simple.bat`**

### Problem 4: Port already in use

**Solution:**
- Another app is using port 8501
- Close any running Streamlit apps
- Or run: `python -m streamlit run app.py --server.port 8502`

### Problem 5: Nothing happens when clicking bat file

**Solution:**
- Right-click the bat file
- Select "Run as administrator"
- Check antivirus - it might be blocking the file

## Available Bat Files

- **`check-python.bat`** - Check if Python is installed correctly
- **`start.bat`** - Full automatic launch (checks Python, installs deps, runs app)
- **`start-simple.bat`** - Simple launch (assumes everything is installed)
- **`install.bat`** - Only install dependencies

## Manual Command Line Method

If bat files don't work, use command line:

1. Open File Explorer and navigate to project folder
2. Click in address bar and type: `cmd`
3. Press Enter (command prompt opens in this folder)
4. Run these commands:

```cmd
# Check Python
python --version

# Install dependencies (first time only)
python -m pip install -r requirements.txt

# Run application
python -m streamlit run app.py
```

## Application Usage

Once running, the app will open in your browser at: http://localhost:8501

To stop the application:
- Press `Ctrl + C` in the command window
- Or close the command window

## Need Help?

If nothing works:

1. Make sure Python 3.8+ is installed: `python --version`
2. Make sure you're in the correct folder (you should see app.py)
3. Make sure you have internet connection (to install dependencies)
4. Try the manual command line method above
5. Check Windows firewall/antivirus settings

## Quick Start (Summary)

1. **`check-python.bat`** - Check Python installation
2. Install Python if needed (don't forget "Add to PATH"!)
3. Restart computer
4. **`start.bat`** - Run the app
5. Open browser: http://localhost:8501
