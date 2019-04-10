# TOAST : outils pour l'analyse sémiotique de Twitter (version 2)

## Principes

- captation via la _Streaming API_ avec [Tweepy](http://www.tweepy.org/)
- stockage des _tweets_ sans modification dans une base [MongoDB](https://www.mongodb.com/)
- enrichissement du corpus (images & conversations) par déclenchement manuel :
  - téléchargement des images sur le disque dur local et calcul du [SHA1](https://en.wikipedia.org/wiki/SHA-1) pour dédoublonnage technique
  - téléchargement des conversations (_scraping_ avec [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/))

## Captation

- ajuster la configuration :
  - [keys & tokens personnels des API Twitter](https://developer.twitter.com/en/apps) de l'application => `secret.conf` (renommer `secret.conf.dist`)
  - configuration générale => `toast.conf`
- lancer MongoDB :

```mkdir -p ~/mongodata && mongod --dbpath=/Users/<votre compte utilisateur ou utilisatrice>/mongodata```

- lancer la captation (stop : `Ctrl+C`) :

```python3 1_collect_tweets.py --db test --coll test --track china,eurorack```

## Enrichissement du corpus

### Images

- télécharger les images : `python3 2_get_medias.py --db test --coll test --dldir /Users/amleth/Desktop`

### Conversations

**_TODO_**

### Outils

Export Excel :

```python3 mongodb_to_excel.py --db test --coll test --xlsxfile /Users/amleth/Desktop/tralala.xlsx```

Génération d'une « sous-collection » par filtrage du texte :

```mongo mongo_text_filter.js```

## Quelques éléments de documentation technique

- [Didacticiel Python](https://docs.python.org/3/tutorial/index.html)
- [Didacticiel Python—MongoDB](https://www.w3schools.com/python/python_mongodb_getstarted.asp)
