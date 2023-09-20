from sqlalchemy import Column, Integer, String, SmallInteger, Boolean, Date, TIMESTAMP, ForeignKey, PrimaryKeyConstraint, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    google_id = Column(String, unique=True, nullable=True)
    phone = Column(String(14), nullable=True)
    address = Column(String(60), nullable=True)
    birthday = Column(Date, nullable=False)
    gender = Column(SmallInteger, nullable=True)
    oncar = Column(Boolean, nullable=True)

    campaigns = relationship('Campaign', secondary='campaign_subscriptions', back_populates='users')
    notification_register = relationship('NotificationRegister', back_populates='user')
    location = relationship('UsersLocation', back_populates='user')

class UsersLocation(Base):
    __tablename__ = 'users_locations'

    location_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    position_time = Column(TIMESTAMP, nullable=False)

    user = relationship('User', back_populates='location')

class CampaignRule(Base):
    __tablename__ = 'campaign_rules'

    rule_id = Column(Integer, primary_key=True)
    age_start = Column(Date, nullable=True)
    age_end = Column(Date, nullable=True)
    gender = Column(SmallInteger, nullable=True)
    oncar = Column(Boolean, nullable=True)
    

class Campaign(Base):
    __tablename__ = 'campaigns'

    campaign_id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    status = Column(SmallInteger(), nullable=False, default=0)
    
    begin_date = Column(TIMESTAMP(), nullable=False, default=datetime.now())
    end_date = Column(TIMESTAMP(), nullable=True)
    creation_date = Column(TIMESTAMP(), nullable=False, default=datetime.now())
    rule_id = Column(Integer, ForeignKey('campaign_rules.rule_id'), nullable=True)
    poi_campaign = Column(Boolean, nullable=True)

    
    users = relationship('User', secondary='campaign_subscriptions', back_populates='campaigns') # Many to many relationship. (back_populates seems to be prefered over backref)
    
    campaign_notifications = relationship('CampaignNotification', back_populates='campaign')

class NotificationTouchpoint(Base):
    __tablename__ = 'notification_touchpoints'

    touchpoint_id = Column(Integer, primary_key=True)
    channel = Column(Integer, nullable=False)
    topic = Column(String(60), nullable=True)

    campaign_notifications = relationship('CampaignNotification', back_populates='notification_touchpoint')

class CampaignNotification(Base):
    __tablename__ = 'campaign_notifications'

    notification_id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.campaign_id'))
    notification_title = Column(String(40), nullable=False)
    message_template = Column(String, nullable=False)
    priority = Column(SmallInteger, nullable=False)
    responsive = Column(Boolean, nullable=False)
    touchpoint_id = Column(Integer, ForeignKey('notification_touchpoints.touchpoint_id'), nullable=False)
    notification_type = Column(String(30), nullable=True)
    notification_icon_type = Column(String(40), nullable=True)
    poi_notification = Column(Boolean, nullable=True)

    campaign = relationship('Campaign', back_populates='campaign_notifications')

    notification_touchpoint = relationship('NotificationTouchpoint', back_populates='campaign_notifications')
    pois = relationship('PointOfInterest', secondary='notification_pois', back_populates='notifications')

class CampaignSubscription(Base):
    __tablename__ = 'campaign_subscriptions'

    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.campaign_id'), primary_key=True)


    __table_args__= (
        PrimaryKeyConstraint(user_id, campaign_id),
        {},
    )



class NotificationRegister(Base):
    __tablename__ = 'notification_register'

    notification_reg_id = Column(Integer, primary_key=True)
    google_notification_id = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    campaign_id = Column(Integer, ForeignKey('campaigns.campaign_id'), nullable=False)
    touchpoint_id = Column(Integer, ForeignKey('notification_touchpoints.touchpoint_id'), nullable=False)
    topic = Column(String, nullable=False)
    publish_time = Column(TIMESTAMP, nullable=False)
    response_status = Column(Integer, nullable=True)
    notification_id = Column(Integer, ForeignKey('campaign_notifications.notification_id'), nullable=False)
    poi_notification = Column(Boolean, nullable=True)
    poi_id = Column(Integer, ForeignKey('points_of_interest.poi_id'), nullable=True)

    user = relationship('User', back_populates='notification_register')

class PointOfInterest(Base):
    __tablename__ = 'points_of_interest'

    poi_id = Column(Integer, primary_key=True)
    poi_type = Column(String, nullable=False)
    poi_name = Column(String(40), nullable=False)
    poi_description = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    notifications = relationship('CampaignNotification', secondary='notification_pois', back_populates='pois')

class NotificationPois(Base):
    __tablename__ = 'notification_pois'

    notification_id = Column(Integer, ForeignKey('campaign_notifications.notification_id'), primary_key=True)
    poi_id = Column(Integer, ForeignKey('points_of_interest.poi_id'), primary_key=True)


    __table_args__= (
        PrimaryKeyConstraint(notification_id, poi_id),
        {},
    )
