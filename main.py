import signal
from dotenv import load_dotenv
from app import run_application, signal_handler

if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)
    try:
        load_dotenv()
        run_application()
    except KeyboardInterrupt:
        print("Exit signal detected.")
