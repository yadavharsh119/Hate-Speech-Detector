from pyngrok import ngrok

# Open a tunnel to port 8000
public_url = ngrok.connect(8000)
print(f"🚀 Tunnel Active! Public URL: {public_url}")
print("Keep this script running while testing webhooks.")

# Keep the script alive
input("Press Enter to close tunnel...")
