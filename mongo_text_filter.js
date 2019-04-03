conn = new Mongo()
db = conn.getDB('test')
db.nom_de_la_collection.drop()
db.nom_de_la_collection_filtree.ensureIndex({
  fulltext: 'text'
})

c = db.nom_de_la_collection.aggregate([
  {
    $match: {
      $or: [{ fulltext: /blip/gim }, { fulltext: /blop/gim }]
    }
  },
  {
    $out: 'nom_de_la_collection_filtree'
  }
])

while (c.hasNext()) {
  print(tojson(c.next()))
}

print(db.nom_de_la_collection_fitree.find().count())
