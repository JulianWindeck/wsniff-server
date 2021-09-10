from server import create_server, db
from werkzeug.security import generate_password_hash
from server.models import User, Sniffer

import uuid

app = create_server()
# context to run outside the application (no need to launch the server)
ctx = app.app_context()
ctx.push()  # start working on database after that command

# Database manipulations here

db.drop_all()
db.create_all()

hashed_password = generate_password_hash("feedmepackets", method='sha256')
new_user = User(public_id=str(uuid.uuid4()), name="admin", password=hashed_password, admin=True)
db.session.add(new_user)

sniffer = Sniffer(public_id=str(uuid.uuid4), name="sniffer1", password="hello") 
db.session.add(sniffer)

db.session.commit()

db.session.commit()

# exit from the app
ctx.pop()
