"""
RFM Analysis Entrypoint Wrapper
Redirects to the production modular pipeline in main.py.
"""

from main import run_pipeline

if __name__ == "__main__":
    run_pipeline()
