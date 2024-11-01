import os
from typing import List, Optional


def scan_folder(path: str) -> List[str]:
    """Scan folder for markdown files."""
    md_files = []
    for root, _, files in os.walk(path):
        md_files.extend(
                os.path.join(root, file)
                for file in files
                if file.endswith('.md')
                )
    return md_files


def read_markdown(file_path: str) -> Optional[str]:
    """Read markdown file content safely."""
    try:
        with open(file_path, 'r', encoding = 'utf-8') as md:
            return md.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def format_system_prompt(system_prompt:str="./prompt/system_prompt"):
    with open(system_prompt,'r') as prompt_file:
        prompt = prompt_file.read()
        prompt_file.close()
    return prompt

def format_user_prompt(user_prompt:str= "./prompt/user_prompt"):
    with open(user_prompt,'r') as prompt_file:
        prompt = prompt_file.read()
        prompt_file.close()
    return prompt