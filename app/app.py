# importing modules
import time

import sshtunnel as sshtunnel

import tomtomSearch
from flask_bootstrap import Bootstrap
from geopy.geocoders import GoogleV3
from flask import Flask, render_template, request, redirect, flash, session, jsonify, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, IntegerField, SelectField, RadioField
from wtforms.validators import DataRequired
import mysql.connector as mysql
from datetime import datetime
from pytz import timezone


'''
TODO:
-add so user can input address as well
- fix the full page 2 columns
- add information about the store
- integrate the user
- authenticate the managers
'''


class LocationForm(FlaskForm):
    address = StringField('Address', validators=[DataRequired()])
    item_option = SelectField('item_option', choices=[('1', 'Toilet Paper'), ('2', 'Hand Sanitizer')])
    distance_option = SelectField('distance_option',
                                choices=[('1', '1 km'), ('5', '5 km'), ('10', '10 km'),
                                         ('15', '15 km'), ('20', '20 km')])
    submit = SubmitField('Search')

class StatusForm(FlaskForm):
    status_option = SelectField('status_option',
                                choices=[('1', 'Full Stock'), ('2', 'Majority Remaining'), ('3', 'Half Remaining'),
                                         ('4', 'Few Remaining'), ('5', 'None Remaining')])
    item_option = SelectField('item_option', choices=[('1', 'Toilet Paper'), ('2', 'Hand Sanitizer')])
    submit = SubmitField('Submit Status')





class StoreForm(FlaskForm):
    stores = RadioField('stores', choices=[])
    submit = SubmitField('View')

class optionForm(FlaskForm):
    find_item = SubmitField('Find an Item')
    provide_status = SubmitField('Provide Status')


db = mysql.connect(
    host="localhost",
    user="root",
    passwd="$Soccer2001%",
    database="servers"
)




# declaring app name
app = Flask(__name__)
#Bootstrap(app)
app.config['SECRET_KEY'] = 'WAcodevid2020'


def getStore(latitude, longitude): # get stores from coordinates
    cursor = db.cursor()
    # SELECT school, student FROM table1 LIMIT 1;
    store = []
    ids = []
    addresses = []
    for i in range(len(latitude)):

        query = 'SELECT name FROM all_stores WHERE lat = ' + str(latitude[i]) + ' AND lon = ' + str(longitude[i]) + ';'

        cursor.execute(query)
        data_store = cursor.fetchall()

        query = 'SELECT id FROM all_stores WHERE lat = ' + str(latitude[i]) + ' AND lon = ' + str(longitude[i]) + ';'

        cursor.execute(query)
        data_id = cursor.fetchall()

        query = 'SELECT freeFormAddress FROM all_stores WHERE lat = ' + str(latitude[i]) + ' AND lon = ' + str(
            longitude[i]) + ';'

        cursor.execute(query)
        data_address = cursor.fetchall()

        # rcount = len(data)

        # print(rcount)
        if (len(data_store) != 0):
            store.append(data_store[0][0])
            ids.append(data_id[0][0])
            addresses.append((data_address[0][0]))

    return store, ids, addresses


def getItemStatus(selected_item, store_id, num_to_average): #get the status of the selected item using moving average
    cursor = db.cursor()
    query = "SELECT rating FROM status_list WHERE id = '" + str(store_id) + "' AND item = " + str(selected_item) +";"
    cursor.execute(query)
    status_values = []
    status = cursor.fetchall()


    moving_average = 0
    for x in range(len(status)):
        i = len(status) - x - 1
        status_values.append(5-(status[i][0])+1)

    if len(status_values) != 0:
        for i in range(min(len(status_values),num_to_average)):
            moving_average += status_values[i]

        moving_average = moving_average/min(num_to_average, len(status_values))
    return round(moving_average)


def getManagerList(raw_manager):
    manager_lst = []
    for x in range(len(raw_manager)):
        i = len(raw_manager) - x - 1
        manager_lst.append(raw_manager[i][0])
    return manager_lst

def parseMessage(store, raw_item, raw_rating, raw_date, raw_user): # get status messages

    messages = []
    type = []
    rating_choices = ['Full Stock', 'Majority Remaining', 'Half Remaining', 'Few Remaining', 'None Remaining']
    item_choices = ['Toilet Paper', 'Hand Sanitizer']

    color_array = []
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


def getAddress(address): # get basic store information for landing page
    message = 'Address: ' + address
    return message

def getPhone(phone):
    phone_formatted = ''
    if len(phone)>0:
        phone_formatted = phone[5:14] + '-' + phone[14:18]
    else:
        phone_formatted = 'Unavailable'
    message = 'Phone: ' + phone_formatted
    return message
def getItem(key):
    items = {'1': 'Toilet Paper', '2': 'Hand Sanitizer'}
    return items[key]

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        session['user'] = data['user_email']
        session['user_store_id'] = data['store_id']

    return "Forbidden!"

@app.route('/location', methods=['GET', 'POST'])
def location():

    cursor = db.cursor()
    form = LocationForm()

    if form.validate_on_submit():
        flash('Item requested from the user {}'.format(form.item_option.data))
        flash('Item requested from the user {}'.format(form.distance_option.data))
        flash('Item requested from the user {}'.format(form.address.data))
        session['selected_item'] = form.item_option.data
        session['distance'] = form.distance_option.data
        user_lat, user_lon = tomtomSearch.geo(form.address.data)
        lat_lst, lon_lst = tomtomSearch.search(user_lat, user_lon,1000*int(session.get('distance')),10*int(session.get('distance')))
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
    cursor = db.cursor()

    form = StoreForm()
    if request.method == 'POST':

        #flash('Status requested from the user {}'.format(form.stores.data))
        option =  int(request.form['options'])
        session['selected_store'] = session.get('stores')[option]


        session['selected_id'] = session.get('ids')[option]

        return redirect('/item-status')
    status_values = []

    radio = {}
    all_stores = []
    store_info = {}
    store_count = []
    for i in range(len(session.get('stores'))): # append radio button options
        cur_status = getItemStatus(session.get('selected_item'), session.get('ids')[i], 1)
        if session.get('selected_option') == 'find' and cur_status==0:
            continue
        else:
            #form.stores.choices.append((str(i), (session.get('stores')[i] + ' - ' + session.get('addresses')[i])))
            all_stores.append((session.get('stores')[i] + ' - ' + session.get('addresses')[i]))
            store_info[i] =[session.get('stores')[i],session.get('ids')[i],session.get('addresses')[i]]
            #radio[i] = str(session.get('stores')[i] + ' - ' + session.get('addresses')[i])
            store_count.append(i)
            status_values.append(cur_status)

    #form.stores.choices = [x for _, x in sorted(zip(status_values, form.stores.choices), reverse=True)]

    all_stores = [x for _, x in sorted(zip(status_values, all_stores), reverse=True)]
    store_count = [x for _, x in sorted(zip(status_values, store_count), reverse=True)]
    sorted_info = []
    for i in range(len(store_count)):
        sorted_info.append(store_info[store_count[i]])

    session['stores'] = [item[0] for item in sorted_info]
    session['ids'] = [item[1] for item in sorted_info]
    session['addresses'] = [item[2] for item in sorted_info]

    '''
    session['stores'] = [x for _, x in sorted(zip(status_values, only_stores), reverse=True)]
    session['ids'] = [x for _, x in sorted(zip(status_values, only_ids), reverse=True)]
    session['addresses'] = [x for _, x in sorted(zip(status_values, only_addresses), reverse=True)]
'''
    status_values.sort(reverse=True)
    for i in range(len(status_values)):
        s = str(session.get('stores')[i] + ' - ' + session.get('addresses')[i])
        radio[i] = s
        form.stores.choices.append((str(i), s))

    storeFound = True
    if len(status_values) == 0:
        storeFound = False
    print(status_values)
    status_types = ['Full Stock', 'Majority Remaining', 'Half Remaining','Few Remaining', 'None Remaining']
    return render_template("store.html", type_query = session.get('selected_option'),storeFound = storeFound,status_types=status_types, dist = int(session.get('distance')),len=len(form.stores.choices), form=form, status_values=status_values, radio = radio, selected_item_index = int(session.get('selected_item')), selected_item_name = getItem(session.get('selected_item')))



@app.route('/item-status', methods=['GET', 'POST'])
def status():

    status_form = StatusForm()
    cursor = db.cursor()

    if request.method == 'POST':
        user_email = ' '
        print()
        if session.get('user') == '':
            print("hello")
            return redirect("/item-status")
        user_email = session.get('user')
        flash('Status requested from the user {}'.format(status_form.status_option.data))
        #flash('Status requested from the user {}'.format(status_form.item_option.data))
        tz = timezone('US/Eastern')
        now = datetime.now(tz)
        date_now = now.strftime("%m/%d/%Y %H:%M:%S")
        # add manager
        query = ''
        if session.get('user_store_id') == session.get('selected_id'):
            query = "INSERT INTO status_list(date, item, rating, manager, store, id, user) VALUES('" + date_now + "'," + session.get('selected_item') + "," + status_form.status_option.data + ", 1, '" + session['selected_store'] + "', '" + session['selected_id'] + "','"+ user_email+"');"
        else:
            query = "INSERT INTO status_list(date, item, rating, manager, store, id, user) VALUES('" + date_now + "'," + session.get('selected_item') + "," + status_form.status_option.data + ", 0, '" + session['selected_store'] + "', '" + session['selected_id'] + "','"+ user_email+"');"
        cursor.execute(query)
        cursor.execute("COMMIT;")
        time.sleep(0.5)

        return redirect('/item-status')



    get_query = "SELECT rating FROM status_list WHERE item = " + session.get('selected_item') +" AND id = '" + session['selected_id']  + "';"

    cursor.execute(get_query)
    raw_rating = cursor.fetchall()

    get_query = "SELECT date FROM status_list WHERE item = " + session.get('selected_item') +" AND id = '" + session['selected_id']  + "';"
    cursor.execute(get_query)
    raw_date = cursor.fetchall()

    get_query = "SELECT user FROM status_list WHERE item = " + session.get('selected_item') +" AND id = '" + session['selected_id']  + "';"
    cursor.execute(get_query)
    raw_user = cursor.fetchall()

    get_query = "SELECT manager FROM status_list WHERE item = " + session.get('selected_item') +" AND id = '" + session['selected_id']  + "';"
    cursor.execute(get_query)
    raw_manager = cursor.fetchall()

    # get basic store info

    get_query = "SELECT phone FROM all_stores WHERE id = '" + session['selected_id']  + "';"
    cursor.execute(get_query)
    raw_phone = cursor.fetchall()

    get_query = "SELECT freeFormAddress FROM all_stores WHERE id = '" + session['selected_id']  + "';"
    cursor.execute(get_query)
    raw_address = cursor.fetchall()

    messages, colors, type_item = parseMessage(session['selected_store'], int(session.get('selected_item')), raw_rating, raw_date, raw_user)
    managers = getManagerList(raw_manager)
    basic_info = []
    basic_info.append(getAddress(raw_address[0][0]))
    basic_info.append(getPhone(raw_phone[0][0]))

    #user_email = request.get_json()
    if session.get('user') == '':
        return render_template("status.html", managers = managers,type_query = session.get('selected_option'),signIn=0, store=session['selected_store'], form=status_form,
                               messages=messages,
                               len=len(messages), colors=colors, type_item=type_item, basic_info=basic_info,
                               selected_item=getItem(session.get('selected_item')))
    else:
        return render_template("status.html", managers = managers, type_query = session.get('selected_option'), signIn = 1, store=session['selected_store'], form=status_form, messages=messages,
                               len=len(messages), colors=colors, type_item=type_item, basic_info=basic_info, selected_item = getItem(session.get('selected_item')))


@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def homepage():
    session['stores'] = []
    session['ids'] = []
    session['addresses'] = []
    session['has_enabled'] = 'disabled'
    session['distance'] = 10000

    form = optionForm()

    if form.validate_on_submit():
        if form.find_item.data:
            session['selected_option'] = 'find'
            return redirect('/location')
        elif form.provide_status.data:
            session['selected_option'] = 'status'
            return redirect('/location')


    return render_template("index.html", form = form)


if __name__ == '__main__':
    app.run(use_reloader=True, debug=True)
    print("hello")
