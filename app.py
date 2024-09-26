import os
import jwt
from flask_cors import CORS
from pymongo import MongoClient
from flask import Flask, request, jsonify, Response

import time
from flask_bcrypt import generate_password_hash, check_password_hash
from llm import generate_response
from llm import generate_follow_up_question

# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)

# CORSヘッダーを有効にする
CORS(app)

# MongoDBクライアントを初期化し、データベースとコレクションを指定
client = MongoClient('mongodb://localhost:27017/')
db = client['chiba-chatbot']
users_collection = db['users']
chat_history_collection = db['chat-history']

# シークレットキーを環境変数から取得
SECRET_KEY = os.environ.get("SECRET_KEY")

# ユーザー登録エンドポイント
@app.route('/api/auth/signup', methods=['POST'])
def signup():
	# リクエストデータを取得し、必須項目が存在するか確認
	data = request.get_json()
	if not data or 'username' not in data or 'email' not in data or 'password' not in data:
		return jsonify({"error": "無効なリクエストです。ユーザー名、パスワード、メールアドレスを入力してください。"}), 400

	# メールアドレスが既に存在するか確認
	email = data['email']
	existing_user = users_collection.find_one({"email": email})
	if existing_user:
		return jsonify({"error": "このメールアドレスはすでに使用されています。別のメールアドレスを選択してください。"}), 400

	# パスワードをハッシュ化し、新規ユーザー情報をデータベースに保存
	username = data['username']
	password = generate_password_hash(data['password']).decode('utf-8')

	new_user = {
		"username": username,
		"email": email,
		"password": password,
	}

	users_collection.insert_one(new_user)
	return jsonify({"message": "ユーザーが正常に追加されました。", "email": email}), 201

# ユーザーログインエンドポイント
@app.route('/api/auth/signin', methods=['POST'])
def signin():
	# シークレットキーを取得し、リクエストデータを取得し、必須項目が存在するか確認
	SECRET_KEY = os.environ.get("SECRET_KEY")
	data = request.get_json()
	if not data or 'email' not in data or 'password' not in data:
		return jsonify({"error": "無効なリクエストです。メールアドレスとパスワードを入力してください。"}), 400

	# メールアドレスとパスワードを確認し、正当であればJWTトークンを発行
	email = data['email']
	password = data['password']

	user = users_collection.find_one({"email": email})
	if user:
		username = user.get('username')
		if check_password_hash(user['password'], password):
			exp_time = str(round(time.time()) + 3600)
			token = jwt.encode({
				"iss": email,
				"sub": username,
				"aud": "URL",
				"exp": exp_time
			}, SECRET_KEY, algorithm='HS256')
			user['_id'] = str(user['_id'])
			logined_user = {
				"username": username,
				"email": email
			}
			return jsonify({"message": "ログインに成功しました。", "token": token, "logined_user": logined_user}), 200
		else:
			return jsonify({"error": "メールアドレスまたはパスワードが無効です。"}), 401
	else:
		return jsonify({"error": "指定されたメールアドレスは登録されていません。新しいアカウントを作成してください。"}), 404

# チャットメッセージ追加エンドポイント    
@app.route('/api/chat/add_message', methods=['POST'])
def add_message():
	# リクエストデータを取得し、必須項目が存在するか確認
	data = request.get_json()
	if not data or 'loginid' not in data or 'message_type' not in data or 'message' not in data:
		return jsonify({"error": "無効なリクエストです。LoginID、メッセージタイプ、メッセージを提供してください。"}), 400

	# メッセージタイプによって異なる処理を行い、メッセージをデータベースに保存
	loginid = data['loginid']
	message_type = data['message_type']
	message = data['content']

	if message_type == 'audio':
		if 'audio_path' not in data:
			return jsonify({"error": "音声メッセージの場合、音声ファイルのパスを提供してください。"}), 400
		audio_path = data['audio_path']
	else:
		audio_path = None

	new_message = {
		"loginid": loginid,
		"message_type": message_type,
		"content": message,
		"audio_path": audio_path
	}

	result = chat_history_collection.insert_one(new_message)
	return jsonify({"message": "メッセージが正常に追加されました。", "message_id": str(result.inserted_id)}), 201

# 質問に対する応答エンドポイント
@app.route('/api/chat/respond_to_question', methods=['POST'])
def respond_to_question():
	# リクエストデータを取得し、必須項目が存在するか確認
	data = request.get_json()
	if not data or 'question' not in data:
		return jsonify({"error": "無効なリクエストです。質問を提供してください。"}), 400

	# ユーザーのメールアドレスとチャット履歴を取得し、質問に対する応答を生成
	email = data['email']
	chat_history = data['chat_history']
	question = data['question']
	question_type = data['question_type']

	if(question_type == "text"):
		user = users_collection.find_one({"email": email})

		if user:
			user_chat_history = list(chat_history_collection.find({"email": email}))
			chat_history = []
			for chat in user_chat_history:
				chat_history.append({
					'role': chat['role'],
					'content': chat['content']
				})


		def generate():
			complete_response = []
			for response in generate_response(question, chat_history):
				complete_response.append(response)
				yield response
			
			full_response = "".join(complete_response)
			new_message_user = {
				"email": email,
				"message_type": question_type,
				"role": "user",
				"content": question,
				"audio_path": None
			}

			new_message_ai = {
			    "email": email,
			    "message_type": question_type,
			    "role": "ai",
			    "content": full_response,
			    "audio_path": None
			}

			chat_history_collection.insert_one(new_message_user)
			chat_history_collection.insert_one(new_message_ai)
			
		
		return generate(), {"Content-Type": "text/plain"}

@app.route('/api/chat/get_suggest_question', methods=['POST'])
def get_suggest_question():
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "無効なリクエストです。質問を提供してください。"}), 400
    
    email = data['email']
    chat_history = data['chat_history']
    question = data['question']
    
    user = users_collection.find_one({"email": email})

    if user:
        user_chat_history = list(chat_history_collection.find({"email": email}))
        chat_history = []
        for chat in user_chat_history:
            chat_history.append({
                'role': chat['role'],
                'content': chat['content']
            })
    
    follow_up_questions = generate_follow_up_question(question, chat_history)
    return jsonify({'follow_up_questions': follow_up_questions}), 200

# 特定のユーザーのチャット履歴を取得するエンドポイント
@app.route('/api/user/get_chat_history', methods=['GET'])
def get_chat_history():
	email = request.args.get('email')
	chat_history = list(chat_history_collection.find({'email': email})) 

	formatted_chat_history = []
	for chat in chat_history:
		formatted_chat_history.append({
			'role': chat['role'],
			'content': chat['content'],
		})

	return jsonify(formatted_chat_history)

# ログイン状態を確認するエンドポイント
@app.route('/api/auth/verify_token', methods=['GET'])
def verify_token():
	SECRET_KEY = os.environ.get("SECRET_KEY")
	token = request.headers.get('Authorization')
	if not token:
		return jsonify({'error': 'トークンが欠落しています。'}), 401
	
	try:
		decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'], audience="URL")
		email = decoded_token.get('iss')
		username = decoded_token.get('sub')

		user = users_collection.find_one({'email': email})
		if user:
			return jsonify({'email': email, "username": username}), 200
		else:
			return jsonify({'error': '有効なトークンではありません。'}), 401

	except jwt.ExpiredSignatureError:
		return jsonify({'error': 'トークンの有効期限が切れました。'}), 401
	except jwt.InvalidTokenError:
		return jsonify({'error': '無効なトークンです。'}), 401

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
