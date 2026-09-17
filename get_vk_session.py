import vk_api
import sys
import os
from dotenv import load_dotenv

from vk_token_store import get_access_token

# Load environment variables from .env file
load_dotenv()


path_to_user_data = 'passwords.txt'

VK_TOKEN_HELP = (
    'VK access token is not set.\n'
    'Set it from the bot with /set_vk_token, '
    'or put VK_ACCESS_TOKEN into the .env file.\n'
    'How to get a token: see README.md ("VK token")'
)


class VkTokenMissingError(RuntimeError):
    """Raised when no VK access token is configured"""


def get_user_data():
    lines = []
    try:
        with open(path_to_user_data, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError as e:
        print(e)
        print('please, fix the file name either in the folder or in the script')
        sys.exit(e.errno)

    if (lines.__len__() < 2):
        print('unable to read login / phone number and password')
        print('please, check your user data in the file')
        sys.exit(1)
    l = lines[0]
    p = lines[1]

    return l, p


def handler_captcha(captcha):
    key = input(f'Enter captcha code {captcha.get_url()}: ').strip()
    return captcha.try_again(key)


def build_vk_session(access_token):
    """Create a VK session for the given token"""
    return vk_api.VkApi(token=access_token)


def get_vk_session():
    # Token saved via the bot command wins, VK_ACCESS_TOKEN is the fallback
    access_token = get_access_token()

    if not access_token:
        raise VkTokenMissingError(VK_TOKEN_HELP)

    # l, p = get_user_data()
    # vk_session = vk_api.VkApi(l, p, captcha_handler=handler_captcha, app_id=71697589)
    return build_vk_session(access_token)
