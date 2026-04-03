"""
Launcher for Radiation Dose Recorder Desktop Application
Starts Streamlit server and opens browser automatically
"""
import os
import sys
import subprocess
import webbrowser
import threading
import time
import socket
from pathlib import Path

def find_free_port():
    """Find a free port to use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def wait_for_server(host, port, timeout=30):
    """Wait for Streamlit server to be ready"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                if result == 0:
                    return True
        except:
            pass
        time.sleep(0.5)
    return False

def main():
    print("=" * 60)
    print("🏥 Radiation Dose Recorder")
    print("=" * 60)
    print()
    print("🚀 Starting application...")
    print()
    
    # Find app.py location
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = Path(sys.executable).parent
        app_path = app_dir / "app.py"
    else:
        # Running as script
        app_dir = Path(__file__).parent
        app_path = app_dir / "app.py"
    
    if not app_path.exists():
        print(f"❌ Error: app.py not found at {app_path}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Find free port
    port = find_free_port()
    host = "localhost"
    
    print(f"🌐 Server will start at: http://{host}:{port}")
    print()
    print("💡 The application will open in your default browser.")
    print("   You can close the server by closing this window.")
    print()
    
    # Start Streamlit server
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", str(port),
        "--server.headless", "true",
        "--server.address", host,
        "--browser.gatherUsageStats", "false",
        "--theme.base", "light"
    ]
    
    # Set environment variables for Tesseract
    env = os.environ.copy()
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR",
        r"C:\Program Files (x86)\Tesseract-OCR",
    ]
    
    for tesseract_path in tesseract_paths:
        if os.path.exists(tesseract_path):
            env["TESSDATA_PREFIX"] = tesseract_path
            # Add to PATH
            env["PATH"] = tesseract_path + os.pathsep + env.get("PATH", "")
            break
    
    print("🔄 Starting Streamlit server...")
    process = subprocess.Popen(
        streamlit_cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    
    # Wait for server to be ready
    print("⏳ Waiting for server to start...")
    if wait_for_server(host, port):
        print("✅ Server is ready!")
        print()
        print("🌐 Opening browser...")
        
        # Open browser
        url = f"http://{host}:{port}"
        webbrowser.open(url)
        
        print()
        print("=" * 60)
        print("✨ Application is running!")
        print("=" * 60)
        print()
        print("📌 To access the application:")
        print(f"   URL: {url}")
        print()
        print("🛑 To stop the application:")
        print("   Close this window or press Ctrl+C")
        print()
        
        # Keep running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            process.terminate()
            process.wait()
            print("✅ Application stopped.")
    else:
        print("❌ Failed to start server!")
        print("Error output:")
        stderr = process.stderr.read().decode()
        print(stderr)
        input("Press Enter to exit...")
        process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()
