import threading, psycopg2
from models.dbmodels import User, Campaign, CampaignSubscription, NotificationRegister, UsersLocation, CampaignNotification
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, or_, and_, select

class DbManager:

    def __init__(self, postgreParams):
        self.dbUrl = URL.create(
            drivername="postgresql",
            username=postgreParams['user'],
            host=postgreParams['host'],
            database=postgreParams['database'],
            password=postgreParams['password']
            )

        self.engine = create_engine(self.dbUrl)

        Session = sessionmaker(bind=self.engine)

        self.session = Session()

        self.checkDbConnection()
    
    def __del__(self):
        self.session.close()
        print('Database connection closed!')


    def checkDbConnection(self):
        try:
            self.engine.execute("SELECT 1")
            print("DB connection working.")
        except Exception as e:
            print(f"DB connection error: ")

    def listUsers(self):
        try:
            users = self.session.query(User).order_by(User.user_id).all()
            return users
        except Exception as e:
            print(f"Error updating users table: {e}")

    def getUserByGoogleId(self, google_id):
        try:
            return self.session.query(User).filter_by(google_id = google_id).first()
        except Exception:
            return None

    def updateUserTable(self, updateData):

        print("Test update table")

        try:
            
            user = self.session.query(User).filter_by(email=updateData['email']).first()
            
            if user:
                if user.google_id == None:
                    user.google_id = updateData['id']
                user.oncar = updateData['oncar']
                
                self.session.commit()
            else:
                print("User not found.")
        except Exception as e:
            print(f"Error updating users table: {e}")

    def updateUserLocation(self, locationData):
        try:
            user = self.session.query(User).filter_by(google_id=locationData.google_id).first()
            if user:
                if user.location:
                    user.location.latitude = locationData.latitude
                    user.location.longitude = locationData.longitude
                    user.location.position_time = locationData.position_time
                else:
                    newLocationEntry = UsersLocation(
                        user_id = user.user_id,
                        latitude = locationData.latitude,
                        longitude = locationData.longitude,
                        position_time = locationData.position_time
                    )
                    self.session.add(newLocationEntry)
                self.session.commit()
        except Exception as e:
            print(f"Exception: {e}")            

    def createUserCampaignSubscription(self, user_id, campaign_id):
        campaignSubscription = self.session.query(CampaignSubscription).filter(and_(CampaignSubscription.user_id == user_id, CampaignSubscription.campaign_id == campaign_id)).first()

        if campaignSubscription is None:
            try:
                print("creating campaign subscription")
                newCampaignSubscription = CampaignSubscription(user_id = user_id, campaign_id = campaign_id)
                print(newCampaignSubscription)
                self.session.add(newCampaignSubscription)
                self.session.commit()
            except Exception as e:
                print(f"Error creating campaign subscription: {e}")

    def deleteUserCampaignSubscription(self, user_id, campaign_id):
        campaignSubscription = self.session.query(CampaignSubscription).filter(and_(CampaignSubscription.user_id == user_id, CampaignSubscription.campaign_id == campaign_id)).first()

        if campaignSubscription is not None:
            
            self.session.delete(campaignSubscription)
            self.session.commit()

    def listCampaigns(self, queryFilters = None):
        try:
            
            campaignsQuery = self.session.query(Campaign).order_by(Campaign.campaign_id)
            filterClauses = []
            if queryFilters != None:
                if 'poi_campaign' in queryFilters:
                    if queryFilters['poi_campaign'] == False:
                        filterClauses.append(or_(Campaign.poi_campaign == False,  Campaign.poi_campaign == None))
                    if queryFilters['poi_campaign'] == True:
                        filterClauses.append(Campaign.poi_campaign == True)
                if 'google_id' in queryFilters:
                    
                    campaignsQuery = campaignsQuery.join(User, Campaign.users)
                    
                    filterClauses.append(User.google_id == queryFilters['google_id'])
                                    
                    print("Applying user filter!")

                campaignsQuery = campaignsQuery.filter(and_(*filterClauses))
            campaigns = campaignsQuery.all()
            return campaigns
        except Exception:
            return None
        
    def getCampaignByTitle(self, title):
        try:
            return self.sesssion.query(Campaign).filter_by(title = title).first()
        except Exception:
            return None
        
    def createNotificationRegister(self, notificationRegister):
        try:
            self.session.add(notificationRegister)
            self.session.commit()
            self.session.flush()
            return notificationRegister.notification_reg_id
        except Exception as e:
            print(f"Error: {e}")
        

    def listNotifications(self, queryFilters = None):
        try:
            notificationsQuery = self.session.query(CampaignNotification).order_by(CampaignNotification.notification_id)
            filterClauses = []
            if queryFilters != None:
                if 'google_id' in queryFilters:
                    notificationsQuery = notificationsQuery.join(Campaign, CampaignNotification.campaign).join(User, Campaign.users)
                    
                    filterClauses.append(User.google_id == queryFilters['google_id'])
                if 'poi_notification' in queryFilters:
                    if queryFilters['poi_notification']:
                        filterClauses.append(CampaignNotification.poi_notification == queryFilters['poi_notification'])
                    else:
                        filterClauses.append(or_(CampaignNotification.poi_notification == False,  CampaignNotification.poi_notification == None))

                notificationsQuery = notificationsQuery.filter(and_(*filterClauses))
            notifications = notificationsQuery.all()
            return notifications
        except Exception as e:
            print(f"Error listing notifications: {e}")
            return None