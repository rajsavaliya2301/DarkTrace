import bcrypt

password = "BqkwYUIslu5lAGw9iJDtVg=="
password_hash = "$2b$12$zbU.xG3IdMi40v9AZPKEGOH7nhdmrBtop8jEHDTLl1dPUIYbIFWRC"

result = bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
print(f"Password matches: {result}")

# Also test without ==
password2 = "BqkwYUIslu5lAGw9iJDtVg"
result2 = bcrypt.checkpw(password2.encode("utf-8"), password_hash.encode("utf-8"))
print(f"Password (no ==) matches: {result2}")
