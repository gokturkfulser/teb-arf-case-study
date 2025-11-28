import sys
import subprocess
import time
import signal
import os
import platform
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_service_in_terminal(name, script_path, port):
    """Start a service in a new terminal window"""
    print(f"\n{'='*60}")
    print(f"Starting {name} service in new terminal...")
    print(f"{'='*60}")
    print("Note: First-time startup may take longer due to model downloads")
    
    script_abs = script_path.resolve()
    cwd = str(project_root)
    
    if platform.system() == "Windows":
        title = f"{name} Service - Port {port}"
        cmd = f'start "{title}" cmd /k "cd /d {cwd} && {sys.executable} {script_abs}"'
        process = subprocess.Popen(cmd, shell=True)
    else:
        terminal_cmd = ["gnome-terminal", "--title", f"{name} Service", "--", "bash", "-c"]
        cmd = f"cd {cwd} && {sys.executable} {script_abs}; exec bash"
        process = subprocess.Popen(terminal_cmd + [cmd])
    
    return process

def wait_for_service_ready(name, port, max_wait=None):
    """Wait for service to be ready by checking health endpoint"""
    print(f"Waiting for {name} to be ready on port {port}...")
    if max_wait:
        print(f"(Will wait up to {max_wait} seconds)")
    else:
        print("(No timeout - will wait until service is ready)")
    
    start_time = time.time()
    
    import requests
    consecutive_success = 0
    required_success = 3
    last_progress_time = start_time
    ready_message_shown = False
    
    while max_wait is None or (time.time() - start_time < max_wait):
        elapsed = int(time.time() - start_time)
        
        if elapsed > 0 and elapsed % 10 == 0 and elapsed != int(last_progress_time - start_time):
            print(f"\nStill waiting... ({elapsed}s elapsed)", end="", flush=True)
            last_progress_time = time.time()
        
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=10)
            if response.status_code == 200:
                consecutive_success += 1
                if consecutive_success >= required_success and not ready_message_shown:
                    elapsed_total = int(time.time() - start_time)
                    print(f"\n✓ {name} service is ready and healthy! (took {elapsed_total}s)")
                    ready_message_shown = True
                    return True
            else:
                consecutive_success = 0
        except requests.exceptions.RequestException:
            consecutive_success = 0
        except Exception as e:
            consecutive_success = 0
        
        time.sleep(3)
        if consecutive_success == 0 and not ready_message_shown:
            print(".", end="", flush=True)
    
    if max_wait:
        print(f"\n✗ {name} service failed to start in {max_wait} seconds")
    return False

def stop_service(process, name, port):
    """Stop a service process by closing its terminal window"""
    if process:
        print(f"Stopping {name} service...", end=" ", flush=True)
        try:
            if platform.system() == "Windows":
                subprocess.run(f'taskkill /FI "WINDOWTITLE eq {name} Service - Port {port}*" /T /F', shell=True, capture_output=True, timeout=5)
                time.sleep(1)
            else:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
            print(f"✓")
        except Exception as e:
            print(f"⚠ (may need manual close)")

def main():
    """Run all services in separate terminal windows"""
    processes = {}
    service_ports = {}
    
    try:
        stt_script = project_root / "services" / "stt" / "main.py"
        rag_script = project_root / "services" / "rag" / "main.py"
        gateway_script = project_root / "services" / "gateway" / "main.py"
        
        print("Starting all services in separate terminal windows...")
        print("You will see each service's output in its own terminal window.\n")
        
        processes["STT"] = start_service_in_terminal("STT", stt_script, 8001)
        service_ports["STT"] = 8001
        time.sleep(2)
        
        if not wait_for_service_ready("STT", 8001, max_wait=None):
            return 1
        
        print("\nWaiting 5 seconds before starting next service...")
        time.sleep(5)
        
        processes["RAG"] = start_service_in_terminal("RAG", rag_script, 8002)
        service_ports["RAG"] = 8002
        time.sleep(2)
        
        if not wait_for_service_ready("RAG", 8002, max_wait=None):
            print("\nNote: STT service is still running in its terminal window")
            return 1
        
        print("\nWaiting 5 seconds before starting next service...")
        time.sleep(5)
        
        processes["Gateway"] = start_service_in_terminal("Gateway", gateway_script, 8000)
        service_ports["Gateway"] = 8000
        time.sleep(2)
        
        if not wait_for_service_ready("Gateway", 8000, max_wait=None):
            print("\nNote: STT and RAG services are still running in their terminal windows")
            return 1
        
        print(f"\n{'='*60}")
        print("All services are running!")
        print(f"{'='*60}")
        print("\nServices (each in its own terminal window):")
        print("  - STT Service:    http://localhost:8001")
        print("  - RAG Service:    http://localhost:8002")
        print("  - Gateway Service: http://localhost:8000")
        print("\nEach service is running in a separate terminal window.")
        print("You can see their outputs in those windows.")
        print("\nPress Ctrl+C here to stop all services and close terminal windows.")
        print(f"{'='*60}\n")
        
        print("Monitoring services... Press Ctrl+C to stop all services.\n")
        
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n\nShutting down all services...")
        for name, process in processes.items():
            port = service_ports.get(name, 0)
            stop_service(process, name, port)
        print("\nAll services stopped.")
        return 0
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        for name, process in processes.items():
            port = service_ports.get(name, 0)
            stop_service(process, name, port)

if __name__ == "__main__":
    sys.exit(main())

