// tcp server на ПИТОНЕ ДЛЯ ВДС! (УДОЛИТЕ ЭТО СООБЩЕНИЯ)

import socket
import threading
import json
from pymongo import MongoClient
from bson import ObjectId, json_util
from bson.json_util import dumps
from datetime import datetime
import base64
import io
from PIL import Image

class MongoDBHandler:
    def init(self):
        self.MONGO_URI = "mongodb://ССЫЛКУ НА МОНГО/admin"
        self.DB_NAME = "ИМЯ БД"
        self.client = MongoClient(self.MONGO_URI)
        self.db = self.client[self.DB_NAME]
        self.accounts_collection = self.db["accounts"]
        self.settings_collection = self.db["settings"]
        
        # Инициализация настроек
        self._ensure_settings_exists()

    def _ensure_settings_exists(self):
        if not self.settings_collection.find_one({"_id": ObjectId("674fe33f0948d62d6ccdad86")}):
            self.settings_collection.insert_one({
                "_id": ObjectId("674fe33f0948d62d6ccdad86"),
                "Version": "1.0.0",
                "LastId": 0
            })

    def handle_request(self, data):
        try:
            request = json.loads(data)
            operation = request["operation"]
            handler = getattr(self, f"handle_{operation}", None)
            
            if not handler:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
            
            return handler(request.get("params", {}))
        
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def handle_register_user(self, params):
        player_name = params["player_name"]
        xvid = params["xvid"]
        
        # Получаем новый ID
        last_id = self.get_last_id() + 1
        self.increment_last_id()
        
        # Генерация аватара по умолчанию
        avatar_data = self.generate_default_avatar()
        
        player_data = {
            "Name": player_name,
            "Id": str(last_id),
            "ClanTag": "",
            "LevelXp": 0,
            "LevelId": 0,
            "Avatar": avatar_data,
            "IsTester": False,
            "Ban": False,
            "BanReason": "",
            "Status": "Online",
            "Xvid": xvid,
            "RoomId": "",
            "TimeInGame": 0,
            "Kills": 0,
            "Hits": 0,
            "Shots": 0,
            "MatchesPlayed": 0,
            "Assists": 0,
            "Headshots": 0,
            "Damage": 0,
            "Deaths": 0,
            "Friends": []
        }
        
        result = self.accounts_collection.insert_one(player_data)
        return {"status": "success", "inserted_id": str(result.inserted_id)}

    def generate_default_avatar(self):
        # Создание простого изображения (красный квадрат)
        img = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

    def handle_login_xvid_user(self, params):
        xvid = params["xvid"]
        player = self.accounts_collection.find_one({"Xvid": xvid})
        
        if player:
            return {"status": "success", "player_exists": True}
        else:
            # Автоматическая регистрация
            player_name = f"SP_{self.generate_random_code(4)}"
            self.handle_register_user({"player_name": player_name, "xvid": xvid})
            return {"status": "success", "player_exists": False}

    def generate_random_code(self, length):
        import random
        return ''.join(str(random.randint(0, 9)) for _ in range(length))

    def handle_validate_account(self, params):
        xvid = params["xvid"]
        player = self.accounts_collection.find_one({"Xvid": xvid})
        
        if not player:
            return {"status": "error", "message": "Player not found"}
if player.get("Ban", False):
            ban_reason = player.get("BanReason", "No reason provided")
            banned_avatar = self.generate_banned_avatar()
            
            self.accounts_collection.update_one(
                {"Xvid": xvid},
                {"$set": {"Status": "Banned", "Avatar": banned_avatar}}
            )
            
            return {
                "status": "banned",
                "ban_reason": ban_reason,
                "player_id": player["Id"]
            }
        
        self.accounts_collection.update_one(
            {"Xvid": xvid},
            {"$set": {"Status": "Online"}}
        )
        
        return {"status": "success", "player_status": "Online"}

    def generate_banned_avatar(self):
        # Создание забаненного аватара (серый квадрат)
        img = Image.new('RGB', (100, 100), color='gray')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

    def handle_get_new_version(self, params):
        settings = self.settings_collection.find_one(
            {"_id": ObjectId("674fe33f0948d62d6ccdad86")}
        )
        return {"status": "success", "version": settings["Version"]}

    # Остальные методы обработки (get_id, set_id, add_friend и т.д.)
    # Реализованы по аналогии с C# кодом
    
    def get_last_id(self):
        settings = self.settings_collection.find_one(
            {"_id": ObjectId("674fe33f0948d62d6ccdad86")}
        )
        return settings.get("LastId", 0)

    def increment_last_id(self):
        self.settings_collection.update_one(
            {"_id": ObjectId("674fe33f0948d62d6ccdad86")},
            {"$inc": {"LastId": 1}}
        )
    
    def handle_set_player_status(self, params):
        self.accounts_collection.update_one(
            {"Xvid": params["xvid"]},
            {"$set": {"Status": params["status"]}}
        )
        return {"status": "success"}
    
    def handle_get_player_status(self, params):
        player = self.accounts_collection.find_one({"Xvid": params["xvid"]})
        return {
            "status": "success",
            "player_status": player.get("Status", "Offline") if player else "Offline"
        }
    
    # Другие методы...
    # Реализуйте остальные методы по аналогии

class TCPServer:
    def init(self, host='ТУТ ИП', port=ТУТ ПОРТИК):
        self.host = host
        self.port = port
        self.db_handler = MongoDBHandler()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

    def handle_client(self, client_socket):
        with client_socket:
            buffer = b""
            while True:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    buffer += data
                    
                    # Разделяем сообщения по символу новой строки
                    while b'\n' in buffer:
                        msg, buffer = buffer.split(b'\n', 1)
                        response = self.process_message(msg.decode())
                        client_socket.sendall((json.dumps(response) + '\n').encode())
                
                except ConnectionResetError:
                    break
                except Exception as e:
                    error_resp = json.dumps({
                        "status": "error", 
                        "message": f"Processing error: {str(e)}"
                    })
                    client_socket.sendall((error_resp + '\n').encode())
                    break

    def process_message(self, message):
        return self.db_handler.handle_request(message)
def start(self):
        while True:
            client_sock, addr = self.server_socket.accept()
            print(f"Accepted connection from {addr}")
            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_sock,),
                daemon=True
            )
            client_thread.start()

if name == "main":
    server = TCPServer()
    server.start()
