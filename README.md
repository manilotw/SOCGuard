# SOC Project
 
### How to run on a server
 
1. Clone the repository
```
git clone <link-to-project>
```
 
2. Go to the project directory
```
cd <name-of-project>
```
 
3. Create a virtual environment
```
python3 -m venv venv
```
 
4. Activate the virtual environment
```
source venv/bin/activate
```
 
5. Install requirements
```
pip install -r requirements.txt
```
 
6. Create a `.env` file and add the environment variables
```
nano .env
```
 
7. Run the bot
```
python src/bot.py
```
 
### Environment variables
 
- `BOT_TOKEN` — Telegram bot token
The script will not start without a `.env` file containing these environment variables.
 
Example:
 
```
BOT_TOKEN=bottoken123
```
