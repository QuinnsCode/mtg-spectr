from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return {'message': 'Hello from Flask on Vercel!'}

@app.route('/api/health')
def health():
    return {'status': 'healthy'}