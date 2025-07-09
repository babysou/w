from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import os
import json
import uuid
from flask import render_template



app = Flask(__name__)

SONGS_FILE = 'songs.xlsx'
VOTES_FILE = 'votes.json'

@app.route('/')
def index():
    return render_template('index.html')

def load_songs():
    df = pd.read_excel(SONGS_FILE)
    return df.to_dict(orient='records')

def load_votes():
    if not os.path.exists(VOTES_FILE):
        return {}
    with open(VOTES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_votes(votes):
    with open(VOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(votes, f, ensure_ascii=False, indent=2)

def get_client_id():
    client_id = request.cookies.get('client_id')
    if not client_id:
        client_id = str(uuid.uuid4())
    return client_id

@app.route('/songs')
def songs():
    songs = load_songs()
    votes = load_votes()
    client_id = get_client_id()

    standardized_songs = []
    for s in songs:
        song = {
            'Titre': s.get('Titre', 'Titre inconnu'),
            'Artiste': s.get('Artiste', 'Artiste inconnu'),
            'Lien': s.get('URL', '#'), 
            'Extrait': s.get('Extrait') or None
        }
        key = f"{song['Artiste']}|{song['Titre']}"
        vote_data = votes.get(key, {})
        if isinstance(vote_data, dict):
            song['votes'] = vote_data.get('count', 0)
            song['user_voted'] = client_id in vote_data.get('voters', [])
        else:
            song['votes'] = vote_data if isinstance(vote_data, int) else 0
            song['user_voted'] = False

        standardized_songs.append(song)

    response = jsonify(standardized_songs)
    if not request.cookies.get('client_id'):
        response.set_cookie('client_id', client_id, max_age=60*60*24*365*5)
    return response



@app.route('/vote', methods=['POST'])
def vote():
    artist = request.form.get('artist')
    title = request.form.get('title')
    action = request.form.get('action') 
    if not artist or not title or action not in ['like', 'dislike']:
        return jsonify({'error': 'Paramètres invalides'}), 400

    key = f"{artist}|{title}"
    votes = load_votes()
    client_id = get_client_id()

    if key not in votes:
        votes[key] = {'count': 0, 'voters': []}

    voters = votes[key]['voters']

    if action == 'like':
        if client_id not in voters:
            voters.append(client_id)
            votes[key]['count'] += 1
    else:  # dislike
        if client_id in voters:
            voters.remove(client_id)
            votes[key]['count'] = max(votes[key]['count'] - 1, 0)

    save_votes(votes)
    response = jsonify({'votes': votes[key]['count']})
    if not request.cookies.get('client_id'):
        response.set_cookie('client_id', client_id, max_age=60*60*24*365*5)
    return response

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

