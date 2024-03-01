import signal

from app import run_application, signal_handler

if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)
    try:
        run_application()
    except KeyboardInterrupt:
        print("Exit signal detected.")
