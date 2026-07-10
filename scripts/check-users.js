var users = db.getSiblingDB("darktrace").users.find().toArray();
print("Total users:", users.length);
users.forEach(function(u) {
  print("  -", u.email, "| role:", u.role);
});
