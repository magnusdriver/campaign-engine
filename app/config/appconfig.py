import yaml

def configLoader() -> dict:
    # with open("./app/config/main_config.yaml", "r") as ymlfile: # Remember to remove app folder from path when this gets deployed on GCP.
    with open("./config/main_config.yaml", "r") as ymlfile:
        return yaml.load(ymlfile, Loader=yaml.FullLoader) # Loader seems to be mandatory to make it work.

cfg = configLoader()

gcpParams = cfg["gcp-parameters"]
postgreParams = cfg["postgresql-parameters"]


