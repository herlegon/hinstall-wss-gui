from pathlib import Path
import subprocess



def get_python_version(python_executable: Path) -> str:
    # Run the python executable with the '-V' or '--version' flag to get the version
    version: str = ""
    try:
        result = subprocess.run(
            [str(python_executable), '--version'],
            capture_output=True,
            text=True
        )
        version = result.stdout.strip()
    except:
        pass
    return version


