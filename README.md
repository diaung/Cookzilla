# Cookzilla Project

main.py has all the app code, and imports app.py (which has the upload folder location)

templates folder has the html files


The Welcome page allows a user to log in, register, search for recipes, or go to a user’s home page (if they are logged in).  A user’s home page will display their profile, their member groups, and links to recipes that they have posted.  It will also allow the user to participaet in the below required and additional features.

Required use cases:
- Login
- Search for Recipes: users can search for recipes that have a particular tag and/or a given number of stars
- Display Recipe Info: given a recipeID, display relevant information about the recipe, including the description, the
steps in order, etc (recipeID is selected from a menu based on a search)
- Post a Recipe: logged in user can post a recipe and related data (steps, tags, etc)

Additional features:
- post an event for a group that user belongs to
- RSVP to an event that the user belongs to
- post a review
- join a group that the user does not belong to
  - Note an assumption is that creators of groups are not automatically included as members of the group(s) they created
