import json
import os
import stat

DEFAULT_TOKEN_FILE = os.path.join('data', 'vk_token.json')


def get_token_file_path():
    """Path to the file where VK token set via bot command is stored"""
    return os.getenv('VK_TOKEN_FILE', DEFAULT_TOKEN_FILE)


def read_stored_token():
    """Read VK token saved via the bot command. Returns None if not set"""
    path = get_token_file_path()
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, ValueError, OSError):
        return None

    token = (data or {}).get('access_token')
    return token.strip() if token else None


def save_token(token, saved_by=None):
    """Persist VK token to disk with restrictive permissions"""
    path = get_token_file_path()
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    payload = {'access_token': token.strip()}
    if saved_by is not None:
        payload['saved_by'] = saved_by

    with open(path, 'w') as f:
        json.dump(payload, f)

    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass

    return path


def delete_token():
    """Remove stored VK token. Returns True if a token file was deleted"""
    path = get_token_file_path()
    try:
        os.remove(path)
        return True
    except (FileNotFoundError, OSError):
        return False


def get_access_token():
    """VK token: file set via bot command wins, env variable is the fallback"""
    return read_stored_token() or os.getenv('VK_ACCESS_TOKEN')
