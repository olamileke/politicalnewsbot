from dotenv import load_dotenv
import os.path as path

base_directory = path.dirname(__file__)

def set():
    env_path = path.join(base_directory, ".env")
    load_dotenv(env_path)

