import yadisk
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Path to downloaded albums
path_to_downloaded_albums = 'vk_downloaded_albums'


def print_progress(value, end_value, bar_length=20):
    """Display upload progress bar"""
    percent = float(value) / end_value
    arrow = '-' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    sys.stdout.write("\rProgress: [{0}] {1}% ({2} / {3})".format(
        arrow + spaces, int(round(percent * 100)),
        value, end_value))
    sys.stdout.flush()


def get_yandex_disk_client():
    """Initialize Yandex Disk client with token from environment"""
    token = os.getenv('YANDEX_DISK_TOKEN')
    
    if not token:
        print('Error: YANDEX_DISK_TOKEN not found in environment variables')
        print('Please add your Yandex Disk token to the .env file')
        print('Get your token from: https://yandex.ru/dev/disk/poligon/')
        sys.exit(1)
    
    y = yadisk.YaDisk(token=token)
    
    # Check if token is valid
    if not y.check_token():
        print('Error: Invalid Yandex Disk token')
        print('Please check your token in the .env file')
        sys.exit(1)
    
    return y


def upload_albums_to_yandex_disk(yandex_disk_path='/VK_Albums'):
    """
    Upload all downloaded VK albums to Yandex Disk
    
    Args:
        yandex_disk_path: Path on Yandex Disk where albums will be uploaded (default: /VK_Albums)
    """
    y = get_yandex_disk_client()
    
    # Check if local albums directory exists
    if not os.path.exists(path_to_downloaded_albums):
        print(f'Error: Directory "{path_to_downloaded_albums}" not found')
        print('Please download some albums first using main.py')
        sys.exit(1)
    
    # Get list of album folders
    albums = [d for d in os.listdir(path_to_downloaded_albums) 
              if os.path.isdir(os.path.join(path_to_downloaded_albums, d))]
    
    if not albums:
        print(f'No albums found in "{path_to_downloaded_albums}"')
        print('Please download some albums first using main.py')
        return
    
    print(f'Found {len(albums)} album(s) to upload')
    print(f'Uploading to Yandex Disk path: {yandex_disk_path}')
    print()
    
    # Create base directory on Yandex Disk if it doesn't exist
    if not y.exists(yandex_disk_path):
        print(f'Creating directory on Yandex Disk: {yandex_disk_path}')
        y.mkdir(yandex_disk_path)
    
    # Upload each album
    for album_name in albums:
        local_album_path = os.path.join(path_to_downloaded_albums, album_name)
        remote_album_path = f'{yandex_disk_path}/{album_name}'
        
        # Get list of photos in the album
        photos = [f for f in os.listdir(local_album_path) 
                  if os.path.isfile(os.path.join(local_album_path, f))]
        
        if not photos:
            print(f'Skipping empty album: {album_name}')
            continue
        
        print(f'Uploading album: {album_name} ({len(photos)} photos)')
        
        # Create album directory on Yandex Disk if it doesn't exist
        if not y.exists(remote_album_path):
            y.mkdir(remote_album_path)
        
        # Upload each photo
        uploaded_count = 0
        skipped_count = 0
        
        for i, photo_name in enumerate(photos, 1):
            local_photo_path = os.path.join(local_album_path, photo_name)
            remote_photo_path = f'{remote_album_path}/{photo_name}'
            
            # Check if photo already exists on Yandex Disk
            if y.exists(remote_photo_path):
                # Check if sizes match (to avoid re-uploading identical files)
                local_size = os.path.getsize(local_photo_path)
                remote_info = y.get_meta(remote_photo_path)
                
                if remote_info.size == local_size:
                    skipped_count += 1
                    print_progress(i, len(photos))
                    continue
            
            # Upload photo
            try:
                y.upload(local_photo_path, remote_photo_path, overwrite=True)
                uploaded_count += 1
            except Exception as e:
                print(f'\nError uploading {photo_name}: {e}')
                continue
            
            print_progress(i, len(photos))
        
        print()
        if uploaded_count > 0:
            print(f'✓ Uploaded {uploaded_count} new photo(s)')
        if skipped_count > 0:
            print(f'⊘ Skipped {skipped_count} existing photo(s)')
        print()
    
    print('All albums uploaded successfully!')


def main():
    """Main function to upload albums to Yandex Disk"""
    # You can customize the Yandex Disk path here
    yandex_disk_path = os.getenv('YANDEX_DISK_PATH', '/VK_Albums')
    
    upload_albums_to_yandex_disk(yandex_disk_path)


if __name__ == "__main__":
    main()
