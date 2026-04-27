import base64


def b64decode(b64_encoded_string: str) -> bytes:
  return base64.b64decode(b64_encoded_string.encode('utf-8'))