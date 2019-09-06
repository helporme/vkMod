import importlib
import sys
import inspect
import requests
import json
import random
from tinydb import TinyDB, Query

import threading
import asyncio

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType



class Keyboard:
    def keyboard(self, rows, one_time = False, btn_name = 'button'):
        dict_keyboard = {
            "one_time": one_time,
            "buttons": []
        }
        
        for row in range(len(rows)):
            dict_keyboard['buttons'].append([])
            for button in rows[row]:
                dict_keyboard['buttons'][row].append(
                    {
                        "action": {
                            "type": "text",
                            "payload": '{"'+btn_name+'": "'+button[0]+'"}',
                            "label": button[1]
                        },
                        "color": button[2]
                    }
                )
        return json.dumps(dict_keyboard)
    
    def default_keyboard(self):
        default_keyboard = [
           [['@', 'Тут будут ваши популярные комманды', 'primary'  ]],
           [['',  'Настройки',                          'secondary'],
            ['',  'Помощь',                             'secondary'],
            ['',  'Про бота',                           'secondary'],
            ['',  'Выход',                              'negative' ]]
        ]

        return default_keyboard
    
    def change_keyboard(self, rows, target, edit, n=1):
        for row in rows:
            for button in row:
                if target in button:
                    button[n] = edit
        return rows

    def update_keyboard_from_stats(self, keyboard, stats):
        top_commands = sorted(stats.items(), key=lambda x: x[1])
        keyboard[0] = [['', command_name[0], 'primary'] for command_name in top_commands]
        return keyboard

class Bot(Keyboard):
    def __init__(self, bot_id, group_token, loop = None):
        self.group_session = vk.VkApi(token=group_token)
        self.user_sessions = {}
        self.bot_id = bot_id
        self.extension = {}
        self.commands = {}

        self.loop = asyncio.get_event_loop() if loop == None else loop
        self.wait_for = {}

    def run(self):
        self.after_restart_login()
        self.loop.run_until_complete(self.longpoll_listen())

    # Main

    async def longpoll_listen(self):
        vkapi = self.group_session.get_api()
        longpoll = VkLongPoll(self.group_session)

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                await self.procces_command(event)

    async def procces_command(self, event):
        event.main_user_id = event.user_id # Author of message

        # Event handler
        if hasattr(event, 'payload'):
            if event.payload == '@':
                event.text = ''
                event.user_id = -1

        if self.user_get(event.user_id, 'login_as') != None:
            event.user_id = self.user_get(event.user_id, 'login_as') #Redirect event.user_id login_as user. 
            
        # Procces command

        if event.user_id in self.wait_for:
            future = self.wait_for[event.user_id]
            future.set_result(event)
            await asyncio.sleep(0)
            
        else:
            request_word = event.text.lower()
            while request_word[-1] == ' ':
                request_word = event.text[:-1]
            
            args = (event,)
            if request_word in self.commands:
                if hasattr(self.commands[request_word], 'userauth_flag'):
                    if event.user_id in self.user_sessions:
                        args = (self.user_sessions[event.main_user_id],) + args
                        self.user_update_stats(event.main_user_id, request_word)
                    
                    else:
                        return

                asyncio.Task(self.commands[request_word](*args))
                await asyncio.sleep(0)

    async def wait_for_message(self, user_id, timeout = None):
        future = asyncio.Future(loop=self.loop)
        self.wait_for[user_id] = future 

        try:
            message = await asyncio.wait_for(future, timeout, loop=self.loop)
        except asyncio.TimeoutError:
            message = None
        
        del self.wait_for[user_id]
        return message

    # Users database

    def user_login(self, user_id, user_token = None, password = None, access_to = None, **kwargs):
        db = TinyDB('userdb.json')
        Users = Query()
        user = db.search(Users.id == user_id)

        if user == []:
            if user_token == None:
                return
            else:
                db.insert({
                    'id': user_id,
                    'login_as': None,
                    'password': password,
                    'token': user_token,
                    'access_to': access_to,
                    'stats': {},
                    'keyboard': self.default_keyboard(),
                    'login': True,
                    **kwargs
                })

                self.user_sessions[user_id] = vk.VkApi(token=user_token)

        else:
            if user_token == None:
                if user[0]['password'] == password:
                    self.user_edit(user_id, 'login', True)
                    if not user_id in self.user_sessions:
                        self.user_sessions[user_id] = vk.VkApi(token=user[0]['token'])
                    return True
                #Passwords doesnt match
                else:
                    return False
            else:
                db.update({'token': user_token}, Users.id == user_id)
                self.user_sessions[user_id] = vk.VkApi(token=user_token)
    
    def login_as(self, user_id, owner_id):
        db = TinyDB('userdb.json')
        Users = Query()
        
        if db.search(Users.id == owner_id) == []:
            return
        
        access_to = self.user_get(owner_id, 'access_to')

        if user_id in access_to or access_to[0] == 'all':
            #create session of user with owner user token
            self.user_sessions[user_id] = vk.VkApi(token=self.user_get(owner_id, 'token'))
            self.user_edit(user_id, 'login_as', owner_id)
            self.user_edit(user_id, 'login', True)
            
            return True
        else:
            return False

    def after_restart_login(self):
        db = TinyDB('userdb.json')
        users = db.all()

        for user in users:
            if user['login']:
                if user['login_as'] == None:
                    token = self.user_get(user['id'], 'token')
                    self.user_sessions[user['id']] = vk.VkApi(token=token)
                
                else:
                    self.user_sessions[user['id']] = vk.VkApi(token=self.user_get(user['login_as'], 'token'))

    def unlogin_user(self, user_id):
        db = TinyDB('userdb.json')
        Users = Query()
        
        if db.search(Users.id == user_id) == []:
            return

        self.user_edit(user_id, 'login', False)
        self.user_edit(user_id, 'login_as', None)

        if user_id in self.user_sessions:
            del self.user_sessions[user_id]

    def delete_user(self, user_id):
        db = TinyDB('userdb.json')
        Users = Query()
        
        if db.search(Users.id == user_id) == []:
            return

        db.remove(Users.id == user_id)
        if user_id in self.user_sessions:
            if 'logged_in' in self.user_sessions[user_id]:
                logged_user_id = self.user_sessions[user_id].split(' ')[1]
                self.user_edit(logged_user_id, 'login_as', None)
            del self.user_sessions[user_id]
    
    def user_get(self, user_id, query):
        db = TinyDB('userdb.json')
        Users = Query()

        if db.search(Users.id == user_id) == []:
            return

        response = db.search(Users.id == user_id)[0][query]
        return response
    
    def user_edit(self, user_id, item, value):
        db = TinyDB('userdb.json')
        Users = Query()

        if db.search(Users.id == user_id) == []:
            return

        db.update({item: value}, Users.id == user_id)

    def user_update_stats(self, user_id, command_name):
        db = TinyDB('userdb.json')
        Users = Query()
        if db.search(Users.id == user_id) == []:
            return

        stats = self.user_get(user_id, 'stats')
        keyboard = self.user_get(user_id, 'keyboard')
        
        if command_name in stats:
            stats[command_name] += 1
        else:
            stats[command_name] = 1
        keyboard = self.update_keyboard_from_stats(keyboard, stats)
        
        self.user_edit(user_id, 'stats', stats)
        self.user_edit(user_id, 'keyboard', keyboard)
    
    def user_keyboard(self, user_id):
        db = TinyDB('userdb.json')
        Users = Query()

        if db.search(Users.id == user_id) == []:
            return
        
        return self.keyboard(self.user_get(user_id, 'keyboard'))

    def userauth(self, func):
        """Add userinfo as first argument.
        If there is no information about the user, the login function is automatically called.

        Decorator.

        (for extensions, you can use this: from bot import botuserauth)
        """

        func.userauth_flag = True    
        return func

    # upload commands

    def load_extension(self, name):
        if name in self.extension: 
            return
        try:
            lib = importlib.import_module(name)
        except:
            raise Exception('Unable to import file.')
        
        if not hasattr(lib, 'setup'):
            del lib
            del sys.modules[name]
            raise Exception('File does not have a setup function.')
        
        lib.setup(self)
        self.extension[name] = lib

    def add_class(self, obj):
        """Get all functions-command.
        
        Parameters
        ---------
        obj : Class
        """
        members = inspect.getmembers(obj)
        for name, member in members:
            if 'command_flag' in dir(member):
                for name in member.command_names:
                    self.commands[name] = member

    def command(self, *names):
        """Mark function as command.
        
        Decorator.

        (for extensions, you can use this: from bot import botcommand)

        Parameters
        ----------
        *names : str
            Name/s to invoke the command.
            Default: name of function.
        """
        
        def decorator(func):
            command_names = names if names != () else func.__name__

            func.command_names = command_names
            func.command_flag = True

            return func
        return decorator

# decorator for extensions

def botcommand(*names):
    """Mark function as command. 

    (for extensions)

    Parameters
    ----------
    *names : str
        Name/s to invoke the command.
        Default: name of function.
    """

    def decorator(func):
        command_names = names if names != () else func.__name__

        func.command_names = command_names
        func.command_flag = True

        return func
    return decorator

def userauth(func):
    """Add userinfo as first argument.
    If there is no information about the user, the login function is automatically called.

    Decorator.

    (for extensions, you can use this: from bot import botuserauth)
    """

    func.userauth_flag = True    
    return func