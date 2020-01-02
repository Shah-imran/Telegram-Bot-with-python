#!/usr/bin/python3

from settings import USERS
from telethon import TelegramClient
from telethon.tl.types import ChannelParticipantsSearch, PeerChannel, InputUser, User, Chat, InputChannel
from telethon.tl.functions.channels import GetParticipantsRequest, InviteToChannelRequest, JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
import os
import time
import sys
import json
import socks

def telegram_connect(user):
    client = TelegramClient('sessions/' + user['phone'], user['api_id'], user['api_hash'])
    client.connect()

    if not client.is_user_authorized():
        try:
            print('Generating code for ' +'('+ user['phone'] +'), please wait...')
            client.send_code_request(user['phone'])
            client.sign_in(user['phone'], input('Enter the code: '))

            while not client.is_user_authorized():
                print('Bad passcode. Press "s" to skip this user.')
                code = input('Enter the code: ')

                if code == 's':
                    print('Skipping authorization of user ' + user['phone'])
                    break

                time.sleep(2)

                client.sign_in(user['phone'], code)

            if client.is_user_authorized():
                    print(user['phone'] + ' successfully authorized.')
                    time.sleep(5)
                    pass

        except Exception as e:
            print(e)
            print('Skipping this user...')
            time.sleep(5)
            pass

    else:
        print(user['phone'] + ' already authorized.')

    time.sleep(5)
    return client

def scrape(client):
    dialogs, entities = client.get_dialogs(100)

    avail_channels = {}

    channel_id = None
    for i, entity in enumerate(entities):
        if not isinstance(entity, User) and not isinstance(entity, Chat):
            avail_channels[str(i)] = [entity.title, entity.id]

    for k, v in avail_channels.items():
        print(k, v[0])

    if len(avail_channels) < 1:
        print('No super groups to scrape from.')
        sys.exit()

    channel_index = input("Please select number of super group you want to scrape> ")
    channel = client.get_entity(PeerChannel(avail_channels[channel_index][1]))

    # dialogs=client.get_dialogs(500)
    # entity=None
    # for dialog in self.dialogs:
    #     if not isinstance(dialog.input_entity, InputPeerUser) and not isinstance(dialog.input_entity,InputPeerSelf):
    #             avail_channels.append(dialog.name)

    #     if isinstance(dialog.input_entity, InputPeerChannel) and dialog.name==target_group:
    #             entity=dialog.input_entity



    offset = 0
    limit = 200
    all_participants = []
    users = []

    while True:
        try:
            participants = client.invoke(GetParticipantsRequest(channel, ChannelParticipantsSearch(''), offset,limit))
            if not participants.users:
                break
            all_participants.extend(participants.users)
            offset += len(participants.users)

        except Exception as e:
            print(e)
            sys.exit()

    for item in all_participants:       

        users.append(
            {'username': item.username, 'id': item.id, 'access_hash': item.access_hash})



    file_name = avail_channels[channel_index][0].replace(' ', '_')
    file_name = file_name.replace('&', '')
    file_name = file_name.replace('$', '')
    file_name = file_name.replace('/', '')
    file_name = file_name.replace('*', '')
    file_name = file_name.replace('^', '')
    file_name = file_name.replace('~', '')
    file_name = file_name.replace('|', '')

    with open('saksham.json', 'w') as f:
        json.dump(users, f, indent=4)

    print("All users of the channel " + avail_channels[channel_index][
        0] + " has been stored into " +  "saksham.json file.")

def add_users(client, file_name):
        dialogs, entities = client.get_dialogs(100)

        avail_channels = {}

        channel = None
        channel_id = None
        channel_access_hash = None
        for i, entity in enumerate(entities):
                if not isinstance(entity, User) and not isinstance(entity, Chat):
                        avail_channels[str(i)] = [entity, entity.id, entity.access_hash, entity.title]

        for k,v in  avail_channels.items():
                print(k, v[3])

        channel_index = input("Please select number of supergroup where you want to add users> ")

        #participants = client.invoke(GetParticipantsRequest(avail_channels[channel_index][0], ChannelParticipantsSearch(''), 0, 0))
        #count_of_members_before_adding = len(participants.users)

        users = None
        try:
                with open(file_name, 'r') as f:
                        users = json.load(f)

        except Exception:
                print('Invalid file name, make sure you have added extension or if file even exists, if not, run scrape_channel_users.py to create one!')
                sys.exit()

        count = int(input('Do you want to add only subset of users('+ str(len(users)) +')? if so, enter the number of users to be added: '))

        users_to_save_back = users[count:] # only users, which didnt be used, will be saved to file again
        print(str(len(users_to_save_back)) + ' users to be saved back to json file!')
        users = users[:count] # users to be added
        print(str(len(users)) + ' users to be removed from list!')
        print()

        with open(file_name, 'w') as f:
                json.dump(users_to_save_back, f, indent=4)

        input_users = []
        for item in users:
                input_users.append(InputUser(item['id'], item['access_hash']))


        user_chunks = list(chunks(input_users, 40))

        for item in user_chunks:
                try:
                        client(InviteToChannelRequest(InputChannel(avail_channels[channel_index][1], avail_channels[channel_index][2]), item))

                        print('Adding chunk of '+ str(len(item)) +' users...')
                        time.sleep(2)
                except Exception as e:
                        print(str(e))
                        print('some error occurred, skipping to next chunk.')
                        time.sleep(2)

        print('There was attempt to add ' + str(len(input_users)) + ' users in total.')

        #participants = client.invoke(GetParticipantsRequest(avail_channels[channel_index][0], ChannelParticipantsSearch(''), 0, 0))
        #count_of_members_after_adding = len(participants.users)

        #print('Count of members before adding: ' + str(count_of_members_before_adding))
        #print('Count of members after adding: ' + str(count_of_members_after_adding))
        print()
        #print('True number of added users: ' + str(count_of_members_after_adding - count_of_members_before_adding))
        print('added')


def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        yield l[i:i+n]


def remove():
    users = None
    with open(file_name, 'r') as f:
        users = json.load(f)
    value1=int(input("The file has" + str(len(users)) + ".Enter how many you want to remove :"))
    print("Removing" + str(value1) + "users") 
    users_to_save_back = users[value1:] # only users, which didnt be used, will be saved to file again
    print(str(len(users_to_save_back)) + ' users to be saved back to json file!')
    with open(file_name, 'w') as f:
        try:
            json.dump(users_to_save_back, f, indent=4)
        except Exception as e:
            print(e)




def options(client,file_name):
    client1=client
    file_name1=file_name
    while True:
        value=input("Press 1 for addition if not 50, 2 for deletion from json, else to end :")
        if value=="1":
            add_users(client1,file_name1)
        elif value=="2":
            remove()       
        else:
            break


if __name__ == '__main__':
    for user in USERS:
    #user = check_arguments()
        client=telegram_connect(user)
        #entity1=client.get_entity('girlspod')
        #client(JoinChannelRequest(entity1))
        #entity2=client.get_entity('dx5Lcs')
        #client(JoinChannelRequest(entity2))
        #try:
        #    updates = client(ImportChatInviteRequest('IE9TC0U1ENCkA5LVPIzLrQ'))
        #except Exception as e:
        #    pass    
        scrape(client)
        file_name= "saksham.json"
        add_users(client, file_name)
        options(client,file_name)
        client.disconnect()                
