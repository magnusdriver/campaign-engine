import os, threading, time, sys, queue
from google.oauth2 import service_account
from concurrent.futures import TimeoutError
from mypubsub.pubsub import PubSub, PubSubForRegistry, PubSubForResponses, PubSubForLocation
from helpers.dbhelper import DbManager
from helpers.usershelper import UsersManager
from config.appconfig import postgreParams, gcpParams
from campaigns_engine.engine import CampaignsEngine
from mytests.dbHelperTests import runDbTests



if __name__ == "__main__":

    runDbTests()

    
    exitFlag = False

    dbManager = DbManager(postgreParams)


    registerQueue, inEngineQueueNotifications, inEngineQueueresponses, inEngineQueueLocations = [queue.Queue() for _ in range(4)]

    lock = threading.Lock()

    try:
    
        credentials = service_account.Credentials.from_service_account_file("./config/pubsub-credential.json")

        pubsubRegisterConnection = PubSubForRegistry(gcpParams["project-id"], inQueue = registerQueue, exitFlag=exitFlag)
        pubsubForNotifications = PubSub(gcpParams["project-id"], inEngineQueueNotifications, exitFlag)
        pubSubForResponses = PubSubForResponses(gcpParams["project-id"], inEngineQueueresponses, exitFlag)
        pubSubForLocations = PubSubForLocation(gcpParams["project-id"], inEngineQueueLocations, exitFlag=exitFlag)

        pubSubForLocations.pubsubSubscription(gcpParams["locations-subscription"])

        subscriptions = pubsubForNotifications.getSubscriptionsList()

        
        usersManager = UsersManager(pubsubRegisterConnection, pubsubForNotifications, dbManager, registerQueue, lock)
        campaignsEngine = CampaignsEngine(dbManager, pubsubForNotifications, pubSubForResponses, lock, inEngineQueueNotifications, inEngineQueueLocations, inEngineQueueLocations)

        pubsubRegisterConnection.pubsubSubscription(gcpParams["register-subscription-id"])

        usersManagerThread = threading.Thread(target = usersManager.userRegistry)
        usersManagerThread.daemon = True
        usersManagerThread.start()

        campaignsEngineThread = threading.Thread(target = campaignsEngine.run)
        campaignsEngineThread.daemon = True
        campaignsEngineThread.start()
        campaignsEngineThread.join()


    except KeyboardInterrupt:
        exitFlag = True
        print("Service closed...")
        sys.exit(0)

    