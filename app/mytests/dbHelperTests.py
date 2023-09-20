from helpers.dbhelper import DbManager
from config.appconfig import postgreParams


def testCampaignList(dbManager):
    campaignList = dbManager.listCampaigns({'google_id': "103437917318319692710", 'poi_campaign': False})
    print(f"Campaigns for test user: {campaignList}")
    if campaignList is not None:
        for campaign in campaignList:
            print(campaign.title)

def testNotificationsList(dbManager):
    # notificationList = dbManager.listNotifications({'google_id': "103437917318319692710", 'poi_notification': False})
    notificationList = dbManager.listNotifications({'google_id': "111239271836469362379", 'poi_notification': False})
    # notificationList = dbManager.listNotifcations()
    print(f"Notifications for test user: {notificationList}")
    if notificationList is not None:
        for notification in notificationList:
            print(notification.notification_title)

def runDbTests():
    dbManager = DbManager(postgreParams)
    testNotificationsList(dbManager)
    pass