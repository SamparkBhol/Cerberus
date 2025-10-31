import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TrafficConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            'traffic_group',
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            'traffic_group',
            self.channel_name
        )

    async def new_traffic(self, event):
        traffic = event['traffic']
        await self.send(text_data=json.dumps({
            'type': 'traffic',
            'data': traffic
        }))

    async def new_alert(self, event):
        alert = event['alert']
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'data': alert
        }))

    async def system_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'system',
            'data': message
        }))
