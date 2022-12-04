import os
import hashlib
import base64

from flask import Flask, render_template, request, session, url_for, redirect, flash
from werkzeug.utils import secure_filename
import pymysql.cursors

# for uploading photo:
from app import app

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False

def allowed_image_filesize(filesize):
    if int(filesize) <= app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False


###Initialize the app from Flask
app = Flask(__name__)
# app.secret_key = "secret key"

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=3306, #port=8889,
                       user='diana', #user='jessie',
                       password='cookzilla6083',
                       db='cookzilla',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(),'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/upload', methods=['GET'])
def upload_form():
    if request.method=='GET':
        return render_template('upload.html')

@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    url = None
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('upload_form'))
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(url_for('upload_form'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_url)
            flash('File successfully uploaded')
            return redirect(url_for('upload_form'))
        else:
            flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
            return redirect(url_for('upload_form'))


def passwordHash(password):
    # SHA-256 password hashing
    salt = '5gz4'
    db_password = password + salt
    h = hashlib.sha256(db_password.encode())
    b64_bytes = base64.b64encode(h.digest())
    hash_password = b64_bytes.decode('ascii')
    return hash_password

# Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')


# Define route for login
@app.route('/login')
def login():
    return render_template('login.html')


# Define route for register
@app.route('/register')
def register():
    return render_template('register.html')


# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    # SHA-256 password hashing
    hash_password = passwordHash(password)

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hash_password))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if (data):
        # creates a session for the user
        # session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        # returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)


# Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    profile = request.form['profile']

    # SHA-256 password hashing
    hash_password = passwordHash(password)

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # If the previous query returns data, then user exists
        error = "This user already exists. Please login"
        return render_template('login.html', error=error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hash_password, fname, lname, email, profile))
        conn.commit()
        cursor.close()
        return redirect(url_for('login'))

@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT DISTINCT profile, gName, title ' \
            'FROM Person NATURAL JOIN GroupMembership NATURAL JOIN Recipe ' \
            ' WHERE username = %s AND memberName = %s AND postedBy = %s'
    cursor.execute(query, (user, user, user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, posts=data)


#recipes search
@app.route('/recipes_search')
def recipesSearch():
    return render_template('recipes_search.html')

@app.route('/recipes_search', methods=["GET"])
def recipesSearchResults():
    tag = request.args['tag']
    stars = request.args['stars']
    searchType = request.args['searchType']
    cursor = conn.cursor();
    if searchType == 'tag':
        # query recipes with chosen tag value
        query = 'SELECT recipeID, title FROM Recipe NATURAL JOIN RecipeTag WHERE tagText = %(tag)s'
        cursor.execute(query)
        data = cursor.fetchall()
    elif searchType == 'stars':
        # query recipes with chosen star rating
        query = 'SELECT recipeID, title FROM Recipe NATURAL JOIN Review WHERE stars = %(stars)s'
        cursor.execute(query)
        data = cursor.fetchall()
    else:
        # query both recipe tag & num stars
        query = 'SELECT recipeID, title FROM Recipe NATURAL JOIN RecipeTag NATURAL JOIN Review' \
                'WHERE tagText = %(tag)s AND stars = %(stars)s'
        cursor.execute(query)
        data = cursor.fetchall()

    cursor.close()
    return render_template('display_recipe.html', recipe=data)


''' 
REQUIRED CASE 2: search for recipe and display relevant info
'''
# initial search page
@app.route('/display_recipe')
def display_recipe():
    return render_template('display_recipe.html')

# display the recipe options based on user's search term
@app.route('/display_recipe_options')
def display_recipe_options():
    searchTerm = request.args['searchTerm']
    cursor = conn.cursor()
    query = 'SELECT DISTINCT recipeID,title FROM Recipe WHERE (recipeID LIKE %s OR title LIKE %s) ORDER BY recipeID ASC'
    args = ['%' + searchTerm + '%']
    cursor.execute(query, (args, args))
    data = cursor.fetchall()
    cursor.close()
    error = None
    if not data:
        error = "There are no recipes matching your search, try again."
        return render_template('display_recipe.html', error=error)
    else:
        return render_template('display_recipe_options.html', recipes=data)

# display relevant details of the recipe after selecting an option
@app.route('/show_recipe_details', methods=["GET", "POST"])
def show_recipe_details():
    poster = request.args['recipeID']
    cursor = conn.cursor()

    query1 = 'SELECT stepNo,sDesc FROM Recipe NATURAL JOIN Step WHERE recipeID = %s ORDER BY stepNo ASC'
    cursor.execute(query1, poster)
    data1 = cursor.fetchall()

    query2 = 'SELECT * FROM Recipe WHERE recipeID = %s'
    cursor.execute(query2, poster)
    data2 = cursor.fetchall()

    query3 = 'SELECT * FROM RecipeIngredient WHERE recipeID = %s'
    cursor.execute(query3, poster)
    data3 = cursor.fetchall()

    query4 = 'SELECT * FROM Review WHERE recipeID = %s'
    cursor.execute(query4, poster)
    data4 = cursor.fetchall()

    query5 = 'SELECT recipe2 FROM RelatedRecipe WHERE recipe1 = %s'
    cursor.execute(query5, poster)
    data5 = cursor.fetchall()

    query6 = 'SELECT pictureURL FROM RecipePicture WHERE recipeID = %s'
    cursor.execute(query6, poster)
    data6 = cursor.fetchall()
    cursor.close()

    return render_template('display_recipe_details.html', recipeID=poster, posts1=data1,
                           posts2=data2, posts3=data3, posts4=data4, posts5=data5, posts6=data6)


''' 
REQUIRED CASE 4: post a recipe
'''
''' 
# initial page to post in Recipe table
@app.route('/post_recipe')
def post_recipe():
    return render_template('post_recipe.html')

# make sure Recipe post is valid
@app.route('/post_recipeAuth', methods=['GET', 'POST'])
def post_recipeAuth():
    # grabs information from the forms
    username = session['username']
    recipeID = request.form['recipeID']
    title = request.form['title']
    numServings = request.form['numServings']
    cursor = conn.cursor() # cursor used to send queries
    query = 'SELECT * FROM Recipe WHERE recipeID = %s' # executes query
    cursor.execute(query, (recipeID))
    data = cursor.fetchone()
    error = None
    if data:
        error = "This recipe ID already exists, please try another one"
        return render_template('post_recipe.html', error=error)
    else:
        ins = 'INSERT INTO Recipe (recipeID, title, numServings, postedBy) VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (recipeID, title, numServings, username))
        conn.commit()
        cursor.close()
        return render_template('home.html')
# To Do:
# add Steps
# add RecipeIngredients
# add RecipePicture (if any)
# add RecipeTag (if any)
# add RelatedRecipe (if any)
# add Restrictions (if any)
'''
'''OPTIONAL CASE 1:'''
# 7 Post an event for a group user belongs to
# check user's group and return GroupName and GroupCreator
def getGroupMembership(user):
    cursor = conn.cursor()
    query = 'SELECT gName, gCreator FROM groupMembership WHERE memberName = %s'
    cursor.execute(query, (user))
    data = cursor.fetchall()
    cursor.close
    return data
@app.route('/post_event')
def postEventPage():
    # function only available if logged in.
    # need to check if user is logged in
    user = None
    if session.get('username'):
        user = session['username']
    else:
        return redirect(url_for('login'))
    groups = getGroupMembership(user)
    return render_template('post_event.html', username=user, groups=groups)

@app.route('/post_event', methods=['GET', 'POST'])
def postEvent():
    user = session['username']
    finalPath = []
    # check if pictures
    if request.method == 'POST':
        # get information
        eName = request.form['eName']
        eDesc = request.form['eDesc']
        if eDesc == "":
            eDesc = None
        eDate = request.form['eDate']
        gName = request.form['gName']
        gCreator = request.form['gCreator']
        eventPicture = request.files.getlist('pictures')

        # check if the user is member of group for event
        cursor = conn.cursor()
        grp_query = 'SELECT * FROM groupMembership WHERE memberName = %s AND gName = %s AND gCreator = %s'
        cursor.execute(grp_query, (user, gName, gCreator))
        grp_query = cursor.fetchall()
        data = grp_query[0]

        #if user in data:
        if user in data.values():
            ins = 'INSERT INTO event (eName, eDesc, eDate, gName, gCreator) VALUES(%s, %s, %s, %s, %s)'
            cursor.execute(ins, (eName, eDesc, eDate, gName, gCreator))
            eID = cursor.lastrowid

            # if pictures, add pictures
            for file in eventPicture:
                if request.method == 'POST':
                    # check if the post request has the file part
                    if 'file' not in request.files:
                        flash('No file part')
                    if file.filename == '':
                        flash('No file selected for uploading')
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_url)
                        flash('File successfully uploaded')
                        query = 'INSERT INTO eventPicture (eID, pictureURL) VALUES (%s, %s)'
                        cursor.execute(query, (eID, str(file_url)))
                    else:
                        flash('Allowed file types are png, jpg, jpeg, gif')
            conn.commit()
            cursor.close()
            message = "Confirmation of your event addition! Here is your eventID number: " + str(eID)
            return render_template('post_event.html', username=user, groups=data, message=message)

        #if not in group
        else:
            error = 'You must be a member of the group to post an event for it.'
            conn.commit()
            cursor.close()
            return redirect(url_for('post_event'), error=error)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5001
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5001, debug=True)