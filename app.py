from flask import Flask, jsonify, request
from flask_cors import CORS
import os 
from google.auth import credentials
from google.auth.transport import requests
from firebase_admin import initialize_app
from firebase_admin import credentials
from firebase_admin import db
from flask_socketio import SocketIO, emit

import json
#import websocket

#from websocket import create_connection

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)
cred = credentials.Certificate("zapisnikendava-firebase-adminsdk-t794o-1174b717b7.json")
initialize_app(cred, {'databaseURL': 'https://zapisnikendava-default-rtdb.europe-west1.firebasedatabase.app/'})
sestanki = []

root = db.reference()

sestanki_ref = root.child('sestanki')
 # websocket = None


@app.route('/create-meeting', methods=['POST', 'OPTIONS'])
def create_meeting():
    if request.method == 'OPTIONS':
        return _build_cors_prelight_response()

    meeting_name = request.form.get('meetingName')
    user_email = request.form.get('userEmail')
    room = {
        'meetingName': meeting_name,
        'participants': [user_email]
    }
    sestanki_ref.push(room)

    return jsonify({'message': 'Sestanek uspešno ustvarjen'})

@app.route('/join-meeting', methods=['POST', 'OPTIONS'])
def join_meeting():
    if request.method == 'OPTIONS':
        return _build_cors_prelight_response()

    meeting_name = request.form.get('meetingName')
    user_email = request.form.get('userEmail')

    snapshot = sestanki_ref.order_by_child('meetingName').equal_to(meeting_name).get()

    room_key = None
    room = None
    for key, value in snapshot.items():
        room_key = key
        room = value

    if room:
        room_participants = room.get('participants', [])
        if user_email in room_participants:

            return jsonify({'message': 'Ta naslov je že prisoten v sestanku'}), 404
        room_participants.append(user_email)
        sestanki_ref.child(room_key).update({'participants': room_participants})

        room['participants'] = room_participants  
       # socketio.emit('permission_request', room_key, room=room_key, namespace='/sestanki')
        return jsonify({'message': 'Uspešno pridružitev sestanku', 'room': room})
    else:
        return jsonify({'message': 'Sestanek ne obstaja', 'room': None}), 404
#def send_permission_request(room_key, room):
 #   global websocket
  #  if websocket is None:
    #    websocket = create_connection('ws://192.168.0.14:5000/socket')
    #permission_request = {
     #   'permission': True,
      #  'email': room['participants'][0]  
    #}
    #websocket.send(json.dumps(permission_request))

    
@app.route('/meeting-participants', methods=['POST', 'OPTIONS'])
def get_meeting_participants():
    if request.method == 'OPTIONS':
        return _build_cors_prelight_response()

    meeting_name = request.form.get('meetingName')

    snapshot = sestanki_ref.order_by_child('meetingName').equal_to(meeting_name).get()

    room = None
    for value in snapshot.values():
        room = value

    if room:
        participants = room['participants']
        return jsonify({'participants': participants})
    else:
        return jsonify({'message': 'Sestanek ne obstaja', 'participants': []}), 404
    

@app.route('/sestanki', methods=['GET', 'OPTIONS'])
def get_sestanki():
    if request.method == 'OPTIONS':
        return _build_cors_prelight_response()

    snapshot = sestanki_ref.get()

    sestanki = []
    for key, value in snapshot.items():
       sestanki.append({key: value})

    return jsonify(sestanki)
transcripts_ref = root.child('transcripts')
@app.route('/save-transcript', methods=['POST', 'OPTIONS'])
def save_transcript():
    if request.method == 'OPTIONS':
        return _build_cors_prelight_response()

    transcript = request.form.get('transcript')

    transcript_data = {
        'transcript': transcript
    }

    transcripts_ref.push(transcript_data)

    return jsonify({'message': 'Transcript successfully saved'})

@app.route('/get-transcripts', methods=['GET', 'OPTIONS'])
def get_transcripts():
    if request.method == 'OPTIONS':
        return _build_cors_prelight_response()

    snapshot = transcripts_ref.get()

    transcripts = []
    for key, value in snapshot.items():
        transcript = value.get('transcript')
        if transcript:
            transcripts.append({'meetingName': key, 'transcript': transcript})

    return jsonify({'transcripts': transcripts})


def _build_cors_prelight_response():
    response = jsonify({'message': 'Preflight CORS check passed'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST')
    return response

if __name__ == '__main__':
    app.run(app, host='0.0.0.0', port=5000)