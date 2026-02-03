import vk_api
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


path_to_user_data = 'passwords.txt'


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

def get_vk_session():
    # Get access token from environment variable
    access_token = os.getenv('VK_ACCESS_TOKEN')
    
    if not access_token:
        print('Error: VK_ACCESS_TOKEN not found in environment variables')
        print('Please create a .env file with your VK access token')
        print('Get your token from: https://oauth.vk.com/authorize?client_id=7624256&display=page&scope=photos,offline&response_type=token&v=5.131')
        sys.exit(1)
    
    # l, p = get_user_data()
    # vk_session = vk_api.VkApi(l, p, captcha_handler=handler_captcha, app_id=71697589)
    vk_session = vk_api.VkApi(token=access_token)
    return vk_session

