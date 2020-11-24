import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import os
import time
import socket
import struct
import sys
import queue
import threading
import select

thing_name = []
thing_ip = []
ss_name = ''
start_flag = 0
num = 1
LARGE_FONT = ("Verdana", 12)


class InitPage(tk.Frame):

    def __init__(self, parent, controller):

        global thing_name, thing_ip
        print("initPage")

        tk.Frame.__init__(self, parent)

        self.queue = queue.Queue()

        thing_name = ''
        thing_ip = ''
        l1 = tk.Label(self, text="Please input your Smart Space name:")  # 标签
        l1.place(x=10, y=10)
        self.ssname_text = tk.Entry(self, relief=tk.RIDGE)  # 创建文本框
        self.ssname_text.place(x=250, y=10)

        l2 = tk.Label(self,
                      text="Please input your online Smart Things' names: (Split by ',' and no space between words, ex:Thing01,Thing02)")
        l2.place(x=10, y=50)
        self.thingname_text = tk.Entry(self, width=70, relief=tk.RIDGE)
        self.thingname_text.place(x=10, y=80)

        # l3 = tk.Label(self, text="Please input your things' ip addresses in VSS accordingly:(Split by ',' and no space between ips, ex:10.254.0.5,10.254.0.7)")
        # l3.place(x=10, y=120)
        # self.thingip_text = tk.Entry(self,width = 70, relief=tk.RIDGE)
        # self.thingip_text.place(x=10, y=150)

        self.l4 = tk.Label(self, text="Please click the button when you input all information!")
        self.l4.place(x=10, y=120)

        self.pbar = ttk.Progressbar(self, orient='horizontal',
                                    length=300, mode='determinate')
        self.btn = tk.Button(self, text="Start", command=lambda: self.spawnthread(controller))

        self.btn.place(x=390, y=150)

        # self.pbar = tk.ttk.Progressbar(self, maximum=2 *(5 * 5), mode='determinate')
        self.pbar.place(x=260, y=180)

    def spawnthread(self, controller):
        global thing_name, thing_ip, ss_name, start_flag
        input_appropriate = True
        temp_things = []
        # temp_ips = []
        ss_name = self.ssname_text.get()  # 获取文本框内容
        print(ss_name)
        thing_name = self.thingname_text.get()
        # thing_ip = self.thingip_text.get()
        if ss_name == '' or thing_name == '':
            # or thing_ip == ''
            tk.messagebox.showinfo('Error', 'Please input your information correctly!')
        # elif len(thing_name.split(',')) != len(thing_ip.split(',')):
        #     tk.messagebox.showinfo('Error', 'Please input same number of thing names and ip addresses!')
        else:
            # 判断thing name是否有重名情况
            thing_name = thing_name.split(',')
            for name in thing_name:
                if name not in temp_things:
                    temp_things += [name]
                else:
                    tk.messagebox.showinfo('Error',
                                           'Please check your thing names! Cannot have two things with the same name!')
                    input_appropriate = False
                    break
            '''
            # 判断ip是否有重复情况，以及判断ip输入格式是否满足"10.254.0.x"的格式
            if input_appropriate == True:
                thing_ip = thing_ip.split(',')
                for ip in thing_ip:
                    if ip not in temp_ips:
                        temp_ips += [ip]
                    else:
                        tk.messagebox.showinfo('Error',
                                               'Please check your ip addresses! Cannot have two things with the same ip!')
                        input_appropriate = False
                        break
                    temp_ip = ip.split('.')
                    if len(temp_ip) != 4 or temp_ip[0] != '10' or temp_ip[1] != '254' or temp_ip[2] != '0':
                        tk.messagebox.showinfo('Error', 'Please input appropriate ip addresses!')
                        input_appropriate = False
                        break
            '''

            # 当所有条件都满足才执行接收步骤
            if input_appropriate == True:
                print("thingname is: ")
                print(thing_name)

                self.btn.config(state="disabled")
                self.thread = ThreadedClient(self.queue)
                self.thread.start()
                self.periodiccall()

                self.l4['text'] = "Start listening. Please wait until the button is available!"

                from startpage import StartPage
                self.btn['command'] = lambda: controller.show_frame(StartPage)

    def periodiccall(self):

        self.checkqueue()
        if self.thread.is_alive():
            self.after(100, self.periodiccall)
        else:
            self.btn.config(state="active")
            if start_flag == 1:
                self.l4['text'] = "Your input was wrong, please exit and restart the program!"
                self.btn["text"] = "exit"
                self.btn["command"] = lambda: InitPage.quit(self)

    def checkqueue(self):
        global num  # account of thing
        while self.queue.qsize():
            msg = self.queue.get(0)
            # self.listbox.insert('end', msg)
            self.pbar['value'] += 100 / num
            # self.pbar.step(25)


class ThreadedClient(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        global thing_name, thing_ip, ss_name, start_flag
        global num  # account of thing
        print("thingname!!!!!!!! ")
        print(thing_name)

        thingID = {}
        ipaddr = {}
        for i in range(len(thing_name)):
            thingID[thing_name[i]] = i
            ipaddr[thing_name[i]] = i
        num = len(thing_name)
        print("thingID!!!!!!!! ", end='')
        print(thingID)

        # All the Thing ID of group 3
        # thingID = {'MySmartThing01': 0, 'MySmartThing02': 1, 'MySmartThing03': 2, 'MySmartThing04': 3, 'MySmartThing05': 4}
        # thingID = {'MySmartThing01': 0}
        onlineThing = set()

        i = len(thing_name)
        firstTweet = [''] * i
        serviceInfo = [[]]
        relationshipInfo = [[]]
        for j in range(i - 1):
            serviceInfo += [[]]
            relationshipInfo += [[]]

        print("firstTweet: ", firstTweet)
        print("serviceInfo: ", serviceInfo)
        print("relationshipInfo", relationshipInfo)

        multicast_group = '232.1.1.1'
        server_address = ('', 1235)

        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(server_address)

        group = socket.inet_aton(multicast_group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:

            sock.setblocking(0)

            ready = select.select([sock], [], [], 40)
            if ready[0]:
                data, server = sock.recvfrom(4096)
            else:
                start_flag = 1
                tk.messagebox.showinfo('Error', 'Time out! Please exit and restart the program')
                break
            # data, server = sock.recvfrom(4096)
            vss = "\"Space ID\" : \"" + ss_name + "\""
            str1 = data.decode("utf-8")
            if vss not in str1:
                continue
            datadict = data.decode("utf-8").replace("\"waitingTime_Seconds\"", "waitingTime_Seconds")
            # print(datadict)
            datadict = datadict.replace("'", "_")
            datadict = datadict.replace("\"", "'")
            # convert dictionary string to dictionary 
            datadict = eval(datadict)

            print("The converted dictionary : " + str(datadict))

            if not thingID:
                break

            if datadict['Thing ID'] in thingID:
                thing = datadict['Thing ID']
                index = thingID[thing]
                tweetType = datadict['Tweet Type']
                print(thing, index, tweetType)
                if datadict in firstTweet:
                    print("pop: " + str(thingID))
                    thingID.pop(thing)
                    print("pop: " + str(thingID))
                    self.queue.put(num)
                else:
                    if thing not in onlineThing:
                        onlineThing.add(thing)
                        firstTweet[index] = datadict
                        print(onlineThing)
                        print("first:" + str(firstTweet))

                    if tweetType == "Identity_Language":
                        ipaddr[thing] = datadict['IP']
                    elif tweetType == 'Service':
                        serviceInfo[index].append(datadict['Name'])
                        print("datadict['Name'] ", datadict['Name'])
                        print("serviceInfo ", serviceInfo)
                    elif tweetType == 'Relationship':
                        rs = [datadict['Name'], datadict['Type'], datadict['FS name'], datadict['SS name']]
                        relationshipInfo[index].append(rs)
                        print(relationshipInfo)
        sock.close()
        print("")
        print("Reception done!\n")
        print("onlineThing: ", onlineThing)
        print("ipaddr: ", ipaddr)
        print("serviceInfo: ", serviceInfo)
        print("relationshipInfo", relationshipInfo)

        # onlineThing = {'MySmartThing01', 'MySmartThing02'}
        onlineThing = list(onlineThing)
        # serviceInfo = [['soil', 'tempC', 'tempF', 'humi'], ['buzzer', 'buzzerRing'], [], [], []]
        f = open('thing.csv', 'w')
        for thingId in ipaddr:
            f.write(thingId + ',' + ipaddr[thingId] + '\n')
        f.close()

        f = open('service.csv', 'w')
        for i in range(len(serviceInfo)):
            for service_name in serviceInfo[i]:
                f.write(service_name + ',' + thing_name[i] + '\n')
        f.close()

        f = open('relationship.csv', 'w')
        f.write("Name,Type,Service1,Service2" + '\n')
        for thing in relationshipInfo:
            if thing:
                for relationship in thing:
                    f.write(
                        relationship[0] + ',' + relationship[1] + ',' + relationship[2] + ',' + relationship[3] + '\n')
        f.close()
