print("=== USERS ===");
db.users.find({}).forEach(function(u) {
  print("  email: " + u.email + " role: " + (u.role || "?") + " is_active: " + (u.is_active || false));
});
