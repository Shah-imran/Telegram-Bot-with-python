from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerUser, PeerChat, PeerChannel, MessageEmpty, MessageService,InputChannel,InputPeerChannel,InputUser
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.users import GetFullUserRequest
from time import sleep
from pprint import pprint
import json
import traceback
import pickle
import gzip


scraping_limit = 1000000
print('Available Task list:')
print('0: Scrape')
print('1: Add')
task = input('Choose task. (Enter a Number): ')

accounts_data = json.load(open('accounts.json'))
# print(accounts_data['accounts'])
# Telegram login

i=0
clients=[]
for acc in accounts_data['accounts']:
    api_id = acc['api_id']

    api_hash = acc['api_hash']
    phone = acc['phone']
    # print(api_id, api_hash, phone)
    client = TelegramClient('session' + str(i), api_id, api_hash)
    client.connect()
    if not client.is_user_authorized():
        client.send_code_request(phone)
        client.sign_in(phone, input('Enter the code (' + phone + '): '))
    i+=1
    clients.append(client)
chats = []
last_date = None
chunk_size = 100
i=0
groups=[]
targets=[]
while True:
    if i>=1:
        break
    result = clients[0](GetDialogsRequest(
                 offset_date=last_date,
                 offset_id=0,
                 offset_peer=InputPeerEmpty(),
                 limit=chunk_size
                 ))
    chats.extend(result.chats)
    if not result.messages:
        break
    for msg in chats:
        try:
            mgg=msg.megagroup
        except:
            continue
        if msg.megagroup== True:
            groups.append(msg)
        try:
            if msg.access_hash is not None:
                targets.append(msg)
        except:
            pass
    i+=1
    sleep(1)
# for c in chats:
#     pprint(vars(c))


if int(task) == 0:
    print('List of groups:')
    i=0
    for g in groups:
        print(str(i) + '- ' + g.title)
        i+=1
    g_index = input("Choose a group to scrape members from. (Enter a Number): ")
    chat_id_from= groups[int(g_index)].id

    i=0


    target_groups_from=[]

    # print(len(clients))
    for client in clients:
        #pprint(vars(client))
        chats=[]
        i=0
        while True:
            if i>=1:
                break
            result = client(GetDialogsRequest(
                        offset_date=last_date,
                        offset_id=0,
                        offset_peer=InputPeerEmpty(),
                        limit=chunk_size
                    ))
            chats.extend(result.chats)
            if not result.messages:
                break
            for msg in chats:
                try:
                    # print(msg.id)
                    mgg=msg.megagroup
                except:
                    continue
                try:
                    if msg.access_hash is not None:
                        if msg.id== chat_id_from:
                            target_groups_from.append(msg)
                except:
                    pass
            i+=1
            sleep(1)

    if len(target_groups_from)!= len(clients):
        print('All accounts should be a member of both groups.')
        exit()

    groups_participants= []
    i=0
    for client in clients:
        all_participants= []
        offset = 0
        limit = 1000
        while True:
            participants = client.invoke(GetParticipantsRequest(
                InputPeerChannel(target_groups_from[i].id,target_groups_from[i].access_hash), ChannelParticipantsSearch(''), offset, limit
            ))
            if not participants.users:
                break
            # if len(all_participants) >= scraping_limit:
            #     break
            # print(len(all_participants))
            all_participants.extend(participants.users)
            offset += len(participants.users)
            sleep(1)
        i+=1
        print(len(all_participants))
        groups_participants.append(all_participants)
        print(" length of groups - ", len(groups_participants[0]))

    try:
        print("Saving user list...")
        with open('user.txt', 'w+', encoding = "utf-8") as f:
            for item in groups_participants[0]:
                if item.username is not None:
                    f.write("%s\n" % (item.username))
        print("Saving Done...")
    except Exception as e:
        print("Error occured during saving...")
        print(e)
    print("Scraping Completed")

elif int(task) == 1:
    print('List of groups:')
    i=0
    for g in targets:
        print(str(i) + '- ' + g.title)
        i+=1
    g_index = input("Choose a group or channel to add members. (Enter a Number): ")
    chat_id_to= targets[int(g_index)].id

    target_groups_to=[]
    for client in clients:
        #pprint(vars(client))
        chats=[]
        i=0
        while True:
            if i>=1:
                break
            result = client(GetDialogsRequest(
                        offset_date=last_date,
                        offset_id=0,
                        offset_peer=InputPeerEmpty(),
                        limit=chunk_size
                    ))
            chats.extend(result.chats)
            if not result.messages:
                break
            for msg in chats:
                try:
                    # print(msg.id)
                    mgg=msg.megagroup
                except:
                    continue
                try:
                    if msg.access_hash is not None:
                        if msg.id== chat_id_to:
                            target_groups_to.append(msg)
                except:
                    pass
            i+=1
            sleep(1)

    if  len(target_groups_to)!= len(clients):
        print('All accounts should be a member of both groups.')
        exit()

    try:
        i=0
        offset = 0
        limit= 0
        members=[]
        count = 0 
        while True:
            participants = client.invoke(GetParticipantsRequest(
                InputPeerChannel(target_groups_to[i].id,target_groups_to[i].access_hash), ChannelParticipantsSearch(''), offset, limit, hash=0
            ))
            if not participants.users:
                break
            print(count)
            members.extend(participants.users)
            offset += len(participants.users)
            count+=1
            sleep(1)
        memberIds=[]
        for member in members:
            if member.username is not None:
                memberIds.append(member.username)
    except:
        memberIds=[]
        pass

    members_ids = set(memberIds)
    userlist = []
    try:
        with open('user.txt', 'r', encoding = "utf-8") as f:
            _temp = f.read()
            userlist = _temp.split('\n')
            userlist = userlist[:-1]

        for index, user in enumerate(userlist,1):
            if user in members_ids:
                continue

            try:
                __user = clients[0].get_entity(user)
                print('Adding user : ', user ) 
                clients[0].invoke(InviteToChannelRequest(
                InputChannel(target_groups_to[0].id,target_groups_to[0].access_hash),
                [__user],
                ))
                with open('user.txt', 'w+', encoding = "utf-8") as f:
                    for item in userlist[index:]:
                        f.write("%s\n" % (item))
            except Exception as e:
                print(e)
                pass
    except Exception as e:
        print(e)

    print('Adding Completed.')