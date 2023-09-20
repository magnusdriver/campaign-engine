from google.cloud import pubsub_v1
import json, concurrent.futures, threading
from models.messaging_models import IncomingLoginMessage, LocationMessage, CampaignResponse
from helpers.stringshelper import getIdFromString
from helpers.googlesigninhelper import verifyGoogleIdToken

class PubSub:

    topics = []
    subscriptions = {}
    subscription_flags = {}
    
    def __init__(self, project_id, inQueue = None, exitFlag = False):
        self.project_id = project_id
        self.inQueue = inQueue
        self.exitFlag = exitFlag

    def createTopic(self, topic_id):
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(self.project_id, topic_id)

        topic = publisher.create_topic(request={"name": topic_path})
        self.topics.append(topic_id)
        print(f"Created topic: {topic.name}")

    def createSubscription(self, subscriptionId, topicId, filter = None):
        publisher = pubsub_v1.PublisherClient()
        subscriber = pubsub_v1.SubscriberClient()
        topic_path = publisher.topic_path(self.project_id, topicId)
        subscription_path = subscriber.subscription_path(self.project_id, subscriptionId)
        

        with subscriber:
            subscription = subscriber.create_subscription(
                request={"name": subscription_path, "topic": topic_path, "filter": filter}
            )
            print(f"Created subscription: {subscription}")

    def deletePubSubSubscription(self, subscriptionId):
        try:
            subscriber = pubsub_v1.SubscriberClient()
            subscription_path = subscriber.subscription_path(self.project_id, subscriptionId)

            with subscriber:
                subscriber.delete_subscription(request={"subscription": subscription_path})
        except Exception as e:
            print(f"Error deleting PubSub subscription: {e}")



    def callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        print(f"Received {message}.")

        message.ack()

    def pubsubSubscription(self, subscription_id):

        def subscriptionFunction(subscription_id, exitFlag):
            subscriber = pubsub_v1.SubscriberClient()
            # The `subscription_path` method creates a fully qualified identifier
            # in the form `projects/{project_id}/subscriptions/{subscription_id}`
            
            subscription_path = subscriber.subscription_path(self.project_id, subscription_id)


            streaming_pull_future = subscriber.subscribe(subscription_path, callback=self.callback)

            print(f"Listening for messages on {subscription_path}..\n")

            # Wrap subscriber in a 'with' block to automatically call close() when done.
            with subscriber:
                
                while not exitFlag:
                    try:
                        # When `timeout` is not set, result() will block indefinitely,
                        # unless an exception is encountered first.
                        
                        streaming_pull_future.result(timeout=10)
                    except concurrent.futures.TimeoutError:
                        
                        pass
                    else:
                            streaming_pull_future.cancel()  # Trigger the shutdown.
                            print('Canceling pubsub subscription')
                            streaming_pull_future.result()  # Block until the shutdown is complete.
                    
        
        self.subscription_flags[subscription_id] = False
        self.subscriptions[subscription_id] = threading.Thread(target = subscriptionFunction, args=[subscription_id, self.subscription_flags[subscription_id]])
        self.subscriptions[subscription_id].daemon = True
        self.subscriptions[subscription_id].start()
    
    def publish(self, data, topicId, attributes = None):
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(self.project_id, topicId)
        if attributes == None:
            future = publisher.publish(topic_path, data)
        else:
            future = publisher.publish(topic_path, data, **attributes)
        print(future.result())

    def getSubscriptionsList(self):
        subscriber = pubsub_v1.SubscriberClient()
        project_path = f"projects/{self.project_id}"


        with subscriber:
            subscriptionsList = [subscribe.name.split("/")[-1] for subscribe in subscriber.list_subscriptions(request={"project": project_path})]

        return subscriptionsList


class PubSubForRegistry(PubSub):

    # Specific callback for users sign-in.
    def callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        data = json.loads(message.data)
        
        args = {
            "accountMessageType": message.attributes['accountMessageType'],
            "idToken": data.get("idToken"),
            "oncar": data.get("oncar"),
            "campaign_id": data.get("campaign_id"),
            "subscription_status": data.get("subscription_status")
        }
        
        incomingLoginMessage = IncomingLoginMessage(**args)
        self.inQueue.put(incomingLoginMessage)
        message.ack()

class PubSubForLocation(PubSub):

    def callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        data = json.loads(message.data)

        try:
            tokenData = verifyGoogleIdToken(data['tokenId'])


            newLocationMessage = LocationMessage(
                tokenData['sub'],
                data['latitude'],
                data['longitude'],
                data['position_time']
            )

            print("New location message.")
            self.inQueue.put(newLocationMessage)

            message.ack()

        except Exception as e:
            message.ack()
            return

class PubSubForResponses(PubSub):

    def callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        data = json.loads(message)

        try:
            tokenData = verifyGoogleIdToken(data['token'])
        except Exception:
            message.ack()
            return

        newResponseMessage = CampaignResponse(
            tokenData['sub'],
            data['client_subscription'],
            data['response']
        )

        self.inQueue.put(newResponseMessage)

        message.ack()


