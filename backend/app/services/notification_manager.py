from collections import defaultdict

from fastapi import WebSocket


class NotificationManager:

    def __init__(self):
        self.active_connections = defaultdict(set)

    async def connect(
        self,
        user_id: int,
        websocket: WebSocket
    ):
        self.active_connections[user_id].add(
            websocket
        )

    def disconnect(
        self,
        user_id: int,
        websocket: WebSocket
    ):
        if user_id in self.active_connections:

            self.active_connections[user_id].discard(
                websocket
            )

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(
        self,
        user_id: int,
        message: dict
    ):
        connections = list(
            self.active_connections.get(
                user_id,
                set()
            )
        )

        for websocket in connections:

            try:

                await websocket.send_json(
                    message
                )

            except Exception:

                self.disconnect(
                    user_id,
                    websocket
                )


notification_manager = NotificationManager()