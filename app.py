from flask import Flask, render_template
from flask import request, redirect
from db_connector.db_connector import connect_to_database, execute_query
#create the web application
app = Flask(__name__)


#homepage- links to all other pages on website
@app.route('/')
def index():
    return render_template('index.html')


#counselors page
@app.route('/counselors', methods=['POST','GET'])
def browse_counselors():
    print("Fetching and rendering counselors web page")
    db_connection = connect_to_database()
    #display all counselors
    if request.method == 'GET':
        query = "SELECT `counselorID`, `first_name`, `last_name`, `name` FROM `Counselors` INNER JOIN Shelters ON Counselors.shelterID = Shelters.shelterID ORDER BY `first_name`"
        result = execute_query(db_connection, query).fetchall()
        print(result)
        #query to show dropdown shelter options in counselor form 
        query = 'SELECT shelterID, name from Shelters'
        shelters = execute_query(db_connection,query).fetchall()
        print(shelters)
        return render_template('counselors.html', rows=result, shelters=shelters)
    elif request.method == 'POST':
        #add counselor to table 
        print("Adding an counselor")
        fname = request.form['firstName'] 
        lname = request.form['lastName'] 
        shelterID = request.form['shelterID'] 
        #query to add counselor
        query = 'INSERT INTO Counselors (first_name, last_name, shelterID) VALUES (%s,%s,%s)'    
        data = (fname, lname, shelterID)

        db_connection = connect_to_database()
        execute_query(db_connection, query, data)
        return redirect('/counselors')

#applications page
@app.route('/applications')
def browse_applications():
    print("Fetching and rendering applications web page")
    db_connection = connect_to_database()
    #query to diaplay application table
    query = "SELECT app_num, app_date, Shelters.name, concat(Adopters.first_name,' ', Adopters.last_name), concat(Counselors.first_name,' ', Counselors.last_name), p1.name, p2.name, p3.name, meet_greet, num_adults, num_children, num_pets, home_type, home_status FROM Applications AS app INNER JOIN Adopters ON app.adopterID = Adopters.adopterID INNER JOIN Shelters ON app.shelterID = app.shelterID LEFT JOIN Counselors ON app.counselorID = Counselors.counselorID LEFT JOIN Dogs AS p1 ON app.petID1 = p1.petID LEFT JOIN Dogs AS p2 ON app.petID2 = p2.petID LEFT JOIN Dogs AS p3 ON app.petID3 = p3.petID ORDER BY app_num;"
    result = execute_query(db_connection, query).fetchall()
    print(result)
    return render_template('applications.html', rows=result)

#addoption details page (relationship between apps and dogs)
@app.route('/adoption_details', methods=['POST','GET'])
def browse_adoption_details():
    db_connection = connect_to_database()
    if request.method == 'GET':
        print("Fetching and rendering adoption details web page")
        #query to display applications table
        query = "SELECT AdoptionDetails.app_num, Adopters.first_name, Adopters.last_name, Applications.counselorID, Dogs.name AS Dog_Name, app_status, AdoptionDetails.petID from AdoptionDetails INNER JOIN Applications ON AdoptionDetails.app_num = Applications.app_num INNER JOIN Adopters ON Applications.adopterID = Adopters.adopterID INNER JOIN Dogs ON AdoptionDetails.petID = Dogs.petID;"
        result = execute_query(db_connection, query).fetchall()
        print(result)
        #query for form dropdown- diplays available & pending dogs
        query = 'SELECT petID, name from Dogs where adoption_status != "Adopted"'
        pets = execute_query(db_connection,query).fetchall()
        print(pets)
        #query to display applications by adopters name
        query = 'SELECT app_num, app_num, Adopters.first_name, Adopters.last_name from Applications INNER JOIN Adopters ON Applications.adopterID = Adopters.adopterID'
        applications = execute_query(db_connection,query).fetchall()
        print(applications)

        return render_template('adoption_details.html', rows=result, pets=pets, apps=applications)
    elif request.method == 'POST':
        print("Adding an adoption detail")
        db_connection = connect_to_database()
        appID = request.form['appID'] 
        petID = request.form['petID'] 
        appstatus = request.form['appStatus'] 
        #query to add adoption details 
        query = 'INSERT INTO AdoptionDetails (app_num, petID, app_status) VALUES (%s,%s,%s)'    
        data = (appID, petID, appstatus)
        execute_query(db_connection, query, data)
        #creating adoption detail also adds dog to application
        query = 'UPDATE Applications SET petID3 = ( case when ( petID2 is not null and petID3 is null ) then %s else petID3 end ), petID2 = ( case when ( petID1 is not null and petID2 is null ) then %s else petID2 end ), petID1 = ( case when ( petID1 is null ) then %s else petID1 end ) WHERE app_num=%s;'
        data=(petID,petID,petID,appID)
        result = execute_query(db_connection,query,data)

        print(str(result.rowcount) + " row(s) updated")
        return redirect('/adoption_details')

#delete adoption page- runs query then redirects to adoption details
@app.route('/delete_adoption/<int:app_id>,<int:pet_id>')
def delete_adoptions(app_id, pet_id):
    db_connection = connect_to_database()
    data = (app_id, pet_id)
    #query to delete adoption details
    query = "DELETE FROM AdoptionDetails WHERE app_num = %s AND petID = %s"
    execute_query(db_connection, query, data)
    #deleting adoption detail also removes dog from application
    query = 'UPDATE Applications SET petID3 = ( case when ( petID2 = %s ) then NULL else petID3 end ), petID2 = ( case when ( petID1 = %s ) then NULL else petID2 end ), petID1 = ( case when ( petID1 = %s ) then NULL else petID1 end ) WHERE app_num=%s;'
    data=(pet_id,pet_id,pet_id,app_id)
    result = execute_query(db_connection,query,data)

    return redirect('/adoption_details')

#add application page
@app.route('/add_application', methods=['POST','GET'])
def add_application():
    db_connection = connect_to_database()
    if request.method == 'GET':
        #query to populate shelter dropdown
        query = 'SELECT shelterID, name from Shelters'
        shelters = execute_query(db_connection,query).fetchall()
        print(shelters)
        #query to populate adopter dropdown
        query = 'SELECT adopterID, adopterID, first_name, last_name from Adopters'
        adopters = execute_query(db_connection,query).fetchall()
        print(adopters)
        #query to populate counselor drowpdown
        query = 'SELECT counselorID, counselorID, first_name, last_name from Counselors'
        counselors = execute_query(db_connection,query).fetchall()
        print(counselors)
        #query to populate available/pending dogs dropdown
        query = 'SELECT petID, petID, name from Dogs where adoption_status!="Adopted"'
        pets = execute_query(db_connection,query).fetchall()
        print(pets)
        
        return render_template('add_application.html', shelters = shelters, adopters = adopters, counselors = counselors, pets = pets)
    elif request.method == 'POST':
        print("Adding an application")
        date = request.form['appDate'] 
        adopterID = request.form['adopterID'] 
        shelterID = request.form['shelterID'] 
        counselorID = request.form['counselorID'] 
        petID1 = request.form['petID1']
        if petID1 == "":
            petID1 = None 
        petID2 = request.form['petID2']
        if petID2 == "":
            petID2 = None
        petID3 = request.form['petID3']
        if petID3 == "":
            petID3 = None
        meet_greet = request.form['meetGreet'] 
        num_adults = request.form['numAdults'] 
        num_kids = request.form['numChildren'] 
        num_pets = request.form['numAnimals'] 
        home_status = request.form['homeStatus'] 
        home_type = request.form['homeType'] 

        db_connection = connect_to_database()
        #add adpplication query
        query = 'INSERT INTO Applications (app_date, shelterID, counselorID, adopterID, petID1, petID2, petID3, meet_greet, num_adults, num_children, num_pets, home_type, home_status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        data = (date, shelterID, counselorID, adopterID, petID1, petID2, petID3, meet_greet, num_adults, num_kids, num_pets, home_type, home_status)
        result=execute_query(db_connection, query, data)
        print(result.lastrowid)

        #adding application with pets also results in adding to adoption details
        if petID1 != None:
            query2 = 'INSERT INTO AdoptionDetails (app_num ,petID, app_status) VALUES (%s,%s,%s)'
            data2 = (result.lastrowid, petID1, 'Pending')
            execute_query(db_connection,query2,data2)

        if petID2 != None:
            query3 = 'INSERT INTO AdoptionDetails (app_num ,petID, app_status) VALUES (%s,%s,%s)'
            data3 = (result.lastrowid, petID2, 'Pending')
            execute_query(db_connection,query3,data3)

        if petID3 != None:
            query4 = 'INSERT INTO AdoptionDetails (app_num ,petID, app_status) VALUES (%s,%s,%s)'
            data4 = (result.lastrowid, petID3, 'Pending')
            execute_query(db_connection,query4,data4)

        return redirect('/applications')

#update adoption page
@app.route('/update_adoption/<int:app_id>,<int:pet_id>', methods=['POST','GET'])
def update_adoption_details(app_id, pet_id):
    db_connection = connect_to_database()

    if request.method == 'GET':
        print("Fetching and rendering adoption details web page")
        #displays adoption detail with given app id and pet id
        query = 'SELECT AdoptionDetails.app_num, Adopters.first_name, Adopters.last_name, Applications.counselorID, Dogs.name, app_status, AdoptionDetails.petID from AdoptionDetails INNER JOIN Applications ON AdoptionDetails.app_num = Applications.app_num INNER JOIN Adopters ON Applications.adopterID = Adopters.adopterID INNER JOIN Dogs ON AdoptionDetails.petID = Dogs.petID WHERE AdoptionDetails.app_num = %s AND AdoptionDetails.petID = %s'
        data = (app_id, pet_id)
        adoption_result = execute_query(db_connection, query, data).fetchone()
        print(adoption_result)
        return render_template('update_adoption.html', adoption=adoption_result)
    elif request.method == 'POST':
        print('The POST Request')
        app_num = request.form['app_num']
        petID = request.form['petID']
        status = request.form['status']
        #updates status of adoption
        query = "UPDATE AdoptionDetails SET app_status=%s WHERE app_num=%s AND petID=%s"
        data=(status,app_num,petID)
        result = execute_query(db_connection,query,data)
        print(str(result.rowcount) + " row(s) updated")
        #set adoption status of dog based on status of application
        if status == 'Pending':
            query = "UPDATE Dogs SET adoption_status=%s WHERE petID=%s"
            data=('Pending',petID)
            result = execute_query(db_connection,query,data)
            print(str(result.rowcount) + " row(s) updated")
        elif status == 'Approved':
            query = "UPDATE Dogs SET adoption_status=%s WHERE petID=%s"
            data=('Adopted',petID)
            result = execute_query(db_connection,query,data)
            print(str(result.rowcount) + " row(s) updated")
        elif status == 'Denied':
            query = "UPDATE Dogs SET adoption_status=%s WHERE petID=%s"
            data=('Available',petID)
            result = execute_query(db_connection,query,data)
            print(str(result.rowcount) + " row(s) updated")


    return redirect('/adoption_details')

#update counselor page
@app.route('/update_counselor/<int:id>', methods=['POST','GET'])
def update_counselor(id):
    db_connection = connect_to_database()
    #display existing data
    if request.method == 'GET':
        #query to populate form for counselor with given id
        people_query = 'SELECT counselorID, first_name, last_name, shelterID FROM Counselors where counselorID = %s' % (id)
        people_result = execute_query(db_connection, people_query).fetchone()

        if people_result == None:
            return "No such person found!"
        #query to poulate shelter dropdown on form
        shelters_query = 'SELECT shelterID, name from Shelters'
        shelters_results = execute_query(db_connection, shelters_query).fetchall()

        print('Returning')
        return render_template('update_counselor.html', shelters = shelters_results, person = people_result)
    elif request.method == 'POST':
        print('The POST request')
        #grabbing info from the form
        character_id = request.form['character_id']
        fname = request.form['fname']
        lname = request.form['lname']
        shelter = request.form['shelter']
        #query to update counselors
        query = "UPDATE Counselors SET first_name= %s, last_name= %s, shelterID = %s WHERE counselorID = %s"
        data = (fname, lname, shelter, character_id)
        result = execute_query(db_connection, query, data)
        print(str(result.rowcount) + " row(s) updated")

        return redirect('/counselors')

#delete counselor page- runs query then redirects to counselor page
@app.route('/delete_counselor/<int:id>')
def delete_people(id):
    #deletes a person with the given id
    db_connection = connect_to_database()
    data = (id,)

    query = "DELETE FROM Counselors WHERE counselorID = %s"
    result = execute_query(db_connection, query, data)

    print(str(result.rowcount) + " row deleted")

    return redirect('/counselors')

#delete application page- runs query then redirects to applications page
@app.route('/delete_application/<int:id>')
def delete_app(id):
    #deletes a application with the given id
    db_connection = connect_to_database()
    data = (id,)

    query = "DELETE FROM Applications WHERE app_num = %s"
    result = execute_query(db_connection, query, data)

    print(str(result.rowcount) + " row deleted")

    return redirect('/applications')

#update application page
@app.route('/update_application/<int:id>', methods=['POST','GET'])
def update_application(id):
    db_connection = connect_to_database()

    if request.method == 'GET':
        #query to populate form for appliation with given id
        app_query = 'SELECT * FROM Applications where app_num = %s' % (id)
        app_result = execute_query(db_connection, app_query).fetchone()

        if app_result == None:
            return "No such application found!"
        #query to populate shelter dropdown on form
        query = 'SELECT shelterID, name from Shelters'
        shelters = execute_query(db_connection,query).fetchall()
        print(shelters)
        #query to populate adopter dropdown on form
        query = 'SELECT adopterID, adopterID, first_name, last_name from Adopters'
        adopters = execute_query(db_connection,query).fetchall()
        print(adopters)
        #query to populate counselor dropdown on form
        query = 'SELECT counselorID, counselorID, first_name, last_name from Counselors'
        counselors = execute_query(db_connection,query).fetchall()
        print(counselors)

        #query = 'SELECT petID, petID, name from Dogs where adoption_status!="Adopted"'
        #pets = execute_query(db_connection,query).fetchall()
        #print(pets)
        
        return render_template('update_application.html', shelters=shelters, app=app_result, adopters = adopters, counselors = counselors) #pets = pets)
    elif request.method == 'POST':
        print('The POST request')
        #grabbing info from the form
        app_id = request.form['app_id']
        adopter_id = request.form['adopter_id']
        fname = request.form['fname']
        lname = request.form['lname']
        shelterID = request.form['shelterID']
        counselorID = request.form['counselorID']
        if counselorID == "":
            counselorID = None
        #petID1 = request.form['petID1']
        #if petID1 == "":
        #    petID1 = None 
        #petID2 = request.form['petID2']
        #if petID2 == "":
        #    petID2 = None 
        #petID3 = request.form['petID3']
        #if petID3 == "":
        #    petID3 = None 
        meetGreet = request.form['meetGreet']
        numAdults = request.form['numAdults']
        numChildren = request.form['numChildren']
        numPets = request.form['numPets']
        homeType = request.form['homeType']
        homeStatus = request.form['homeStatus']
        #query to update application 
        query = "UPDATE Applications SET shelterID= %s, counselorID= %s, meet_greet = %s, num_adults = %s, num_children = %s, num_pets = %s, home_type = %s, home_status = %s WHERE app_num = %s"
        data = (shelterID, counselorID, meetGreet, numAdults, numChildren, numPets, homeType, homeStatus, app_id)
        result = execute_query(db_connection, query, data)
        print(str(result.rowcount) + " row(s) updated")
        #also update adopters name if needed
        query2 = "UPDATE Adopters SET first_name= %s, last_name= %s WHERE adopterID = %s"
        data2 = (fname, lname, adopter_id)
        result2 = execute_query(db_connection, query2, data2)
        print(str(result2.rowcount) + " row(s) updated")

        return redirect('/applications')
#############################SHELBIS PAGES###############################


### DOG PAGES ### 
@app.route('/dogs', methods=['POST','GET'])
def browse_dogs():

    db_connection = connect_to_database()

    if request.method == 'GET':
        #query to display dogs table
        query = 'SELECT petID, Shelters.name, Dogs.name, birthday, gender, breed, size, adoption_status, energy_level, coat_type, color, dogs_ok, cats_ok, kids_ok FROM Dogs INNER JOIN Shelters ON Dogs.shelterID = Shelters.shelterID'
        result = execute_query(db_connection, query).fetchall()
        
        return render_template('dogs.html', rows=result)
    elif request.method == 'POST':
        status = request.form['dogstatus']
        search = '%' + request.form['dogSearch'] + '%'
        #if filter chosen-
        if status != "any":
            #filter dogs by given status
            query = "SELECT petID, Shelters.name, Dogs.name, birthday, gender, breed, size, adoption_status, energy_level, coat_type, color, dogs_ok, cats_ok, kids_ok FROM Dogs INNER JOIN Shelters ON Dogs.shelterID = Shelters.shelterID WHERE adoption_status=%s"
            data = (status,)
            result = execute_query(db_connection, query, data).fetchall()
        #if search criteria entered  
        elif search != None:
            #search for dog by name
            query = "SELECT petID, Shelters.name, Dogs.name, birthday, gender, breed, size, adoption_status, energy_level, coat_type, color, dogs_ok, cats_ok, kids_ok FROM Dogs INNER JOIN Shelters ON Dogs.shelterID = Shelters.shelterID WHERE Dogs.name LIKE %s"
            data = (search,)
            result = execute_query(db_connection, query, data).fetchall()
        #default- display dog table per usual
        else:
            query = 'SELECT petID, Shelters.name, Dogs.name, birthday, gender, breed, size, adoption_status, energy_level, coat_type, color, dogs_ok, cats_ok, kids_ok FROM Dogs INNER JOIN Shelters ON Dogs.shelterID = Shelters.shelterID'
            result = execute_query(db_connection, query).fetchall()
    
        return render_template('dogs.html', rows=result)

#add dog page
@app.route('/add_dog', methods=['POST','GET'])
def add_new_dog():
    
    db_connection = connect_to_database()
    if request.method == 'GET':
       
        return render_template('add_dog.html')
    elif request.method == 'POST':
        print("Add new dog!")
        shelterID = '1'
        name = request.form['dogname']
        birthday = request.form['birthday']
        breed = request.form['breed']
        gender = request.form['doggender']
        size = request.form['dogsize']
        status = request.form['dogstatus']
        energy = request.form['energy']
        coat = request.form['coat']
        color = request.form['color']
        dogsOK = request.form['dogsOK']
        catsOK = request.form['catsOK']
        kidsOK = request.form['kidsOK']
        #query to add dog
        query = 'INSERT INTO Dogs (shelterID, name, birthday, gender, breed, size, adoption_status, energy_level, coat_type, color, dogs_ok, cats_ok, kids_ok) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        data = (shelterID, name, birthday, gender, breed, size, status, energy, coat, color, dogsOK, catsOK, kidsOK)
        execute_query(db_connection, query, data)
        return redirect('/dogs')

#update dog page
@app.route('/update_dog/<int:id>', methods=['POST','GET'])
def update_dog(id):
    print('In the function')
    db_connection = connect_to_database()
    #display existing data
    if request.method == 'GET':
        print('The GET request')
        #query to populate form with values for given adopter id
        dog_query = 'SELECT * from Dogs WHERE petID = %s'  % (id)
        dog_result = execute_query(db_connection, dog_query).fetchone()

        if dog_result == None:
            return "No such dog found!"

        print('Returning')
        return render_template('update_dog.html', dog = dog_result)
    elif request.method == 'POST':
        print('The POST request')
        petID = request.form['petID']
        name = request.form['dogname']
        birthday = request.form['birthday']
        breed = request.form['breed']
        gender = request.form['doggender']
        size = request.form['dogsize']
        status = request.form['dogstatus']
        energy = request.form['energy']
        coat = request.form['coat']
        color = request.form['color']
        dogsOK = request.form['dogsOK']
        catsOK = request.form['catsOK']
        kidsOK = request.form['kidsOK']
        #updates dog with given id
        query = "UPDATE Dogs SET name=%s, birthday=%s, gender=%s, breed=%s, size=%s, adoption_status=%s, energy_level=%s, coat_type=%s, color=%s, dogs_ok=%s, cats_ok=%s, kids_ok=%s WHERE petID=%s"
        data = (name, birthday, gender, breed, size, status, energy, coat, color, dogsOK, catsOK, kidsOK, petID)
        result = execute_query(db_connection, query, data)
        print(str(result.rowcount) + " row(s) updated")
        return redirect('/dogs')

#delete dog page- runs query then redirects to dog page
@app.route('/delete_dog/<int:id>')
def delete_dog(id):
    #deletes a dog with the given id
    db_connection = connect_to_database()
    query = "DELETE FROM Dogs WHERE petID = %s"
    data = (id,)

    execute_query(db_connection, query, data)
    return redirect('/dogs')

### ADOPTERS PAGES ###
@app.route('/adopters', methods=['POST','GET'])
def adopters():
    
    db_connection = connect_to_database()
    if request.method == 'GET':
        #diplay all adopters
        query = "SELECT * from Adopters;"
        result = execute_query(db_connection, query).fetchall()
        print(result)

        return render_template('adopters.html', rows=result)
    elif request.method == 'POST':
        search = '%' + request.form['adopterSearch'] + '%'
        button = request.form['submit_button']
        #adopterSearch = request.form['adopterSearch']
        if button == 'Search':
            #query to search adopters
            query = "SELECT * FROM Adopters WHERE first_name LIKE %s OR last_name LIKE %s OR phone LIKE %s OR email LIKE %s OR street LIKE %s OR city LIKE %s OR state LIKE %s OR zip LIKE %s;"
            data = (search, search, search, search, search, search, search, search)
            result = execute_query(db_connection, query, data).fetchall()
            print(result)
            return render_template('adopters.html', rows=result)
        elif button == 'Submit':       
            print("Add new adopter!")
            first_name = request.form['fname']
            last_name = request.form['lname']
            phone = request.form['phone']
            email = request.form['email']
            street = request.form['street']
            city = request.form['city']
            state = request.form['state']
            zipcode = request.form['zipcode']
            #query to add adopter
            query = 'INSERT INTO Adopters (first_name, last_name, phone, email, street, city, state, zip) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'
            data = (first_name, last_name, phone, email, street, city, state, zipcode)
            execute_query(db_connection, query, data)
            return redirect('/adopters')

@app.route('/update_adopter/<int:id>', methods=['POST','GET'])
def update_adopter(id):
    print('In the function')
    db_connection = connect_to_database()
    #display existing data
    if request.method == 'GET':
        print('The GET request')
        #query to populate form with values for given adopter id
        adopter_query = 'SELECT * FROM Adopters WHERE adopterID = %s'  % (id)
        adopter_result = execute_query(db_connection, adopter_query).fetchone()

        if adopter_result == None:
            return "No such person found!"
        #query to display adopters table
        table_query = 'SELECT * FROM Adopters'
        table_results = execute_query(db_connection, table_query).fetchall()

        print('Returning')
        return render_template('update_adopter.html', adopter = adopter_result, rows = table_results)
    elif request.method == 'POST':
        print('The POST request')
        adopterID =request.form['adopterID']
        first_name = request.form['fname']
        last_name = request.form['lname']
        phone = request.form['phone']
        email = request.form['email']
        street = request.form['street']
        city = request.form['city']
        state = request.form['state']
        zipcode = request.form['zipcode']
        #update adopter
        query = 'UPDATE Adopters SET first_name=%s, last_name=%s, phone=%s, email=%s, street=%s, city=%s, state=%s, zip=%s WHERE adopterID=%s'
        data = (first_name, last_name, phone, email, street, city, state, zipcode, adopterID)
        result = execute_query(db_connection, query, data)
        print(str(result.rowcount) + " row(s) updated")

        return redirect('/adopters')

@app.route('/delete_adopter/<int:id>')
def delete_adopter(id):
    #deletes a dog with the given id
    db_connection = connect_to_database()
    query = "DELETE FROM Adopters WHERE adopterID = %s"
    data = (id,)

    execute_query(db_connection, query, data)
    return redirect('/adopters')