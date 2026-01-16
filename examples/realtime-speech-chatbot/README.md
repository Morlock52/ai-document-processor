# Realtime Speech Chatbot Example

This example demonstrates how to connect to OpenAI's Realtime API using WebRTC to create a voice-enabled chatbot.

## Usage

1. Set your `OPENAI_API_KEY` environment variable:
   - macOS/Linux: `export OPENAI_API_KEY="sk-..."`
   - PowerShell: `$Env:OPENAI_API_KEY="sk-..."`
2. Start the demo server:

   ```bash
   node server.mjs
   ```

3. Open your browser to [http://localhost:3000](http://localhost:3000) and press **Start Chat**.
4. Allow microphone access and speak with the model.
