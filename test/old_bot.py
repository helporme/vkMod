import importlib
import sys
import inspect
import requests
import random

import threading
import asyncio

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType



class Bot:
    def __init__(self, loop = None):
        with open('config.txt', 'r') as f:
            config = eval(f.read())
            self.group_token = config['group_token']
        
        self.group_session = vk.VkApi(token=self.group_token)
        self.user_sessions = {}
        self.extension = {}
        self.commands = {}

        self.loop = asyncio.get_event_loop() if loop is None else loop

    def run(self):
        self.loop.run_until_complete(self.longpoll_listen())

    async def longpoll_listen(self):
        vkapi = self.group_session.get_api()
        longpoll = VkLongPoll(self.group_session)

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                await self.procces_command(event)

    # commands

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
            dirs = dir(member)
            if 'command_flag' in dirs:
                for name in member.command_names:
                    self.commands[name] = member

    async def procces_command(self, event):
        request_words = []
        if 'payload' in dir(event):
            request_words.append(list(eval(event.payload).keys())[0])
        request_words.append(event.text.split(' ')[0])

        for request_word in request_words:
            if request_word in self.commands:
                await self.commands[request_word](event)

    def command(self, *name):
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