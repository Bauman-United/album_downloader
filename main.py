import vk_api
import requests
import os
import re
import datetime
import sys
import shutil
from dotenv import load_dotenv

from get_vk_session import get_vk_session
from upload_to_yandex_disk import upload_albums_to_yandex_disk

# Load environment variables
load_dotenv()

path_to_downloaded_albums = 'vk_downloaded_albums'
path_to_albums_list = 'album_list_2.txt'


def print_progress(value, end_value, bar_length=20):
    percent = float(value) / end_value
    arrow = '-' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    sys.stdout.write("\rProgress: [{0}] {1}% ({2} / {3})".format(
        arrow + spaces, int(round(percent * 100)),
        value, end_value))
    sys.stdout.flush()


def process_url(url):
    verification = re.compile(r'^https://vk\.(com|ru)/album(-?[\d]+)_([\d]+)$')
    o = verification.match(url)
    if not o:
        raise ValueError('invalid album link: {}'.format(url))
    owner_id = o.group(2)
    album_id = o.group(3)
    return {'owner_id': owner_id, 'album_id': album_id}


def read_data():
    lines = []
    queries = []


    # TODO добавить сбор альбомов среди список папок в группе
    try:
        with open(path_to_albums_list, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError as e:
        print(e)
        print('please, fix the file name either in the folder or in the script')
        sys.exit(e.errno)

    queries = []
    for url in lines:
        try:
            queries.append(process_url(url))
        except ValueError as e:
            print(e)
    return queries


def download_image(url, local_file_name):
    response = requests.get(url, stream=True)
    if not response.ok:
        print('bad response:', response)
        return
    with open(local_file_name, 'wb') as file:
        for chunk in response.iter_content(1024):
            # if not chunk:
            #     break
            file.write(chunk)
    return


def fix_illegal_album_title(title):
    illegal_character = '\/|:?<>*"'
    for c in illegal_character:
        title = title.replace(c, '_')
    return title


def clear_downloaded_albums():
    """Delete all downloaded albums from local storage"""
    if os.path.exists(path_to_downloaded_albums):
        print(f'\nCleaning up downloaded albums from: {path_to_downloaded_albums}')
        try:
            shutil.rmtree(path_to_downloaded_albums)
            print('✓ All local albums deleted successfully')
        except Exception as e:
            print(f'Error deleting albums: {e}')
            return False
    return True


def download_albums():
    """Download all albums from VK"""
    queries = read_data()
    vk_session = get_vk_session()

    # Token-based authentication doesn't need auth() call
    # Only try auth if using login/password
    try:
        api = vk_session.get_api()
        # Test the API connection
        api.users.get(user_ids=1)
    except Exception as e:
        print('could not authenticate to vk.com')
        print(e)
        print('please, check your token or user data in the file')
        sys.exit(1)
    l = None
    p = None

    print('number of albums to download: {}'.format(queries.__len__()))
    for q in queries:
        o = q['owner_id']
        a = q['album_id']

        try:
            album = api.photos.getAlbums(owner_id=o, album_ids=a)['items'][0]
            title = album['title']
            title = fix_illegal_album_title(title)
            images_num = album['size']
            photos = api.photos.get(owner_id=o, album_id=a, photo_sizes=1, count=images_num)['items']
        except vk_api.exceptions.ApiError as e:
            print('exception:')
            print(e)
            return False

        album_path = path_to_downloaded_albums + '/' + title
        if not os.path.exists(album_path):
            os.makedirs(album_path)
        else:
            album_path += '.copy_{:%Y-%m-%d_%H-%M-%S}'.format(
                datetime.datetime.now())
            os.makedirs(album_path)

        print('downloading album: ' + title)
        cnt = 0
        for p in photos:
            largest_image_width = p['sizes'][0]['width']
            largest_image_src = p['sizes'][0]['url']

            if largest_image_width == 0:
                largest_image_src = p['sizes'][p['sizes'].__len__() - 1]['url']
            else:
                for size in p['sizes']:
                    if size['width'] > largest_image_width:
                        largest_image_width = size['width']
                        largest_image_src = size['url']

            extension = os.path.splitext(largest_image_src)[-1].split('?')[0]
            # TODO починить имена фоток
            download_image(largest_image_src, album_path + '/' +
                           str(p['id']) + extension)
            cnt += 1
            print_progress(cnt, images_num)
        print()
    
    return True


def main():
    """Main workflow: Download → Upload to Yandex Disk → Cleanup"""
    print('=' * 60)
    print('VK Album Downloader - Full Workflow')
    print('=' * 60)
    print()
    
    # Step 1: Download albums from VK
    print('STEP 1: Downloading albums from VK...')
    print('-' * 60)
    download_success = download_albums()
    
    if not download_success:
        print('\n✗ Download failed. Stopping workflow.')
        sys.exit(1)
    
    print('\n✓ All albums downloaded successfully!')
    print()
    
    # Step 2: Upload to Yandex Disk
    print('STEP 2: Uploading albums to Yandex Disk...')
    print('-' * 60)
    try:
        yandex_disk_path = os.getenv('YANDEX_DISK_PATH', '/VK_Albums')
        upload_albums_to_yandex_disk(yandex_disk_path)
        print('\n✓ All albums uploaded to Yandex Disk successfully!')
    except Exception as e:
        print(f'\n✗ Upload to Yandex Disk failed: {e}')
        print('Local files will NOT be deleted due to upload failure.')
        sys.exit(1)
    
    # Step 3: Cleanup local files
    print()
    print('STEP 3: Cleaning up local files...')
    print('-' * 60)
    clear_downloaded_albums()
    
    print()
    print('=' * 60)
    print('✓ WORKFLOW COMPLETED SUCCESSFULLY!')
    print('=' * 60)


if __name__ == "__main__":
    main()