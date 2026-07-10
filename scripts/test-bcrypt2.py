import bcrypt

password = "BqkwYUIslu5lAGw9iJDtVg=="
password_hash = "$2b$12$MWeE5iKYc0LkQUaR3GYkHugAGGsEqGlKTtYOajB1NIsDke4oQZr8a"

result = bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
print(f"Password matches: {result}")

# Without ==
password2 = "BqkwYUIslu5lAGw9iJDtVg"
result2 = bcrypt.checkpw(password2.encode("utf-8"), password_hash.encode("utf-8"))
print(f"Password (no ==) matches: {result2}")

# What if we hash the password and compare?
new_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
print(f"New hash for this password: {new_hash.decode()}")
