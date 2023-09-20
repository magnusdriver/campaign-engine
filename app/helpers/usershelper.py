from models.messaging_models import UserSubscriptionsMessage
from helpers.googlesigninhelper import verifyGoogleIdToken
import time, json

class UsersManager:

    def __init__(self, registryPubSub, notificationsPubSub, dbManager, registerQueue, lock):
        self.registryPubSub = registryPubSub
        self.notificationsPubSub = notificationsPubSub
        self.registerQueue = registerQueue
        self.dbManager = dbManager
        self.lock = lock


    def userRegistry(self):
        while True:
            if not self.registerQueue.empty():
                incomingLoginMessage = self.registerQueue.get()
                tokenData = verifyGoogleIdToken(incomingLoginMessage.idToken)
                
                if(tokenData != None):
                    match incomingLoginMessage.accountMessageType:
                        case 'login' | 'logout':
                            print("userhelper: login!")
                            
                            updateData = {
                                "email": tokenData['email'],
                                "id": tokenData['sub'],
                                "name": tokenData['name'],
                                "oncar": incomingLoginMessage.oncar
                                }
                            self.lock.acquire()
                            self.dbManager.updateUserTable(updateData)
                            self.lock.release()
                            if incomingLoginMessage.accountMessageType == 'login':
                                self.sendUserCampaignSubscriptions(updateData['id'])
                            else:
                                user = self.dbManager.getUserByGoogleId(updateData['id'])
                                for campaign in user.campaigns:
                                    
                                    if any(notification.responsive for notification in campaign.campaign_notifications):
                                        
                                        self.notificationsPubSub.deletePubSubSubscription(f"campaign{campaign.campaign_id}-client{user.user_id}")
                                        self.dbManager.deleteUserCampaignSubscription(user.user_id, campaign.campaign_id)
                                        
                        
                        case 'campaign-subscription':
                            
                            user = self.dbManager.getUserByGoogleId(tokenData['sub'])
                            # Find out how to add the user to campaign_subscriptions or remove it depending on subscription_status var.
                            print(f"userhelper: Estado de subscription_status {incomingLoginMessage.subscription_status}")
                            if incomingLoginMessage.subscription_status:
                                print("userhelper: creating subscription")
                                
                                self.dbManager.createUserCampaignSubscription(user.user_id, incomingLoginMessage.campaign_id)
                            elif not incomingLoginMessage.subscription_status:
                                
                                
                                self.notificationsPubSub.deletePubSubSubscription(f"campaign{incomingLoginMessage.campaign_id}-client{user.user_id}")
                                self.dbManager.deleteUserCampaignSubscription(user.user_id, incomingLoginMessage.campaign_id)
                                

                            self.sendUserCampaignSubscriptions(tokenData['sub'])
                                


            time.sleep(1)

    def sendUserCampaignSubscriptions(self, google_id):
        subscriptions = []
        attributes = {}
        user =  self.dbManager.getUserByGoogleId(google_id)
        
        for campaign in user.campaigns:
            hasResponsiveNotifications = False
            hasNonResponsiveNotifications = False
            for notification in campaign.campaign_notifications:
                if notification.responsive == True: hasResponsiveNotifications = True
                else: hasNonResponsiveNotifications = True
                if hasNonResponsiveNotifications and hasResponsiveNotifications == True: break

            campaignSubscriptions = self.notificationsPubSub.getSubscriptionsList()

            if hasResponsiveNotifications:
                topicId = f"campaign{campaign.campaign_id}"
                userSubscription = f"campaign{campaign.campaign_id}-client{user.user_id}"
                
                if userSubscription not in self.notificationsPubSub.subscriptions and userSubscription not in campaignSubscriptions:
                    subscriptionFilter = f"attributes.g_id = \"{google_id}\""
                    print(f"creating subscription with filter: {subscriptionFilter}")
                    self.notificationsPubSub.createSubscription(userSubscription, topicId, subscriptionFilter)
                subscriptions.append(userSubscription)

            if hasNonResponsiveNotifications:
                topicId = f"campaign{campaign.campaign_id}"
                userSubscription = f"campaign{campaign.campaign_id}-sub"
                if userSubscription not in self.notificationsPubSub.subscriptions and userSubscription not in campaignSubscriptions:
                    self.notificationsPubSub.createSubscription(userSubscription, topicId)
                subscriptions.append(userSubscription)

        responseMessage = UserSubscriptionsMessage(google_id ,"subscriptions-info", subscriptions)
        messageData = json.dumps(vars(responseMessage)).encode("utf-8")
        
        self.registryPubSub.publish(messageData, f"register-responses", attributes if len(attributes) > 0 else None)

