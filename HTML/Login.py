from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Do something with the username and password
        return 'Welcome, {}!'.format(username)
    else:
        return '''
        <form method="post">
            <label for="username">Username</label>
            <input type="text" name="username" id="username">
            <br>
            <label for="password">Password</label>
            <input type="password" name="password" id="password">
            <br>
            <button type="submit">Login</button>
        </form>
        '''
