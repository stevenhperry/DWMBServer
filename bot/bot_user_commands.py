from discord import User, DMChannel, Client, Message #added message SHP 10FEB24
from dbmanager import db_manager
from dbmodels import user_registration

#redefine to use user ID from the message.author - SHP 10FEB24

#def register_user(user_channel: DMChannel) -> str:
#def register_user(user_message: Message) -> str:
def register_user(user: User) -> str:
    """
    Add the Discord user to the DB, generating a token to be used by the client.
    The user must be confirmed via the API within 5 minutes of creation.

    :param user_channel:    The DMChannel containing the Discord user to be added
    :param user_message:    The message sent [already screened to be a DM] #SHP 10FEB24
    :return:                The token associated with the Discord user.
    """
    #user = user_channel.recipient #doesn't work anymore - SHP 10FEB24
    
    #user = user_message.author.id #SHP 10FEB24
    user_channel = "null" #SHP 10FEB24
    #token = db_manager.add_discord_user(user.id, f'{user.name} #{user.discriminator}', user_channel) #remove discriminator, replace with 0
    token = db_manager.add_discord_user(user.id, f'{user.name} #0', user_channel) #remove discriminator, replace with 0
    
    return token


#async def get_user(client: Client, user: User) -> user_registration.UserRegistration:
async def get_user(client: Client, user: int) -> user_registration.UserRegistration: #user was not putting up User.id, so cast as int? SHP
    """
    Retrieves the registration entry of the given Discord user.

    :param client:  The bot object
    :param user:    discord.py User object
    :return:        Representation of user in the DB. Returns None if not present.
    """
    #return await db_manager.get_user_record(user.id, client)
    return await db_manager.get_user_record(user, client)


def remove_user(discord_id: int) -> bool:
    """
    Removes the specified user from the DB.

    :param discord_id:  Discord ID of the user to remove
    :return:            True on success, False otherwise
    """
    if db_manager.remove_discord_user(discord_id):
        return True
    else:
        return False
