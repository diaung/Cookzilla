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
        return redirect(url_for('home'))

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
    #search only the tags available in database
    cursor = conn.cursor()
    tag_query = 'SELECT DISTINCT tagText FROM RecipeTag'
    cursor.execute(tag_query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('recipes_search.html', tags=data)

''' 
REQUIRED CASE 2: search for recipe and display relevant info
'''
# display the recipe options based on user's search term
@app.route('/display_recipe_options', methods=["GET"])
def display_recipe_options():
    tag = request.args['tag']
    stars = request.args['stars']
    searchType = request.args['searchType']
    print(searchType)
    cursor = conn.cursor();
    if searchType == 'tag':
        # query recipes with chosen tag value available from database
        query = 'SELECT recipeID, title FROM Recipe NATURAL JOIN RecipeTag WHERE tagText = %s'
        cursor.execute(query, tag)
        data = cursor.fetchall()
    elif searchType == 'stars':
        # query recipes with chosen star rating
        query = 'SELECT DISTINCT recipeID, title FROM Recipe NATURAL JOIN Review WHERE stars = %s'
        cursor.execute(query, stars)
        data = cursor.fetchall()
    else:
        # query both recipe tag & num stars
        query = 'SELECT recipeID, title FROM Recipe NATURAL JOIN RecipeTag NATURAL JOIN Review WHERE tagText = %s AND stars = %s'
        cursor.execute(query,(tag, stars))
        data = cursor.fetchall()
    cursor.close()
    error = None
    if not data:
        error = "There are no recipes matching your search, try again."
        return render_template('recipes_search.html', error=error)
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

''' 
OPTIONAL CASE 3: post a review
'''
@app.route('/post_review')
def postPage():
    # function only available if logged in - need to check if user is logged in
    if session.get('username'):
        user = session['username']
    else:
        return redirect(url_for('login'))
    return render_template('post_review.html', username=user)

@app.route('/post_review', methods=['GET', 'POST'])
def postReview():
    user = session['username']
    if request.method == 'POST':
        recipeID = request.form['recipeID']
        revTitle = request.form['revTitle']
        revDesc = request.form['revDesc']
        stars = request.form['stars']
        reviewPicture = request.files.getlist('pictures')

        # check if the recipe ID is valid
        cursor = conn.cursor()
        query = 'SELECT * FROM Recipe WHERE recipeID = %s'
        cursor.execute(query, (recipeID))
        query = cursor.fetchall()
        data = query

        if data:
            ins = 'INSERT INTO Review (userName, recipeID, revTitle, revDesc, stars) VALUES(%s, %s, %s, %s, %s)'
            cursor.execute(ins, (user, recipeID, revTitle, revDesc, stars))

            # if pictures, add pictures
            for file in reviewPicture:
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
                        query = 'INSERT INTO ReviewPicture (userName, recipeID, pictureURL) VALUES (%s, %s, %s)'
                        cursor.execute(query, (user, recipeID, str(file_url)))
                    else:
                        flash('Allowed file types are png, jpg, jpeg, gif')

            conn.commit()
            cursor.close()
            message = "Confirmation of your review post! Post another review, return home, or log out."
            return render_template('post_review.html', username=user, message=message)
        else:
            error = 'You must post a valid recipe ID.'
            conn.commit()
            cursor.close()
            return render_template('post_review.html', username=user, error=error)

''' 
OPTIONAL CASE 4: join a group
'''
@app.route('/join_group', methods=['GET', 'POST'])
def joinGroup():
    user = session['username']

    # user is not a member of these existing groups
    def not_member():
        cursor = conn.cursor()
        not_in_grp_query = 'SELECT * FROM `Group` WHERE gName NOT IN (SELECT gName from GroupMembership WHERE memberName = %s)'
        cursor.execute(not_in_grp_query,(user))
        not_in_grp_query = cursor.fetchall()
        conn.commit()
        cursor.close()
        return not_in_grp_query

    # add user to groups they are not a member of
    if request.method == 'POST':
        gName = request.form['gName']
        gCreator = request.form['gCreator']
        cursor = conn.cursor()
        ins = 'INSERT INTO GroupMembership (memberName,gName,gCreator) VALUES(%s, %s, %s)'
        cursor.execute(ins, (user,gName,gCreator))
        conn.commit()
        cursor.close()
        dataMember = getGroupMembership(user) # Diana's function
        dataNotMember = not_member()
        message = "Confirmation of your new group membership! Join another group (if available), return home, or logout"
        return render_template('join_group.html', username=user, groups=dataMember, notgroups=dataNotMember, message=message)

    else:
        dataMem = getGroupMembership(user) # user is member of these groups
        dataNotMem = not_member() # user is not a member of these groups

    return render_template('join_group.html', username=user, groups=dataMem, notgroups=dataNotMem)


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
'''
OPTIONAL CASE 2: RSVP to an Event
'''
@app.route('/show_events')
def show_eventsPage():
    # function only available if logged in.
    # need to check if user is logged in
    user = None
    if session.get('username'):
        user = session['username']
    else:
        return redirect(url_for('login'))
    groups = getGroupMembership(user)
    return render_template('show_events.html', username=user, groups=groups)

@app.route('/all_events', methods=['GET'])
def show_all_events():
    cursor = conn.cursor()
    query = 'SELECT * FROM Event'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_all_events.html', events=data)

@app.route('/show_events/<int:event_id>', methods = ['GET', 'POST'])
def show_events(event_id):
    user = session['username']

    # show events if user is member of group
    error = None
    this_event = None
    cursor = conn.cursor()
    query = 'SELECT * FROM Event WHERE eID = %s'
    cursor.execute(query, (str(event_id)))
    data = cursor.fetchall()
    cursor.close()
    if data:
        this_event = data[0]
        groupname = this_event.get('gName')
        groupcreator = this_event.get('gCreator')
        cursor = conn.cursor()
        query = 'SELECT * FROM GroupMembership WHERE memberName = %s AND gName = %s AND gCreator = %s'
        cursor.execute(query, (user,groupname,groupcreator))
        group_data = cursor.fetchall()
        cursor.close()

    if request.method == 'POST':
        cursor = conn.cursor()
        rsvp = request.form['rsvp']
        ins = 'INSERT INTO RSVP (userName, eID, response) VALUES(%s, %s, %s)'
        cursor.execute(ins, (user, event_id, rsvp))
        conn.commit()
        cursor.close()
        message = 'Congratulations! You successfully RSVP to event number ' + str(event_id)
        return render_template('show_events.html',event_id=event_id, message=message)
    else:
        #if not submitting form show events
        if group_data:
            return render_template('show_events.html', events=data)
        else:
            error = 'You are not a member of this group. Please join the group to particpate in this event'
            return redirect(url_for('joinGroup'))


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