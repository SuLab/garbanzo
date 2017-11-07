import connexion
from garbanzo.encoder import JSONEncoder

app = connexion.App("garbanzo.__main__", specification_dir='./swagger/')
app.app.json_encoder = JSONEncoder
app.add_api('swagger.yaml',
            arguments={'title': 'A SPARQL/Wikidata Query API wrapper for Translator'},
            validate_responses=True)
application = app.app
application.run(host='0.0.0.0')
