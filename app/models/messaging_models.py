
class DecryptedTokenData:
    def __init__(self, iss, azp, aud, sub, email, email_verified, name, picture, given_name, family_name, locale, iat, exp):
        self.iss = iss
        self.azp = azp
        self.aud = aud
        self.sub = sub
        self.email = email
        self.email_verified = email_verified
        self.name = name
        self.picture = picture
        self.given_name = given_name
        self.family_name = family_name
        self.locale = locale
        self.iat = iat
        self.exp = exp

    def __init__(self, tokenDict):
        self.iss = tokenDict['iss']
        self.azp = tokenDict['azp']
        self.aud = tokenDict['aud']
        self.sub = tokenDict['sub']
        self.email = tokenDict['email']
        self.email_verified = tokenDict['email_verified']
        self.name = tokenDict['name']
        self.picture = tokenDict['picture']
        self.given_name = tokenDict['given_name']
        self.family_name = tokenDict['family_name']
        self.locale = tokenDict['locale']
        self.iat = tokenDict['iat']
        self.exp = tokenDict['exp']


class IncomingLoginMessage:
    
    def __init__(self, accountMessageType = None, idToken = None, oncar = None, campaign_id = None, subscription_status = None):
        self.accountMessageType = accountMessageType
        self.idToken = idToken
        self.oncar = oncar
        self.campaign_id = campaign_id
        self.subscription_status = subscription_status

class IncomingNotificationResponse:
    def __init__(self, idToken = None, notification_id = None, response = None):
        self.idToken = idToken
        self.notification_id = notification_id
        self.response = response


class VerifiedLoginMessage:
    def __init__(self, decryptedToken = None, oncar = None):
        self.decryptedToken = decryptedToken
        self.oncar = oncar

class UserSubscriptionsMessage:
    def __init__(self, google_id = None, response_type = None, subscriptions = None):
        self.google_id = google_id
        self.response_type = response_type
        self.subscriptions = subscriptions

class DataNotificationBody:
    def __init__(self, notification_title = None, notification_message=None, notification_icon_type = None, notification_type = None, notification_id = None, registered_notification_id = None, latitude = None, longitude = None):
        self.notification_title = notification_title
        self.notification_message = notification_message
        self.notification_icon_type = notification_icon_type
        self.notification_id = notification_id 
        self.registered_notification_id = registered_notification_id
        self.notification_type = notification_type
        self.latitude = latitude
        self.longitude = longitude

class OutgoingNotification:
  def __init__(self, user_id = None, dataNotificationBody = None):
    self.user_id = user_id
    self.dataNotificationBody = dataNotificationBody


class CampaignResponse:
    def __init__(self, google_id = None, client_subscription = None, response = None):
        self.google_id = google_id
        self.client_subscription = client_subscription
        self.response = response

class LocationMessage:
    def __init__(self, google_id = None, latitude = None, longitude = None, position_time = None):
        self.google_id = google_id
        self.latitude = latitude
        self.longitude = longitude
        self.position_time = position_time