# TOAST : outils pour l'analyse sémiotique de Twitter (version 2)

Ce dépôt regroupe des outils permettant de constituer des corpus de tweets. Des esquisses de méthodes d'analyse sont en cours de développement.

Ces travaux techniques s'originent dans un travail de recherche conduit avec Virginie Jullliard. Voir par exemple l'article [« Entre informatique et sémiotique. Les conditions techno-méthodologiques d’une analyse de controverse sur Twitter », revue *Réseaux*, 2017/4 (n° 204)](https://www.cairn.info/revue-reseaux-2017-4-page-35.htm).

## Généralités

- L'ensemble du code source est écrit en [Python 3.7.x](https://docs.python.org/3/tutorial/index.html).
- Les données collectées ou transformées sont stockées dans une base [MongoDB](https://www.mongodb.com/).
- Seule une connaissance basique de l'API MongoDB est mobilisée (voir par exemple [ce tutoriel Python/MongoDB](https://www.w3schools.com/python/python_mongodb_getstarted.asp)).

## Captation des tweets

- La captation des tweets s'effectue via la [Streaming API](https://developer.twitter.com/en/docs/tweets/filter-realtime/overview), qui expose l'information au format [JSON](https://www.json.org/). Il faut déclarer une appllication auprès de Twitter [ici](https://developer.twitter.com/en/apps) (un comte Twitter est requis).
- Les keys & tokens personnels des API Twitter doivent être déclarés dans `secret.conf` (renommer `secret.conf.dist`).
- Les tweets captés sont stockés sans modification, ce qui est facilité par le fait que MongoDB supporte nativement le format JSON.
- La connexion à la Streaming API en Python se fait avec la bibliothèque [Tweepy](http://www.tweepy.org/). Voir surtout [la page consacrée à la Streaming API](https://tweepy.readthedocs.io/en/v3.5.0/streaming_how_to.html).
- Lancer MongoDB :
```
mkdir -p /Users/?/mongodata && mongod --dbpath=/Users/?/mongodata
```
- Déclenchement de la captation (stop : `Ctrl+C`) :
```
python3 collecte_1_tweets.py --db test --coll test --track china,eurorack
```

## Traitement

- Génération d'une « sous-collection » par filtrage du texte :
```mongo mongo_text_filter.js```

## Enrichissement : téléchargement des images & vidéos

- Déclenchement :
```
python3 collecte_2_medias.py --db test --coll test --dldir /Users/amleth/Desktop
```
- Les fichiers binaires téléchargés (images, vidéos) sont stockés sur le disque dur.
- Le [SHA1](https://en.wikipedia.org/wiki/SHA-1) de chaque fichier est calculté pour opérer un dédoublonnage technique basique.

## Enrichissement : téléchargement des conversations

- Télécharger [geckodriver](https://github.com/mozilla/geckodriver/releases) et déclarer le chemin dans `toast.conf`.
- Déclenchement :
```
python3 collecte_3_conversations.py --db test --coll test
```

## Consultation

- Interface graphique MongoDB [Robo3T](https://robomongo.org/).
- Export Excel :
```
python3 mongodb_to_excel.py --db test --coll test --xlsxfile ~/Desktop/tralala.xlsx
```

## Pistes pour l'analyse

TODO