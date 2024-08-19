import discord
from discord.ext import commands, tasks
from discord import DMChannel, errors as discordpy_error
from aiohttp import ClientError
from websockets import exceptions as websocket_error
from bot import bot_user_commands
from dbmanager import db_manager
from logging.handlers import TimedRotatingFileHandler
import asyncio
import logging
import os
import discord_credentials
import traceback
#Added UserRegistration class for debugging - SHP 26APR24
from dbmodels.user_registration import UserRegistration

#description = 'FCOM bot' - SHP 09FEB24
description = 'DWMB bot' # SHP 09FEB24

#add intents - https://discordpy.readthedocs.io/en/latest/intents.html?highlight=intents  - SHP 09FEB24
intents = discord.Intents.default()
intents.messages = True
intents.members = True  #needed to get message user id? - SHP 10FEB24
intents.dm_messages = True #needed to get message user id? - SHP 10FEB24
intents = discord.Intents.all() #fuck it - SHP 10FEB24
#finish intents

#bot = commands.Bot(command_prefix='!', description=description) - SHP 09FEB24
commands.Bot(command_prefix='!', description=description, intents=intents)


token = discord_credentials.TOKEN

# Logging config #

if not os.path.exists('logs'):
    os.mkdir('logs')

formatter = logging.Formatter(fmt='%(asctime)s: %(message)s')
handler = TimedRotatingFileHandler(f'logs/bot.log', when='midnight', backupCount=15)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# End logging config #


# https://github.com/Rapptz/discord.py/blob/master/examples/background_task.py
class BotClient(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        logger.info(f'Now logged in as {self.user.name} ({self.user.id})')
        self.forward_messages.start()
        self.prune_registrations.start()

    async def on_message(self, message):
        """
        Handles user-issued commands via DM. All commands are case-insensitive.
        Supports the following commands:
            register:	Registers user to internal DB, and replies with a token.
                        This token must be confirmed via the API within 5 mins.
            status:     Shows the currently registered callsign (if any)
            remove:		De-registers the user from the internal DB.
        """
        
        
        #log inputs - SHP 10FEB24
        #logger.info(f'**** Fire - on_message with ******')
        #logger.info(f'1 - self.user.id = {self.user.id}')
        #logger.info(f'2 - message.channel = {message.channel}')
        #logger.info(f'3 - message.content.lower() = {message.content.lower()}')
        #logger.info(f'4 - message.channel.recipient.id = {message.channel.recipient.id}')
        #logger.info(f'5 - message.mentions.id = {message.mentions.id}')
        
        """
        print(message)
        temp_channel = message.channel
        print("**** Channel Info ***")
        print(temp_channel)
        print("&&&& Message Author info &&&&")
        print(message.author.id)
        print("message.author = ", message.author)
        print(message.author.name)
        print(message.author.discriminator)
        
        #log inputs - SHP 10FEB24
        """
                
        #handle user ID and name here -SHP 10FEB24
        #user_id = message.author.id
        #user_name = message.author.name
                
        # Do not reply to self
        if message.author.id == self.user.id:
            return

        # Ignore non-DM messages
        elif not isinstance(message.channel, DMChannel):
            return

        # register
        elif message.content.lower() == 'register':

            #fcom_api_token = bot_user_commands.register_user(message.channel) #replace w/ message.author SHP
            fcom_api_token = bot_user_commands.register_user(message.author) #replace w/ message.author SHP

            if fcom_api_token is None:
                msg = "You're already registered! To reset your registration, type `remove` before typing `register` again."
            else:
                

                msg = f"Here's your Discord code: ```{fcom_api_token}```" + \
                      "\nPlease enter it into the client within the next 5 minutes.\n" + \
                      "***IMPORANT***: You must get a confirmation message in Discord after you start forwarding to confirm that the bot is working!"
                logger.info(
                    #f'Generate token:\t{fcom_api_token}, {message.channel.recipient.id} '
                    #f'({message.channel.recipient.name} #{message.channel.recipient.discriminator}) ')
                    f'Generate token:\t{fcom_api_token}, {message.author.id} ' #replace with author.id - SHP 10FEB24
                    f'({message.author.name} #0) ') #replace with author.name and hardcode discrim to 0 - SHP 10FEB24
                    
            await message.channel.send(msg)

        #rewrite status for author.id - SHP 10FEB24
        # status
        elif message.content.lower() == 'status':

            #user = await bot_user_commands.get_user(self, message.channel.recipient)  
            user = await bot_user_commands.get_user(self.user.id, message.author.id) #go straight to ints - SHP 10FEB24

            if user is None:
                msg = "You're currently not registered."
            elif not user.is_verified:
                msg = f"You're registered, but you haven't logged in via the client yet.\n" + \
                      f"**Discord code:** `{user.token}`"
            else:
                msg = f"You're registered! The callsign you're using is **{user.callsign}**.\n" + \
                      f"**Discord code:** `{user.token}`"

            await message.reply(msg, mention_author=False)
            
        #rewrite remove for user id - SHP 10FEB24
        elif message.content.lower() == 'remove':

            if bot_user_commands.remove_user(message.author.id):
                msg = "Successfully deregistered! You'll no longer receive forwarded messages."
                logger.info(f'Deregister user:\t{message.author.id} '
                            f'({message.author.name} #0)')
                
            else:
                msg = "Could not unregister. Are you sure you're registered?"

            await message.channel.send(msg)
        
        """
        # remove
        elif message.content.lower() == 'remove':

            if bot_user_commands.remove_user(message.channel.recipient.id):
                msg = "Successfully deregistered! You'll no longer receive forwarded messages."
                logger.info(f'Deregister user:\t{message.channel.recipient.id} '
                            f'({message.channel.recipient.name} #{message.channel.recipient.discriminator})')
            else:
                msg = "Could not unregister. Are you sure you're registered?"

            await message.channel.send(msg)
        """

    # Reference: https://github.com/Rapptz/discord.py/blob/master/examples/background_task.py
    @tasks.loop(seconds=3)
    async def forward_messages(self):
        """
        Background task that retrieves submitted PMs from the DB and forwards them to the registered Discord user.
        """
        # while not bot.is_closed():
        
        # !!! SHP 18APR24 Debug Code
        logger.debug("     DEBUG: firing forward_messages")
        i = 0
                
        messages = db_manager.get_messages()
        
        

        # Iterate through queued messages (if any), and forward them via Discord DM
        if messages is not None:
        
            # !!! SHP 25APR24 Debug Code
            logger.debug("     DEBUG: messages is not None is true")
        
            for msg in messages:

                # !!! SHP 25APR24 Debug Code
                i=i+1
                logger.debug(f'     DEBUG: message number i = {i}')
                logger.debug(f'       DEBUG: msg.token={msg.token}')

                dm_user = await db_manager.get_user_record(msg.token, self)
                
                #!!! SHP 25APR24 Debug Code
                if isinstance(dm_user, UserRegistration):
                        # !!! SHP 25APR24 Debug Code
                        logger.debug("     DEBUG: dm_user is class discord.user")
                else:
                        # !!! SHP 25APR24 Debug Code
                        logger.debug("     DEBUG: dm_user is NOT class discord.user")
                        
                    
                
                if dm_user is not None:
                
                    # !!! SHP 25APR24 Debug Code
                    logger.debug("        DEBUG: messages dm_user is not None is true")
            
                    # if it's a frequency message (i.e. @xxyyy), parse it into a user-friendly format
                    if msg.receiver.startswith('@'):
                        
                        # !!! SHP 25APR24 Debug Code
                        logger.debug("           DEBUG: treating as frequency message")
                        
                        freq = msg.receiver.replace('@', '1')[:3] + '.' + msg.receiver[3:]
                        dm_contents = f'**{msg.sender}** ({freq} MHz):\n{msg.message}'

                    else:
                        
                        # !!! SHP 25APR24 Debug Code
                        logger.debug("          DEBUG: treating as private message")
                    
                        dm_contents = f'**{msg.sender}**:\n{msg.message}'

                    # SHP 19APR24 - appears this attribute is no longer available.  Replace with dm_channel
                    #ref - https://discordpy.readthedocs.io/en/stable/api.html?highlight=channel#discord.User
                    #dm_channel = dm_user.channel_object    # did not work! -SHP 19APR24
                    #dm_channel = dm_user.dm_channel        # did not work! -SHP 19APR24
                    #dm_channel = dm_user.id    # did not work! -SHP 19APR24
                    
                    
                    # Continued trouble here with dm_user
                    # dm_user.channel_object = null in log file
                    # https://discordpy.readthedocs.io/en/stable/api.html#id1
                    
                    
                    # !!! SHP 25APR24 Debug Code
                    logger.info("     DEBUG: now setting dm_channel")
                    logger.info(f'       DEBUG: dm_user.channel_object = {dm_user.channel_object}')
                    logger.info(f'       DEBUG: dm_user.discord_id = {dm_user.discord_id}')
                    logger.info(f'       DEBUG: dm_user.discord_name = {dm_user.discord_name}')
                    logger.debug(f'dm_user data dump: {dm_user}')
                        
                    dm_channel = dm_user.channel_object
                    
                    try:
                        await dm_channel.send(dm_contents)
                    except discordpy_error.Forbidden:
                        logger.warning(f'[HTTP 403] Could not send DM to {dm_user.discord_name} ({dm_user.discord_id})')
                    except discordpy_error.HTTPException as e:
                        logger.error(f'{traceback.format_exc()}')

                else:
                    # NOTE: the API now checks if a token's registered before inserting messages
                    logger.info(f'Token {msg.token} is not registered!')

            # await asyncio.sleep(3)

    @forward_messages.before_loop
    async def before_forward_messages(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=5)
    async def prune_registrations(self):
        """
        Remove registrations that are either unconfirmed and older than 5 minutes,
        or confirmed and older than 24 hours.

        """
        #TODO - remove stale stat entries too!
        db_manager.remove_stale_users()
        await asyncio.sleep(60*5)

    @prune_registrations.before_loop
    async def before_prune_registrations(self):
        await self.wait_until_ready()


def start_bot():
    """
    Starts the bot
    :return:
    """
    # bot.loop.create_task(forward_messages())
    # bot.loop.create_task(prune_registrations())

    intents = discord.Intents.default()
    intents.messages = True
    intents.members = True

    retry = True

    # Based on https://gist.github.com/Hornwitser/93aceb86533ed3538b6f
    while retry:

        # Linearly increasing backoff for Discord server errors.
        wait_interval = 0
        max_wait_interval = 5 * 60      # 5-minute max interval between retries

        try:
            client = BotClient(intents=intents)
            client.run(token)
            # bot.run(token)

        except discordpy_error.HTTPException as e:
            logging.error("Couldn't login (discord.errors.HTTPException)")
            logging.error(f'{traceback.format_exc()}')

            if wait_interval < max_wait_interval:
                wait_interval = wait_interval + 5
            asyncio.sleep(wait_interval)

        except ClientError as e:
            logging.error("Couldn't login (discord.errors.ClientError)")
            logging.error()
            logging.error(f'{traceback.format_exc()}')

            if wait_interval < max_wait_interval:
                wait_interval = wait_interval + 5
            asyncio.sleep(wait_interval)

        except websocket_error.ConnectionClosed as e:
            logger.info(f'{traceback.format_exc()}')

            # Don't reconnect on authentication failure
            if e.code == 4004:
                logging.error("Authentication error!")
                retry = False
                raise

        else:
            break


#debug tools - SHP 25APR24



start_bot()