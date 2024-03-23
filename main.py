from flask import render_template, request, Flask, redirect, url_for, make_response, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import hashlib
import json
import os
import sqlite3

secret_key = b'SECRET_KEY_FOR_FAKEGRAMM'

def connectupdate():
    global connect_user
    global cursor_user
    global connect_album
    global cursor_album
    connect_user = sqlite3.connect(database='static/data/user.db')
    cursor_user = connect_user.cursor()
    connect_album = sqlite3.connect(database='static/data/album.db')
    cursor_album = connect_album.cursor()
connectupdate()
cursor_user.execute('''CREATE TABLE IF NOT EXISTS users(
                    token TEXT, 
                    email TEXT,
                    id INT,
                    name TEXT,
                    albumcol TEXT
               )''')
cursor_user.execute('''CREATE TABLE IF NOT EXISTS album(
                    userid INT,
                    mainid INT,
                    access TEXT,
                    approved TEXT,
                    name TEXT
               )''')
if cursor_user.execute("SELECT max(id) FROM users").fetchone()[0] is None:
    cursor_user.execute("INSERT INTO users VALUES(0, 0, 0, 0, 0)")
    cursor_user.execute("INSERT INTO album VALUES(0, 0, 0, 0, 0)")
    connect_user.commit()

app = Flask(__name__)
cors = CORS(app)

@app.route('/login', methods=['POST', 'GET'])
def login():
    connectupdate()
    if 'token' in request.cookies:
        if cursor_user.execute("SELECT name FROM users WHERE token='{}'".format(request.cookies.get('token'))).fetchone() is not None:
            return redirect(url_for('account'))
        else:
            response = make_response(redirect(url_for('login')))
            response.set_cookie('token', '', expires=0)
            return response
    if request.method == 'POST':
        user = request.form['email'] + request.form['password']
        token = token = hashlib.sha256(user.encode() + secret_key).hexdigest()
        result = cursor_user.execute("SELECT id FROM users WHERE token = '{}'".format(token)).fetchone()
        if result is None or result[0] is None:
            return render_template('login.html', error='Неправильная почта или пароль.')
        else:
            response = make_response(redirect(url_for('account')))
            response.set_cookie('token', token, max_age=15778800, secure=True, httponly=True)
            return response
    else:
        return render_template('login.html')
@app.route('/register', methods=['POST', 'GET'])
def register():
    if 'token' in request.cookies:
        return redirect(url_for('account'))
    if request.method == 'POST':
        connectupdate()
        user = str(request.form['email'] + request.form['password'])
        if cursor_user.execute("SELECT name FROM users WHERE email='{}'".format(request.form['email'])).fetchone() is None:
            name = request.form['name']
            token = hashlib.sha256(user.encode() + secret_key).hexdigest()
            maxid = int(cursor_user.execute("SELECT max(id) FROM users").fetchone()[0])+1
            maxalbum = 1+int(cursor_user.execute("SELECT max(mainid) FROM album").fetchone()[0])
            maxalbum = [maxalbum]
            cursor_user.execute("INSERT INTO users VALUES('{}', '{}', {}, '{}', '{}')".format(token, request.form['email'], maxid, name, maxalbum))
            connect_user.commit()
            cursor_album.execute(f'''CREATE TABLE IF NOT EXISTS _{maxalbum[0]}(
                    id INT,
                    patch TEXT,
                    name TEXT,
                    tags TEXT
               )''')
            cursor_album.execute(f"INSERT INTO _{maxalbum[0]} VALUES(0, 0, 0, 0)")
            connect_album.commit()
            cursor_user.execute("INSERT INTO album VALUES({}, {}, 1, NULL, 'Общий')".format(maxid, maxalbum[0]))
            connect_user.commit()
            response = make_response(redirect(url_for('account')))
            response.set_cookie('token', token, max_age=15778800, secure=True, httponly=True)
            os.mkdir(os.path.join("static/data/img", f'{maxalbum[0]}'))
            return response
        else:
            return render_template('register.html', error='Почта уже зарегестрирована.')
    else:
        return render_template('register.html')

@app.route('/account', methods=['POST', 'GET'])
def account():
    if not request.cookies.get('token'):
        return redirect(url_for('login'))
    connectupdate()
    if cursor_user.execute("SELECT name FROM users WHERE token='{}'".format(request.cookies.get('token'))).fetchone() is None:
        return redirect(url_for('login'))
    data = cursor_user.execute("SELECT email, name, id FROM users WHERE token = '{}'".format(request.cookies.get('token'))).fetchone()
    email, name, ids = data[0], data[1], data[2]
    if email is None:
        response = make_response(redirect(url_for('account')))
        response.set_cookie('token', '', expires=0)
        return response
    return render_template('account.html', email=email, username=name, ids=ids)
@app.route('/account/logout', methods=['GET'])
def logout():
    if not request.cookies.get('token'):
        return redirect(url_for('login'))
    else:
        response = make_response(redirect(url_for('login')))
        response.set_cookie('token', '', expires=0)
        return response
@app.route('/account/delete', methods=['GET'])
def delete_account():
    connectupdate()
    if not request.cookies.get('token'):
        return redirect(url_for('login'))
    else:
        album_list=eval(cursor_user.execute(f"SELECT albumcol FROM users WHERE token = '{request.cookies.get('token')}'").fetchone()[0])
        for i in album_list:
            maximgid=cursor_album.execute(f"SELECT max(id) FROM _{i}").fetchone()[0]
            for num in range(1, maximgid+1):
                patch = cursor_album.execute(f"SELECT patch FROM _{i} WHERE id = '{num}'").fetchone()[0]
                if patch is not None:
                    os.remove(f"{patch}")
            os.rmdir(f'static/data/img/{i}')
            cursor_album.execute(f'''DROP TABLE IF EXISTS _{i};''')
            cursor_user.execute(f"DELETE FROM album WHERE mainid='{i}'")
        cursor_user.execute("DELETE FROM users WHERE token='{}'".format(request.cookies.get('token')))
        connect_user.commit()
        connect_album.commit()
        response = make_response(redirect(url_for('login')))
        response.set_cookie('token', '', expires=0)
        
        return response
@app.route('/account/emailchange', methods=['POST', 'GET'])
def change_email():
    connectupdate()
    if not request.cookies.get('token'):
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('emailswitch.html')
    else:
        password = request.form['password']
        email =  request.form['email']
        name = request.form['name']
        user = email+password
        token = hashlib.sha256(user.encode() + secret_key).hexdigest()
        ids = cursor_user.execute(f"SELECT id FROM users WHERE token='{request.cookies.get('token')}'").fetchone()[0]
        if  ids is not None:
            cursor_user.execute(f"UPDATE users SET email = '{email}' WHERE id={ids}")
            cursor_user.execute(f"UPDATE users SET token = '{token}' WHERE id={ids}")
            cursor_user.execute(f"UPDATE users SET name = '{name}' WHERE id={ids}")
            connect_user.commit()
            response = make_response(redirect(url_for('account')))
            response.set_cookie('token', '', expires=0)
            response.set_cookie('token', token, max_age=15778800, secure=True, httponly=True)
            return response
        else:
            response = make_response(redirect(url_for('login')))
            response.set_cookie('token', '', expires=0)
            return response
@app.route('/view/<user_id>')
def view_profile(user_id):
    connectupdate()
    is_author = False
    if request.cookies.get('token') is None: 
        return render_template('show.html', is_author=is_author, name=cursor_user.execute(f"SELECT name FROM users WHERE id='{user_id}'").fetchone()[0])
    if str(user_id) == str(cursor_user.execute(f"SELECT id FROM users WHERE token='{request.cookies.get('token')}'").fetchone()[0]):
        is_author = True
    return render_template('show.html', is_author=is_author, name=cursor_user.execute(f"SELECT name FROM users WHERE id='{user_id}'").fetchone()[0])
@app.route('/api/albums/<user_id>')
def get_albums(user_id):
    connectupdate()
    if cursor_user.execute(f"SELECT id FROM users WHERE id = '{user_id}'").fetchone()[0] is not None:
        albumlist=json.loads(cursor_user.execute(f"SELECT albumcol FROM users WHERE id = {user_id}").fetchone()[0])
        albums_data = []
        if request.cookies.get('token') is not None: 
                current_userid = cursor_user.execute(f"SELECT id FROM users WHERE token = '{request.cookies.get('token')}'").fetchone()[0]
                if str(user_id) == str(cursor_user.execute(f"SELECT id FROM users WHERE token='{request.cookies.get('token')}'").fetchone()[0]):
                    is_author=True
                else:
                    is_author=False
        else:
                current_userid=0
                is_author=False
        for album_id in albumlist:
            access=int(cursor_user.execute(f"SELECT access FROM album WHERE mainid='{album_id}'").fetchone()[0])
            if access == 0 and is_author == False:
                resp=cursor_user.execute(f"SELECT approved FROM album WHERE mainid='{album_id}'").fetchone()[0]
                if resp is None:
                    name=cursor_user.execute(f"SELECT name FROM album WHERE mainid='{album_id}'").fetchone()[0]
                    albums_data.append({
                    'id': album_id,
                    'name': name
                    })
                    continue
                if str(current_userid) not in eval(resp):
                    continue
            name=cursor_user.execute(f"SELECT name FROM album WHERE mainid='{album_id}'").fetchone()[0]
            albums_data.append({
                    'id': album_id,
                    'name': name
                })
        return jsonify({'albums': albums_data})

@app.route('/view/<user_id>/album/<album_id>')
def view_album(user_id, album_id):
    connectupdate()
    if request.cookies.get('token') is not None: 
            current_userid = cursor_user.execute(f"SELECT id FROM users WHERE token = '{request.cookies.get('token')}'").fetchone()[0]
            if str(user_id) == str(cursor_user.execute(f"SELECT id FROM users WHERE token='{request.cookies.get('token')}'").fetchone()[0]):
                is_author=True
            else:
                is_author=False
    else:
        current_userid=0
        is_author=False
    access=int(cursor_user.execute(f"SELECT access FROM album WHERE mainid='{album_id}'").fetchone()[0])
    if access == 0 and is_author == False:
        resp=eval(cursor_user.execute(f"SELECT approved FROM album WHERE mainid='{album_id}'").fetchone()[0])
        if resp is None:
            name=cursor_user.execute(f"SELECT name FROM album WHERE mainid='{album_id}'").fetchone()[0]
            is_author = False
            if request.cookies.get('token') is not None: 
                if str(cursor_user.execute(f"SELECT userid FROM album WHERE mainid='{album_id}'").fetchone()[0]) == str(cursor_user.execute(f"SELECT id FROM users WHERE token='{request.cookies.get('token')}'").fetchone()[0]):
                    is_author = True
            else:
                is_author = False
            return render_template('album.html', albumname=name, is_author=is_author)
        if str(current_userid) not in eval(resp):
            return redirect(url_for(f'view/{user_id}'))
        
    else:
        name=cursor_user.execute(f"SELECT name FROM album WHERE mainid='{album_id}'").fetchone()[0]
        return render_template('album.html', albumname=name, is_author=is_author)
@app.route('/api/photos/<user_id>/<album_id>')
def get_photos(user_id, album_id):
    connectupdate()
    if request.cookies.get('token') is not None: 
        current_userid = cursor_user.execute(f"SELECT id FROM users WHERE token = '{request.cookies.get('token')}'").fetchone()[0]
        if str(user_id) == str(cursor_user.execute(f"SELECT id FROM users WHERE token='{request.cookies.get('token')}'").fetchone()[0]):
            is_author=True
        else:
            is_author=False
    else:
        current_userid=0
        is_author=False
    photos_data = []
    for ids in range(1, int(cursor_album.execute(f"SELECT max(id) FROM _{album_id}").fetchone()[0])+1):
        if cursor_album.execute(f"SELECT patch FROM _{album_id} WHERE id='{ids}'").fetchone() is not None:
            name = cursor_album.execute(f"SELECT name FROM _{album_id} WHERE id = {ids}").fetchone()[0]
            patch = cursor_album.execute(f"SELECT patch FROM _{album_id} WHERE id = {ids}").fetchone()[0]
            ids = cursor_album.execute(f"SELECT id FROM _{album_id} WHERE id = {ids}").fetchone()[0]
            tags=[cursor_album.execute(f"SELECT tags FROM '_{album_id}' WHERE id={ids}").fetchone()[0]]
            photos_data.append({
                    'name': name,
                    'url': patch,
                    'tags': tags,
                    'id': ids
                })
    access=int(cursor_user.execute(f"SELECT access FROM album WHERE mainid='{album_id}'").fetchone()[0])
    if access == 0 and is_author == False:
        resp=eval(cursor_user.execute(f"SELECT approved FROM album WHERE mainid='{album_id}'").fetchone()[0])
        if resp is None:
            return jsonify({'photos': photos_data})
        else:
            if current_userid in resp:
                return jsonify({'photos': photos_data})
            else:
                return jsonify({'message': 'Access deny'})
    else:
        return jsonify({'photos': photos_data})

@app.route('/api/albums/<user_id>/<album_id>', methods=['PUT'])
def rename_album(user_id, album_id):
    connectupdate()
    if int(user_id) == cursor_user.execute(f"SELECT userid FROM album WHERE mainid='{album_id}'").fetchone()[0]:
        new_name = request.json.get('name')
        cursor_user.execute(f"UPDATE album SET name = '{new_name}' WHERE mainid={album_id}")
        connect_user.commit()
        return jsonify({'message': 'Album renamed successfully'})
    return jsonify({'message': 'You dont author'})
@app.route('/api/albums/<user_id>/<album_id>', methods=['DELETE'])
def delete_album(user_id, album_id):
    connectupdate()
    if int(user_id) == cursor_user.execute(f"SELECT userid FROM album WHERE mainid='{album_id}'").fetchone()[0]:
        albums = json.loads(cursor_user.execute(f"SELECT albumcol FROM users WHERE id={user_id}").fetchone()[0])
        albums.remove(int(album_id))
        maximgid=cursor_album.execute(f"SELECT max(id) FROM _{album_id}").fetchone()[0]
        for num in range(1, maximgid+1):
            patch = cursor_album.execute(f"SELECT patch FROM _{album_id} WHERE id = '{num}'").fetchone()[0]
            if patch is not None:
                os.remove(f"{patch}")
        os.rmdir(f'static/data/img/{album_id}')
        cursor_user.execute(f"UPDATE users SET albumcol = '{albums}' WHERE id={user_id}")
        connect_user.commit()
        cursor_album.execute(f'''DROP TABLE IF EXISTS _{album_id};''')
        connect_album.commit()
        return jsonify({'message': 'Album deleted successfully'})
    return jsonify({'message': 'You dont author'})


@app.route('/api/upload/<user_id>/<album_id>', methods=['POST'])
def upload_photo(user_id, album_id):
    connectupdate()
    if 'image' in request.files:
        image = request.files['image']
        
        cursor_album.execute(f"INSERT INTO '_{album_id}' VALUES('{1+int(cursor_album.execute(f"SELECT max(id) FROM '_{album_id}'").fetchone()[0])}', 'static/data/img/{album_id}/{image.filename}', '{request.form.get('name')}', '{request.form.get('tags')}')")
        connect_album.commit()
        image.save(f'static/data/img/{album_id}/' + image.filename)
        return 'Image uploaded successfully!'

    
    return jsonify({'message': 'Photo uploaded successfully'})
@app.route('/view/<user_id>/album/static/data/img/<album_id>/<image_name>')
def view_image(user_id, album_id, image_name):
    return send_from_directory(f'static/data/img/{album_id}', image_name)
@app.route('/myalbum')
def myalbum():
    connectupdate()
    if request.cookies.get('token') is None: 
        return redirect(url_for('login'))
    uid = cursor_user.execute(f"SELECT id FROM users WHERE token='{request.cookies.get('token')}'").fetchone()[0]
    return redirect(url_for('view_profile', user_id=uid))

@app.route('/create_album', methods=['POST'])
def create_album():
    connectupdate()
    if request.cookies.get('token') is None: 
        return redirect(url_for('login'))
    data = request.json
    token = request.cookies.get('token')
    if token:
        album_name = data.get('name')
        album_vision = data.get('alov')
        access = data.get('access')
        maxalbum=1+int(cursor_user.execute("SELECT max(mainid) FROM album").fetchone()[0])
        os.mkdir(os.path.join("static/data/img", f'{maxalbum}'))
        if access is None:
            access = 'null'
        else:
            access=json.dumps([access])
        cursor_user.execute(f"INSERT INTO album VALUES('{cursor_user.execute(f"SELECT id FROM users WHERE token='{token}'").fetchone()[0]}', '{maxalbum}', {album_vision}, '{access}', '{album_name}')")
        album_count = eval(cursor_user.execute(f"SELECT albumcol FROM users WHERE token='{token}'").fetchone()[0])
        cursor_album.execute(f'''CREATE TABLE IF NOT EXISTS _{maxalbum}(
            id INT,
            patch TEXT,
            name TEXT,
            tags TEXT
            )''')
        cursor_album.execute(f"INSERT INTO _{maxalbum} VALUES(0, 0, 0, 0)")
        connect_album.commit()

        max_album_id = maxalbum
        album_count.append(max_album_id)
        cursor_user.execute(f"UPDATE users SET albumcol='{album_count}' WHERE token='{token}'")
        connect_user.commit()
        return jsonify({'message': 'Альбом успешно создан'})
    else:
        return redirect(url_for('/account'))
@app.route('/', methods=['GET'])
def main():
    return render_template('main.html')

@app.route('/api/photos/<int:user_id>/<int:album_id>/<int:photo_id>', methods=['DELETE'])
def delete_photo(user_id, album_id, photo_id):
    connectupdate()
    if request.cookies.get('token') is None: 
        return redirect(url_for('login'))
    data = cursor_user.execute(f"SELECT id FROM users WHERE token = '{request.cookies.get('token')}'").fetchone()[0]
    if data is None:
        response = make_response(redirect(url_for('account')))
        response.set_cookie('token', '', expires=0)
        return response
    if str(user_id) == str(data):
        os.remove(f'{cursor_album.execute(f"SELECT patch FROM '_{album_id}' WHERE id = {photo_id}").fetchone()[0]}')
        cursor_album.execute(f"DELETE FROM '_{album_id}' WHERE id={photo_id}")
        connect_album.commit()
        return jsonify({'message': f'Photo with id {photo_id} deleted successfully'}), 200
@app.route('/alluser', methods=['GET'])
def allusers():
    return render_template('alluser.html')

@app.route('/api/userlist', methods=['GET'])
def alluser():
    connectupdate()
    userlist=[]
    for num in range(1, cursor_user.execute("SELECT max(id) FROM users").fetchone()[0]+1):
        if cursor_user.execute(f"SELECT id FROM users WHERE id={num}").fetchone()[0] is not None:
            name=str(cursor_user.execute(f"SELECT name FROM users WHERE id={num}").fetchone()[0])
            userlist.append({'id': num, 'name': name})
    return jsonify(userlist)

if __name__ == '__main__':
    app.run(debug=True)