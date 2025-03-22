import os
import subprocess
import sys

def run_streamlit_app(module_name):

    # module_name = os.getenv('MODULE_NAME')

    # if not module_name:
    #     print("Error: MODULE_NAME environment variable is not set.")
    #     sys.exit(1)
    if not module_name.endswith(".py"):
        module_name = f"{module_name}.py"

    command = ["streamlit", "run", module_name]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to run the Streamlit app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage.py <module_name>")
        sys.exit(1)

    module_name = sys.argv[1]
    run_streamlit_app(module_name)
