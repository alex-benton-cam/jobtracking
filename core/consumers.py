from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from numpy import var
import requests
from channels.db import database_sync_to_async
from core.models import Location
from core.utils import dbprint

wrapper_group_name = "wrapper_in"
class ManagerConsumer(AsyncJsonWebsocketConsumer):
    
    @database_sync_to_async
    def change_help_var(self, locid, val):
        loc = Location.objects.get(loc_id=locid)
        loc.help_req = val
        loc.save()
    
    
    async def connect(self):
        await self.channel_layer.group_add("manager_websocket",self.channel_name)
        await self.accept()    
    
    
    async def message(self, event):
        #message = json.loads(event['message'])
        dbprint("message sent in managerconsumer")
        await self.send_json(
            {
                "tag":event['tag'],
                "content":event['content'],
                },
            ) 
        
    
        
    async def receive_json(self,content):
        dbprint(f"Manager Websocket got:{content}")
        tag = content.get('tag',None)
        content = content.get('content',None)
               
        if tag == "call_manager_button":
            await self.change_help_var(content, True)
            await self.channel_layer.group_send(
                "manager_websocket",
                {
                    'type':"message",
                    'content':content,
                    'tag':tag
                }
            )     
        
        elif tag == "cancel_call_manager":
            await self.change_help_var(content, False)
        else:
            pass  
        
   
        

class StateUpdateConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(wrapper_group_name,self.channel_name)
        await self.accept()

    async def disconnect(self,close_code):
        pass
    
    async def receive_json(self,content):
        dbprint(f"WSC got:{content}")
        tag = content.get('tag',None)
        content = content.get('content',None)
        dbprint("SU Consumer got {} {}".format(tag, content))

        if tag == "call_manager_button":
            self.channel_layer.group_send(
                        "manager_websocket",
                        {
                            'type':"message",
                            'content':content,
                            'tag':tag
                        }
                    )    
            
        elif tag is not None and content is not None:
            dbprint("WSC sending on channel layer")
            await self.channel_layer.send(
                    "wrapper_out",
                    {
                        'topic':tag,
                        'content':content,
                    }
                )
    
    async def wrapper_in(self,event): # change topic to mqtt topic
        await self.mqtt_update(event)

    async def mqtt_update(self,event):
        message = json.loads(event['message'])
        dbprint("WSC CONSUMER GOT", message)
        if message['state'] == 'entered' or message['state'] == 'changed':
            ws_message = message
            await self.send_json(
                    {
                        "tag":"state-update",
                        "content":ws_message,
                        },
                    )

