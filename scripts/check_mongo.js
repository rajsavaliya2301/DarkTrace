var doc = db.raw_content.findOne({url: /emergingthreats/}, {text_content: 1});
print("Text length: " + (doc && doc.text_content ? doc.text_content.length : 0));
if (doc && doc.text_content) {
  print("Preview: " + doc.text_content.substring(0, 500));
}
