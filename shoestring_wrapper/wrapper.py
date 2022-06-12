import threading
import socket
import paho.mqtt.client as mqtt
import asyncio
import requests
import json

class MQTTMonitorThread(threading.Thread):
    def __init__(self, name, channel_layer,mqtt_config,channel_groups,topics=[]):
        threading.Thread.__init__(self)
        self.name = name
        self.channel_layer = channel_layer
        self.topics = topics
        self.mqtt_config = mqtt_config
        self.channel_groups = channel_groups

    def run(self):
        print("Starting " + self.name)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(AsyncMqttLoop(self.name,loop,self.channel_layer, self.channel_groups, self.mqtt_config ,self.topics).run())
        loop.close()
        print("Exiting " + self.name)


class AsyncioHelper:
    def __init__(self, loop, client):
        self.loop = loop
        self.client = client
        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_close = self.on_socket_close
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write

    def on_socket_open(self, client, userdata, sock):
        print("MQTT> Socket opened")
        def cb():
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        print("MQTT> Socket closed")
        self.loop.remove_reader(sock)
        self.misc.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        print("MQTT> Watching socket for writability.")
        def cb():
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        print("MQTT> Stop watching socket for writability.")
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break


class AsyncMqttLoop:
    def __init__(self, client_id, loop, channel_layer, channel_groups, mqtt_config, topics = []):
        self.client_id = client_id
        self.loop = loop
        self.channel_layer = channel_layer
        self.channel_groups = channel_groups
        self.mqtt_config = mqtt_config
        self.initial_topics = topics

    def on_connect(self, client, userdata, flags, rc):
        print("MQTT> {id}: subscribing to initial topics: {topics}".format(id=self.client_id,topics=self.initial_topics))
        for topic in self.initial_topics:
            client.subscribe(topic)

    def on_message(self, client, userdata, msg):
        if not self.got_message:
            print("MQTT> {id}: Got unexpected message: {msg}".format(id=self.client_id, msg=msg.decode()))
        else:
            self.got_message.set_result(msg)

    def on_disconnect(self, client, userdata, rc):
        self.disconnected.set_result(rc)

    async def run(self):
        self.disconnected = self.loop.create_future()
       
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        aioh = AsyncioHelper(self.loop, self.client)
        
        #self.client.tls_set('ca.cert.pem',tls_version=2)
        self.client.connect(self.mqtt_config['url'], self.mqtt_config['port'], 60)
        
        t1 = asyncio.create_task(self.check_inbound())
        t2 = asyncio.create_task(self.check_outbound())
        await asyncio.gather(t1,t2)
        self.client.disconnect()
        print("MQTT> Disconnected: {}".format(await self.disconnected))

    async def check_inbound(self):
        self.got_message = self.loop.create_future()
        while True:
            msg = await self.got_message
            print("MQTT> {id}: Got msg: {msg} on topic {topic}".format(msg=msg.payload,id=self.client_id,topic=msg.topic))

            await self.channel_layer.group_send(self.channel_groups.in_group,{'type':f'{self.channel_groups.in_group}','message':msg.payload})
            self.got_message = self.loop.create_future()

    async def check_outbound(self):
        while True:
            payload = await self.channel_layer.receive("wrapper_out")
            topic = 'management_terminal/feeds/'+payload['topic']
            self.client.publish(topic,json.dumps(payload['content']))


class Wrapper:
    inst = None;
    
    def __init__(self):
        self.addr_map = {
                    'statedb':'192.168.0.2:8001'
                }

        self.channel_groups = type('obj',(object,),{
                'in_group':'wrapper_in',
                'out_group':'wrapper_out',
                })()

        self.mqtt_config = {
                    'url':'192.168.0.2',
                    'port':8883,
                }
        # todo from config

    @classmethod
    def get(cls):
        if cls.inst == None:
            cls.inst = cls()
        return cls.inst
    
    @classmethod
    def start(cls,args):
        print("Shoestring Wrapper Starting")
        self = cls.get()
        t = MQTTMonitorThread("mngmt_ui",args['channel_layer'],self.mqtt_config,self.channel_groups,['+/state/update/#'])
        t.start()

    def request(self, endpoint):
        service_id, path = endpoint.split("/",1)
        host = self.get_addr(service_id)
        url = f"http://{host}/{path}"
        response = requests.get(url)
        print(f"got: {response.text}")
        return response.json()

    def subscribe_to(self):
        pass

    def publish(self):
        pass

    def get_addr(self,service_id):
        return self.addr_map[service_id] 


