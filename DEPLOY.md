# 🚀 Deployment Guide - Legal AI RAG System

Your application has been configured and optimized for live cloud deployment! 
Here are the easiest methods to take your app from localhost to a public URL.

---

### Option 1: Streamlit Community Cloud (Easiest & Free)
Streamlit Community Cloud is specifically built to deploy Streamlit applications directly from a GitHub repository.

**Steps:**
1. Push this folder to a new **Public or Private GitHub Repository**.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3. Click **New app** and select your repository, branch, and set `app.py` as the main file path.
4. Before clicking Deploy, click on **Advanced settings**.
5. Under `Secrets`, define your OpenAI API key like this:
   ```toml
   OPENAI_API_KEY = "sk-xxxxxxxx"
   ALLOW_DEMO_ACCOUNT = "false"
   ```
6. Click **Deploy**. Your app will be live with a shareable URL in a few minutes!

---

### Option 2: Render.com or Railway (Using Docker)
A highly scalable method is using a Docker platform, which is more stable for libraries like `sentence-transformers`. 
We have already created a `Dockerfile` for you!

**Steps for Render.com:**
1. Push this folder to GitHub.
2. Sign up on [Render.com](https://render.com) and click **New+** -> **Web Service**.
3. Connect your repository. 
4. Render will automatically detect the `Dockerfile` and understand how to build the app.
5. In the **Environment Variables** section, add your secrets:
   * Key: `OPENAI_API_KEY` | Value: `sk-xxxxxxxx`
   * Key: `ALLOW_DEMO_ACCOUNT` | Value: `false`
6. Click **Create Web Service**.

### What I Changed to Better Support Deployment:
1. **Removed Local-Only Libraries (flask, bcrypt, jinja2, etc):** I cleaned up `requirements.txt` to remove packages the Streamlit system doesn't need, drastically reducing server RAM requirements and avoiding deployment limits.
2. **Added a `.streamlit/config.toml`:** This optimizes Streamlit. I disabled anonymous telemetry gathering and CORS errors that often break apps behind server firewalls on Render/Railway.
3. **Provided a `Dockerfile`:** This defines a standard, repeatable environment so your local Python setup flawlessly matches your server container.
4. **Added Bring Your Own Key (BYOK) Support:** Public users can now enter their own personal OpenAI API keys natively in the app's sidebar. If you don't define a global `OPENAI_API_KEY`, your users will be forced to use their own keys to generate LLM responses—saving you the entire bill!

Good luck! Let me know if you run into any permission or API limits with your particular cloud provider.
