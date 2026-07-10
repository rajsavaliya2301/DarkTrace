// Audit script to understand current state
print("=== COLLECTIONS ===");
db.getCollectionNames().forEach(function(c) {
  print("  " + c + ": " + db[c].countDocuments() + " docs");
});

print("\n=== CRAWL TARGETS ===");
db.crawl_targets.find({}, {url:1, source_type:1, category:1, created_at:1, enabled:1}).forEach(function(t) {
  print("  [ID: " + t._id + "] " + (t.enabled ? "ENABLED" : "DISABLED") + " " + (t.category || "?") + " | " + t.url.substring(0, 80));
});

print("\n=== CRAWL_JOBS ===");
db.crawl_jobs.find({}, {target_id:1, target_url:1, status:1, created_at:1, completed_at:1, pages_crawled:1, errors:1}).forEach(function(j) {
  print("  [ID: " + j._id + "] target=" + (j.target_id || "").substring(0,12) + " url=" + (j.target_url || "").substring(0,60) + " status=" + j.status + " pages=" + (j.pages_crawled || 0) + " errors=" + (j.errors || 0));
});

print("\n=== RAW CONTENT (first 5) ===");
db.raw_content.find().sort({created_at:-1}).limit(5).forEach(function(c) {
  print("  ID=" + c._id + " status=" + (c.processing_status || "?") + " size=" + (c.content_size_bytes || 0) + " text_len=" + ((c.text_content || "").length) + " has_analysis=" + (c.analysis ? "yes" : "no") + " url=" + (c.url || "").substring(0,60));
});

print("\n=== ELASTICSEARCH INDEXES ===");
var esIdx = db.raw_content.aggregate([
  {$group: {_id: null, count: {$sum: 1}}}
]).toArray();
print("  raw_content total: " + (esIdx.length > 0 ? esIdx[0].count : 0));

print("\n=== NLP ANALYSIS ===");
// Check if any doc has NLP analysis
var analyzed = db.raw_content.countDocuments({"analysis": {$exists: true}});
print("  Docs with analysis: " + analyzed);

// Check classification distribution
db.raw_content.aggregate([
  {$match: {"analysis.classification.primary": {$exists: true}}},
  {$group: {_id: "$analysis.classification.primary", count: {$sum: 1}}}
]).forEach(function(g) {
  print("  Class: " + g._id + " = " + g.count);
});

print("\nDone.");
