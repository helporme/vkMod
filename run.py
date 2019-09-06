import asyncio
import importlib

from vkmod.bot import Bot

def main():
    bot = Bot(7073082, 'c5d1c86d71e5eebc0b55f26662ab795522524583ead01c38ead9c0449be5685b8891077b9bfc1eb3ac88e')
    for command in ['ping','start','login','offline', 'wall']:
        bot.load_extension(f'vkmod.commands.{command}')
    
    bot.run()

if __name__ == '__main__':
    main()