""" Client code that connects to the routing agent """

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import os
import requests
from dotenv import load_dotenv
import uvicorn
import asyncio
import re
from markupsafe import escape

load_dotenv()

server = os.environ["SERVER_URL"]
port = os.environ["ROUTING_AGENT_PORT"]

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Agent Chat</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f8f9fa;
                line-height: 1.6;
            }
            
            #chat { 
                width: 100%; 
                max-width: 800px; 
                margin: auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h2 {
                margin: 0 0 10px 0;
                font-size: 1.8em;
            }
            
            .header h3 {
                margin: 0;
                font-weight: 300;
                opacity: 0.9;
                font-size: 1.1em;
            }
            
            #messages { 
                padding: 20px;
                height: 400px; 
                overflow-y: auto;
                border-bottom: 1px solid #eee;
            }
            
            .message {
                margin-bottom: 20px;
                padding: 15px;
                border-radius: 8px;
                max-width: 85%;
            }
            
            .user-message {
                background: #e3f2fd;
                border-left: 4px solid #2196f3;
                margin-left: auto;
                text-align: right;
            }
            
            .agent-message {
                background: #f3e5f5;
                border-left: 4px solid #9c27b0;
            }
            
            .sender {
                font-weight: 600;
                margin-bottom: 8px;
                color: #333;
            }
            
            .message-content {
                color: #444;
            }
            
            /* Formatted response styles */
            .response-header {
                color: #7b1fa2;
                border-bottom: 2px solid #e1bee7;
                padding-bottom: 8px;
                margin: 20px 0 15px 0;
                font-size: 1.2em;
                font-weight: 600;
            }
            
            .title-suggestion {
                background: #fff3e0;
                padding: 12px;
                border-radius: 6px;
                border-left: 4px solid #ff9800;
                margin: 15px 0;
            }
            
            .title-suggestion em {
                font-style: italic;
                color: #f57c00;
                font-weight: 600;
                font-size: 1.05em;
            }
            
            .list-item {
                margin-bottom: 12px;
                padding-left: 8px;
                line-height: 1.5;
            }
            
            .list-item strong {
                color: #4a148c;
                display: block;
                margin-bottom: 4px;
            }
            
            .sub-item {
                margin-left: 20px;
                color: #666;
                font-size: 0.95em;
                margin-bottom: 4px;
            }
            
            .highlight {
                background: #fff59d;
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: 500;
            }
            
            .input-container {
                padding: 20px;
                background: #fafafa;
                display: flex;
                gap: 10px;
            }
            
            #user-input { 
                flex: 1;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.3s;
            }
            
            #user-input:focus {
                border-color: #667eea;
            }
            
            #send-btn { 
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: transform 0.2s;
            }
            
            #send-btn:hover {
                transform: translateY(-1px);
            }
            
            #send-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .loading {
                color: #666;
                font-style: italic;
            }
        </style>
    </head>
    <body>
        <div id="chat">
            <div class="header">
                <h2>Sidney's Blog Title & Outline Assistant</h2>
                <h3>Tell us what topic is on your mind, and we will help you create a blog title and outline!</h3>
            </div>
            <div id="messages"></div>
            <div class="input-container">
                <input type="text" id="user-input" placeholder="Type your message..." />
                <button id="send-btn">Send</button>
            </div>
        </div>
        
        <script>
    const messages = document.getElementById('messages');
    const input = document.getElementById('user-input');
    const btn = document.getElementById('send-btn');

    function appendMessage(sender, text) {
        const wrapper = document.createElement('div');
        wrapper.classList.add('message');

        if (sender === 'User') {
            wrapper.classList.add('user-message');
            wrapper.innerHTML = `
                <div class="sender">${sender}</div>
                <div class="message-content">${escapeHtml(text)}</div>
            `;
        } else {
            wrapper.classList.add('agent-message');
            wrapper.innerHTML = `
                <div class="sender">${sender}</div>
                <div class="message-content">${text}</div>
            `;
        }

        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
    }

    // Prevents malicious HTML injection in user messages
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    btn.onclick = async function() {
        const prompt = input.value.trim();
        if (!prompt) return;
        appendMessage('User', prompt);
        input.value = '';
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        const data = await res.json();
        appendMessage('Agent', data.response);
    };

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') btn.click();
    });
</script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    url = f"http://{server}:{port}/message"
    payload = {"message": prompt}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            agent_raw = response.json().get("response", "No response from agent.")
        else:
            agent_raw = f"Error {response.status_code}: {response.text}"
    except Exception as e:
        agent_raw = f"Request failed: {e}"

    # --- Formatting logic ---
    formatted_lines = []
    for line in agent_raw.splitlines():
        line = line.strip()
        if not line:
            continue

        # Headers like ### Suggested Book Title
        if line.startswith("###"):
            formatted_lines.append(
                f'<div class="response-header">{escape(line.lstrip("# ").strip())}</div>'
            )

        # Numbered list: 1. Something
        elif re.match(r"^\d+\.\s+", line):
            title = re.sub(r"^\d+\.\s*", "", line)
            formatted_lines.append(
                f'<div class="list-item"><strong>{escape(title)}</strong></div>'
            )

        # Bullets with dash
        elif line.startswith("- "):
            formatted_lines.append(
                f'<div class="sub-item">{escape(line[2:].strip())}</div>'
            )

        # Bold segments (**like this**)
        elif "**" in line:
            html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escape(line))
            formatted_lines.append(f'<div class="list-item">{html}</div>')

        else:
            formatted_lines.append(f'<div class="sub-item">{escape(line)}</div>')

    formatted_html = "\n".join(formatted_lines)

    return JSONResponse({"response": formatted_html})

# 👇 reusable async main
async def main():
    """Entry point for running the FastAPI client app"""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

# 👇 standalone mode support
if __name__ == "__main__":
    asyncio.run(main())
