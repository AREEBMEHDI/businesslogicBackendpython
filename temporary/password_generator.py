from flask_bcrypt import Bcrypt

# Create an instance of Bcrypt
bcrypt = Bcrypt()

# Generate a password hash
e = bcrypt.generate_password_hash("jason").decode('utf-8')
print(e)