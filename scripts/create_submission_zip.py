
import zipfile
import os
from pathlib import Path

def create_linux_zip(output_filename, source_dirs):
    """
    Creates a zip file where all internal paths use forward slashes (POSIX style),
    ensuring compatibility with Linux systems (like Kaggle Datasets).
    """
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        for source_dir in source_dirs:
            if not os.path.exists(source_dir):
                print(f"Warning: Directory not found: {source_dir}")
                continue
                
            print(f"Adding directory: {source_dir}")
            for root, dirs, files in os.walk(source_dir):
                # Skip __pycache__ and specific folders if needed
                if "__pycache__" in root:
                    continue

                for file in files:
                    if file.endswith(".pyc") or file == ".DS_Store":
                        continue
                        
                    file_path = os.path.join(root, file)
                    
                    # Create the archive name (arcname)
                    # This is the path inside the zip file.
                    # We ensure it uses forward slashes.
                    arcname = os.path.relpath(file_path, start=".")
                    arcname = arcname.replace(os.path.sep, "/")
                    
                    print(f"  Zipping: {arcname}")
                    zf.write(file_path, arcname)

    print(f"\nSuccessfully created {output_filename}")

if __name__ == "__main__":
    current_dir = Path.cwd()
    output_zip = "aimo_agent_code.zip"
    
    # Directories to include
    folders_to_zip = [
        "agent", 
        "corpus", 
        "analysis", 
        "youtube",
        "supply_chain"
    ]
    
    create_linux_zip(output_zip, folders_to_zip)
