coll = 'test'
coll_filtered = 'test_filtered'

conn = new Mongo()
db = conn.getDB(coll)
db[coll_filtered].drop()
db[coll_filtered].ensureIndex({
  fulltext: 'text'
})

c = db[coll].aggregate([
  {
    $match: {
      $or: [{ fulltext: /china/gim }, { fulltext: /music/gim }]
    }
  },
  {
    $out: coll_filtered
  }
])

print(db[coll_filtered].find().count())
