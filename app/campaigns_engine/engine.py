import time, json
from models.messaging_models import DataNotificationBody, OutgoingNotification
from models.dbmodels import NotificationRegister, Campaign
from datetime import datetime, timedelta
from helpers.stringshelper import getIdFromString
from geopy import distance

class CampaignsEngine:
    
    def __init__(self, dbManager, publisher, responsesPubSub, threadLock, inEngineQueueNotifications = None, inEngineQueueResponses = None, inEngineQueueLocations = None):
        self.dbManager = dbManager
        self.publisher = publisher
        self.responsesPubSub = responsesPubSub
        self.threadLock = threadLock
        self.inEngineQueueNotifications = inEngineQueueNotifications
        
        self.inEngineQueueResponses = inEngineQueueResponses
        self.inEngineQueueLocations = inEngineQueueLocations

    def run(self):
        print("Engine starting...")
        while True:
            print("Campaigns:")
            
            campaigns = self.dbManager.listCampaigns()
            print(campaigns.__class__)
            if campaigns != None:
                for campaign in campaigns:
                    print(campaign.title)
                    # All campaign's paramenters are checked to take necessary actions.
                    if datetime.now() >= campaign.begin_date and (datetime.now() < campaign.end_date) if campaign.end_date != None else True:
                        if campaign.status == 0:
                            campaign.status = 1
                            self.dbManager.session.commit()
                    else:
                        if campaign.status != 0:
                            campaign.status = 0
                            self.dbManager.session.commit()
                            continue
                    if campaign.status == 1:
                        if campaign.users == None:
                            print("Campaign haven't users.")
                        for user in campaign.users:
                            
                            for notification in campaign.campaign_notifications:                                                              
                                
                                match notification.notification_touchpoint.channel:
                                    case 1:
                                        if notification.poi_notification == False or notification.poi_notification == None:
                                            # Only non POI based notifications are attended by engine loop. POI based ones are sent when a user's location hits a POI area.
                                            match notification.notification_type:
                                                case "Info":
                                                    if any((
                                                        notification_registered.notification_id == notification.notification_id 
                                                        and notification_registered.touchpoint_id == notification.touchpoint_id 
                                                        and notification_registered.campaign_id == notification.campaign_id
                                                        and notification_registered.user_id == user.user_id) for notification_registered in user.notification_register):
                                                        print("Notification already sent.")
                                                        
                                                    else:
                                                        if (user.oncar):
                                                            newNotificationRegistered = NotificationRegister(
                                                                google_notification_id = user.google_id,
                                                                user_id = user.user_id,
                                                                campaign_id = campaign.campaign_id,
                                                                touchpoint_id = notification.notification_touchpoint.touchpoint_id,
                                                                topic = notification.notification_touchpoint.topic,
                                                                publish_time = datetime.now(),
                                                                notification_id = notification.notification_id
                                                            )

                                                            self.threadLock.acquire()
                                                            registered_notification_id = self.dbManager.createNotificationRegister(newNotificationRegistered)
                                                            self.threadLock.release()

                                                            extraData = {"registered_notification_id": registered_notification_id}

                                                            self.sendNotification(notification, user, extraData=extraData)
                                                    pass
                                    case _:
                                        print('Touchpoint not implemented yet.')
                            # After every user in campaign check about if he got to be notified, check the inEngineQueue for responses on the campaigns-responses topic.
                            if not self.inEngineQueueNotifications.empty() or not self.inEngineQueueLocations.empty():
                                maxIterations = 10
                                i = 0
                                # while not self.inEngineQueueNotifications.empty() and i < maxIterations:
                                while i < maxIterations and (not self.inEngineQueueNotifications.empty() or not self.inEngineQueueLocations.empty()):
                                    if not self.inEngineQueueResponses.empty():
                                        pass
                                    if not self.inEngineQueueNotifications.empty():
                                        response = self.inEngineQueueNotifications.get()
                                        campaign_id = getIdFromString(response.client_subscription.split("-")[0])
                                        campaign = self.dbManager.getCampaignById(campaign_id)
                                        i += 1
                                    if not self.inEngineQueueLocations.empty():
                                        locationMessage = self.inEngineQueueLocations.get()
                                        self.threadLock.acquire()
                                        self.dbManager.updateUserLocation(locationMessage)
                                        self.threadLock.release()
                                        user =  self.dbManager.getUserByGoogleId(locationMessage.google_id)
                                                                        
                                        poiNotifications = self.dbManager.listNotifications({'google_id': locationMessage.google_id, 'poi_notification': True})
                                        

                                        
                                        for notification in poiNotifications:
                                            if not any((notification_register.campaign_id == notification.campaign.campaign_id
                                                    and (datetime.now() - notification_register.publish_time) < timedelta(minutes=15)
                                                    and notification_register.user_id == user.user_id) for notification_register in user.notification_register):
                                                for poi in notification.pois:
                                                    poiDistance = distance.distance((poi.latitude, poi.longitude), (locationMessage.latitude, locationMessage.longitude)).km                                                                                                     
                                                
                                                    if poiDistance < 3 :
                                                        newNotificationRegistered = NotificationRegister(
                                                            google_notification_id = user.google_id,
                                                            user_id = user.user_id,
                                                            
                                                            campaign_id = notification.campaign.campaign_id,
                                                            touchpoint_id = notification.notification_touchpoint.touchpoint_id,
                                                            topic = notification.notification_touchpoint.topic,
                                                            publish_time = datetime.now(),
                                                            notification_id = notification.notification_id,
                                                            poi_notification = True,
                                                            poi_id = poi.poi_id
                                                        ) # Add poi_notification boolean to notification_register
                                                        
                                                        self.threadLock.acquire()
                                                        registered_notification_id = self.dbManager.createNotificationRegister(newNotificationRegistered)
                                                        self.threadLock.release()

                                                        extraData = {
                                                            "registered_notification_id": registered_notification_id,
                                                            "latitude": poi.latitude,
                                                            "longitude": poi.longitude
                                                        }

                                                        
                                                        self.sendNotification(notification, user, extraData=extraData)
                                                        time.sleep(1)
                                                        break
                                                                                                                        
                                        i += 1


                time.sleep(10)
                self.dbManager.session.expire_all() # This cleans sqlalchemy cache.
            

    
    def sendNotification(self, notification, user=None, extraData = None):
        attributes = {}

        args = {
                "notification_title": notification.notification_title,
                "notification_message": notification.message_template,
                "notification_icon_type": notification.notification_icon_type,
                "notification_type": notification.notification_type,
                "notification_id": notification.notification_id,
                "registered_notification_id": extraData.get("registered_notification_id"),
                "latitude": extraData.get("latitude"),
                "longitude": extraData.get("longitude")
            }
        
        
        if notification.responsive:

            notificationData = DataNotificationBody(**args)
           
            attributes['g_id'] = user.google_id
        else:
            
            notificationData = DataNotificationBody(**args)

        dataToSend = json.dumps(vars(notificationData)).encode("utf-8")
        print(f"message to publish: {dataToSend}")
        self.publisher.publish(dataToSend, notification.notification_touchpoint.topic, attributes if len(attributes) > 0 else None)