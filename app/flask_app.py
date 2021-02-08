
__author__ = "Ethan Mendes"
__credits__ = ["Ethan Mendes", "Jerry Xu", "Matthew Ding", "Jason Liang", "David Towers"]
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Ethan Mendes"
__email__ = "eamendes88@gmail.com"
__status__ = "Prototype"

import time
import tomtomSearch
from flask import Flask, render_template, request, redirect, flash, session, jsonify, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, IntegerField, SelectField, RadioField
from wtforms.validators import DataRequired
from datetime import datetime
from flaskext.mysql import MySQL


# declaring app name
app = Flask(__name__)
app.config['SECRET_KEY'] = 'WAcodevid2020'

mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'WestfordCodevid1'
app.config['MYSQL_DATABASE_PASSWORD'] = 'WAcodevid2020'
app.config['MYSQL_DATABASE_DB'] = 'WestfordCodevid1$codevid'
app.config['MYSQL_DATABASE_HOST'] = 'WestfordCodevid123.mysql.pythonanywhere-services.com'
mysql.init_app(app)


class LocationForm(FlaskForm):
    """ Form class to manage location information

    This class manages the form on the homepage, which allows a user to enter in their address and preferred item
    """
    address = StringField('Address', validators=[DataRequired()])
    item_option = SelectField('item_option', choices=[('1', 'Toilet Paper'), ('2', 'Hand Sanitizer')])
    submit = SubmitField('Enter')

class StatusForm(FlaskForm):
    """ Form class to manage user status updates

    This class manages the form on the status update page, which allows a user to enter the item and its current status
    """
    status_option = SelectField('status_option',
                                choices=[('1', 'Full Stock'), ('2', 'Majority Remaining'), ('3', 'Half Remaining'),
                                         ('4', 'Few Remaining'), ('5', 'None Remaining')])
    item_option = SelectField('item_option', choices=[('1', 'Toilet Paper'), ('2', 'Hand Sanitizer')])
    submit = SubmitField('Enter')


class StoreForm(FlaskForm):
    """ Form class to manage user store selection

    This class manages the form on the homepage, which allows a user to select a certain store from a list
    """
    stores = RadioField('stores', choices=[])
    submit = SubmitField('View')


def getStore(latitude, longitude): # get stores from coordinates
    """ This method pulls the information from the nearest stores in the MySQL database

    :param latitude: user's latitude GPS coordinate
    :param longitude: user's longitude GPS coordinate
    :return: list of store names, ids, and addresses
    """
    db = mysql.connect()
    cursor = db.cursor()
    store = []
    ids = []
    addresses = []
    for i in range(len(latitude)):

        query = 'SELECT name FROM all_stores WHERE lat = ' + str(latitude[i]) + ' AND lon = ' + str(
            longitude[i]) + ';'

        cursor.execute(query)
        data_store = cursor.fetchall()

        query = 'SELECT id FROM all_stores WHERE lat = ' + str(latitude[i]) + ' AND lon = ' + str(
            longitude[i]) + ';'

        cursor.execute(query)
        data_id = cursor.fetchall()

        query = 'SELECT freeFormAddress FROM all_stores WHERE lat = ' + str(latitude[i]) + ' AND lon = ' + str(
            longitude[i]) + ';'

        cursor.execute(query)
        data_address = cursor.fetchall()

        if (len(data_store) != 0):
            store.append(data_store[0][0])
            ids.append(data_id[0][0])
            addresses.append((data_address[0][0]))
    cursor.close()
    db.close()
    return store, ids, addresses


def getItemStatus(selected_item, store_id, num_to_average):
    """ Method pulls the stock status of the selected item in the given store

    :param selected_item: current item being processed (toilet paper or hand sanitizer)
    :param store_id: id of the current store
    :param num_to_average: number of recent status updates to include in the cumulative moving average status update
    :return: returns the status of the item (integer between 1-5)
    """
    db = mysql.connect()
    cursor = db.cursor()
    query = "SELECT rating FROM status_list WHERE id = '" + str(store_id) + "' AND item = " + str(selected_item) +";"
    cursor.execute(query)
    status_values = []
    status = cursor.fetchall()

    moving_average = 0
    for i in range(len(status)):
        status_values.append(5-(status[i][0])+1)

    if len(status_values) != 0:
        for i in range(min(len(status_values),num_to_average)):
            moving_average += status_values[i]

        moving_average = moving_average/min(num_to_average, len(status_values))
    cursor.close()
    db.close()
    return round(moving_average)



def parseMessage(store, raw_item, status_data):
    """ Method parses and forms status statments

    :param store: list of store name
    :param raw_item: list of item selection (0 or 1 for toilet paper or handsanitizer)
    :param status_data: contains the raw values of the rating, date, and username for a particular status message
    :return: list of formed messages, list of the color of status updates, list of item types
    """
    messages = []
    type = []
    rating_choices = ['Full Stock', 'Majority Remaining', 'Half Remaining', 'Few Remaining', 'None Remaining']
    item_choices = ['Toilet Paper', 'Hand Sanitizer']
    color_array = []

    raw_rating = status_data[0]
    raw_date = status_data[1]
    raw_user = status_data[2]

    for x in range(len(raw_rating)):
        i = len(raw_rating) - x - 1
        if raw_user[i][0] == None:
            new_message = '' + raw_date[i][0] + ' Status of ' + item_choices[
                raw_item - 1] + ' at ' + store + ': ' + rating_choices[int(raw_rating[i][0]) - 1]
        else:
            new_message = '' + raw_date[i][0] + ' Status of ' + item_choices[raw_item - 1] + ' at ' + store + ': ' + rating_choices[int(raw_rating[i][0]) - 1] + " - " + raw_user[i][0]
        messages.append(new_message)
        color_array.append(int(raw_rating[i][0]))
        type.append(int(raw_item))
    return messages, color_array, type


def getAddress(address):
    """ Method returns the formed address

    :param address: raw address
    :return: formed address
    """
    message = 'Address: ' + address
    return message

def getPhone(phone):
    """ Method returns formed phone information

    :param phone: raw phone number
    :return: formed phone number
    """
    message = 'Phone:' + phone
    return message

def getItem(key):
    """ Method returns formed item from key

    :param key: 0 or 1 corresponding to the desired item
    :return: string containing item name
    """
    items = {'1': 'Toilet Paper', '2': 'Hand Sanitizer'}
    return items[key]


@app.route('/location', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def location():
    """ Method manages the homepage of the UI including user interactions

    :return: rendered HTML template of the location form
    """

    form = LocationForm()

    if form.validate_on_submit():

        flash('Item requested from the user {}'.format(form.item_option.data))
        flash('Item requested from the user {}'.format(form.address.data))
        session['selected_item'] = form.item_option.data
        user_lat, user_lon = tomtomSearch.geo(form.address.data)
        lat_lst, lon_lst = tomtomSearch.search(user_lat, user_lon)
        stores, ids, addresses = getStore(lat_lst, lon_lst)
        session['stores'] = []
        session['ids'] = []
        session['addresses'] = []

        session['stores'] = stores
        session['ids'] = ids
        session['addresses'] = addresses

        return redirect('/store')

    return render_template('location.html', title='Location', form = form)


@app.route('/store', methods=['GET', 'POST'])
def stores():
    """ Method manages the store listing page of the UI including user interactions

    :return: rendered HTML template of the store listing form
    """

    form = StoreForm()
    if request.method == 'POST':
        option =  int(request.form['options'])
        session['selected_store'] = session.get('stores')[option]
        session['selected_id'] = session.get('ids')[option]
        return redirect('/item-status')

    status_values = []
    radio = {}
    for i in range(len(session.get('stores'))):
        form.stores.choices.append((str(i), (session.get('stores')[i] + ' - ' + session.get('addresses')[i])))
        radio[i] = str(session.get('stores')[i] + ' - ' + session.get('addresses')[i])
        status_values.append(getItemStatus(session.get('selected_item'), session.get('ids')[i], 5))

    return render_template("store.html", len=len(form.stores.choices), form=form, status_values=status_values, radio = radio, selected_item_index = int(session.get('selected_item')), selected_item_name = getItem(session.get('selected_item')))



@app.route('/item-status', methods=['GET', 'POST'])
def status():
    """ Method manages the status page of the UI including user interactions

    :return: rendered HTML template of status form and status listing
    """
    status_form = StatusForm()


    if request.method == 'POST':
        db = mysql.connect()
        cursor = db.cursor()

        user_email = session.get('user')['user_email']
        flash('Status requested from the user {}'.format(status_form.status_option.data))
        now = datetime.now()
        date_now = now.strftime("%m/%d/%Y %H:%M:%S")

        query = "INSERT INTO status_list(date, item, rating, manager, store, id, user) VALUES('" + date_now + "',"\
                + session.get('selected_item') + "," + status_form.status_option.data + ", 0, '" \
                + session['selected_store'] + "', '" + session['selected_id'] + "','"+ user_email+"');"
        cursor.execute(query)
        cursor.execute("COMMIT;")
        time.sleep(0.5)

        cursor.close()
        db.close()
        return redirect('/item-status')

    status_data_type = ['rating', 'date', 'user']
    store_data_type = ['phone', 'freeFormAddress']
    status_data = []
    store_data = []

    db = mysql.connect()
    cursor = db.cursor()

    # query status message data
    for type_query in status_data_type:
        get_query = "SELECT " + type_query  + " FROM status_list WHERE item = " + session.get('selected_item') + \
                    " AND id = '" + session['selected_id'] + "';"
        cursor.execute(get_query)
        status_data.append(cursor.fetchall())

    # query store data
    for type_query in store_data_type:
        get_query = "SELECT " + type_query + "FROM all_stores WHERE id = '" + session['selected_id'] + "';"
        cursor.execute(get_query)
        store_data.append(cursor.fetchall())

    messages, colors, type_item = parseMessage(session['selected_store'], int(session.get('selected_item')), status_data)

    basic_info = []
    basic_info.append(getPhone(status_data[0][0][0]))
    basic_info.append(store_data[1][0][0])

    cursor.close()
    db.close()

    # render template based on login
    if session.get('user')['user_email'] == '':
        return render_template("status.html", signIn=0, store=session['selected_store'], form=status_form,
                               messages=messages, len=len(messages), colors=colors, type_item=type_item,
                               basic_info=basic_info, selected_item=getItem(session.get('selected_item')))
    else:
        return render_template("status.html", signIn = 1, store=session['selected_store'], form=status_form,
                               messages=messages, len=len(messages), colors=colors, type_item=type_item,
                               basic_info=basic_info, selected_item = getItem(session.get('selected_item')))

if __name__ == '__main__':
    app.run(use_reloader=True, debug=True)

