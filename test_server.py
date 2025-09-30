#!/usr/bin/env python3
"""
Simple Flask Test Server - VoidCat RDC Diagnostic Tool
"""

from flask import Flask, jsonify
import sys

app = Flask(__name__)

@app.route('/test')
def test():
    return jsonify({'status': 'Flask test server is working!', 'message': 'VoidCat RDC Diagnostic'})

if __name__ == '__main__':
    print("Starting simple Flask test server on port 5111...")
    try:
        app.run(host='0.0.0.0', port=5111, debug=True)
    except Exception as e:
        print(f"Flask server failed to start: {e}")
        sys.exit(1)