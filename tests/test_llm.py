import sys
sys.path.append("backend")
from llm_client import ask_llm

with open("tests/cassava1.jpg", "rb") as f:
    img = f.read()

print(ask_llm(
    "Identify the crop and any disease or pest visible. Give your confidence.",
    image_bytes=img,
    system="You are an agricultural advisor for Ugandan smallholder farmers.",
))