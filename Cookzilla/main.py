# Import Flask Library
import os
import hashlib
import base64

from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors

# for uploading photo:
from app import app
# from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

###Initialize the app from Flask
app = Flask(__name__)
# app.secret_key = "secret key"

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=8889, #port=3306,
                       user='jessie', #user='diana',
                       password='cookzilla6083',
                       db='cookzilla',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


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
        return render_template('login.html')


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
    elif searchType == 'stars':
        # query recipes with chosen star rating
        query = 'SELECT recipeID, title FROM Recipe NATURAL JOIN Review WHERE stars = %(stars)s'
        cursor.execute(query)
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
# initial page to post in Recipe table
@app.route('/post_recipe')
def post_recipe():
    return render_template('post_recipe.html')

# make sure Recipe post is valid
@app.route('/post_recipeAuth', methods=['GET', 'POST'])
def post_recipeAuth():
    username = session['username']
    title = request.form['title']
    numServings = request.form['numServings']
    cursor = conn.cursor() # cursor used to send queries
    ins = 'INSERT INTO Recipe (title, numServings, postedBy) VALUES(%s, %s, %s)'
    cursor.execute(ins, (title, numServings, username))
    recipeID = cursor.lastrowid
    conn.commit()
    cursor.close()
    return render_template('post_recipe_more.html', recipeID=recipeID, stepNo=1)

@app.route('/post_recipe_details', methods=['GET', 'POST'])
def post_recipe_details():
    rID = request.args['recipeID']
    tagText = request.args['tagText']
    related = request.args['recipe2']
    pic = request.args['pictureURL']
    iName = request.args['iName']
    unitName= request.args['unitName']
    amount = request.args['amount']
    stepNo = request.args['stepNo']
    sDesc = request.args['sDesc']

    cursor = conn.cursor()

    if tagText:
        ins = 'INSERT INTO RecipeTag (recipeID, tagText) VALUES(%s,%s)'
        cursor.execute(ins, (rID, tagText))
        conn.commit()
    if related:
        ins = 'INSERT INTO RelatedRecipe (recipe1, recipe2) VALUES(%s,%s)'
        cursor.execute(ins, (rID, related))
        ins = 'INSERT INTO RelatedRecipe (recipe1, recipe2) VALUES(%s,%s)'
        cursor.execute(ins, (related, rID))
        conn.commit()
    if pic:
        ins = 'INSERT INTO RecipePicture (recipeID, pictureURL) VALUES(%s,%s)'
        cursor.execute(ins, (rID, pic))
        conn.commit()
    if (iName and unitName and amount):
        ins = 'INSERT INTO RecipeIngredient (recipeID, iName, unitName, amount) VALUES(%s,%s,%s,%s)'
        cursor.execute(ins, (rID, iName, unitName, amount))
        conn.commit()
    if (stepNo and sDesc):
        ins = 'INSERT INTO Step (stepNo, recipeID, sDesc) VALUES(%s,%s,%s)'
        cursor.execute(ins, (stepNo, rID, sDesc))
        stepNo = int(stepNo) + 1
        conn.commit()

    cursor.close()

    addMore = request.args['addMore']
    if addMore == 'yes':
        return render_template('post_recipe_more.html', recipeID=rID, stepNo=stepNo)

    return render_template('home.html')



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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