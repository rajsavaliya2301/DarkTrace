var result = db.getSiblingDB("darktrace").users.deleteMany({});
print("Deleted users:", result.deletedCount);
