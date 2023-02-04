# Better Trek Scriptgen

### To run:

- pip install -r requirements.txt
- (TODO auth ignore this line) Create a character in CAI. Paste the character id (The part after char= in the https://beta.character.ai/chat?char= url of the chat) in the external_id field in config.yaml.
- Modify the rest of config.yaml as desired
- Run parse_chakoteya.py
- The parsed scripts will be in output/chakoteya_convos_{character}_{show}_{episode}.txt
- Copypaste into example convo for CAI
