from get_vk_session import get_vk_session

bu_names = ['БЮ', 'Bauman United', 'Бауман Юнайтед', 'BU']
bauman_owners_ids = [-126910967, -76322058]

ext_bu_names = ['БЮ', 'Bauman United', 'Бауман Юнайтед', 'Бауман', 'Bauman', 'BU']
# TODO Убрать альбомы аматорки
owner_ids = [-210711661, -118390813, -219138822, -119296549]


def get_all_albums():
    vk_session = get_vk_session()
    api = vk_session.get_api()
    vk_session._auth_token()
    token = vk_session.token['access_token']
    all_albums_ids = []

    for bauman_owner in bauman_owners_ids:
        all_albums = api.photos.getAlbums(access_token=token, owner_id=bauman_owner)['items']
        bu_albums = list(filter(lambda x: any(name in x['title'] for name in bu_names), all_albums))
        for a in bu_albums:
            all_albums_ids.append('https://vk.com/album' + str(a['owner_id']) + '_' + str(a['id']))

    for owner in owner_ids:
        all_albums = api.photos.getAlbums(access_token=token, owner_id=owner)['items']
        bu_albums = list(filter(lambda x: any(name in x['title'] for name in ext_bu_names), all_albums))
        for a in bu_albums:
            all_albums_ids.append('https://vk.com/album' + str(a['owner_id']) + '_' + str(a['id']))

    with open('albums_list.txt', 'w+') as f:
        # write elements of list
        for a in all_albums_ids:
            f.write('%s\n' % a)

        print("File written successfully")

    # close the file
    f.close()



get_all_albums()