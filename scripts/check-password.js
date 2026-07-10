var user = db.getSiblingDB("darktrace").users.findOne({email: "admin@darktrace.io"});
print("Email:", user.email);
print("Password hash:", user.password_hash);
