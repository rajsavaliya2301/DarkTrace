db.getSiblingDB("darktrace").users.updateOne(
  {email: "admin@darktrace.com"},
  {$set: {email: "admin@darktrace.io"}}
);
print("User updated:");
db.getSiblingDB("darktrace").users.findOne(
  {email: "admin@darktrace.io"},
  {email: 1, role: 1}
);
