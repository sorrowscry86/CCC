#!/usr/bin/env python3
"""
Secure OpenAI API Proxy Server for CCC (Covenant Command Cycle)

This Flask server acts as a secure proxy to the OpenAI API, protecting
the API key and providing controlled access to AI capabilities.
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = 'https://api.openai.com/v1'
HOST = '127.0.0.1'
PORT = 5111

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set!")
    raise ValueError("OPENAI_API_KEY is required but not found in environment variables")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'CCC OpenAI Proxy',
        'version': '1.0.0'
    })


@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """
    Proxy endpoint for OpenAI chat completions
    Forwards requests to OpenAI API with proper authentication
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Prepare headers for OpenAI API
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Log the request (without sensitive data)
        logger.info(f"Proxying chat completion request with model: {data.get('model', 'unknown')}")
        
        # Forward request to OpenAI
        response = requests.post(
            f'{OPENAI_API_BASE}/chat/completions',
            json=data,
            headers=headers,
            timeout=30
        )
        
        # Return the response
        if response.status_code == 200:
            logger.info("Successfully proxied request to OpenAI")
            return jsonify(response.json())
        else:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return jsonify({
                'error': 'OpenAI API error',
                'status_code': response.status_code,
                'message': response.text
            }), response.status_code
            
    except requests.exceptions.Timeout:
        logger.error("Request to OpenAI API timed out")
        return jsonify({'error': 'Request timeout'}), 408
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({'error': 'Request failed', 'details': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info(f"Covenant API Proxy is running on http://{HOST}:{PORT}")
    logger.info("Make sure OPENAI_API_KEY is set in your environment variables")
    app.run(host=HOST, port=PORT, debug=False)