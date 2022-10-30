import requests
from bs4 import BeautifulSoup
from enum import Enum
try:
   from account import GSAccount
except ModuleNotFoundError:
   from .account import GSAccount

class ConnState(Enum):
    INIT = 0
    LOGGED_IN = 1

class GSConnection():
    '''The main connection class that keeps state about the current connection.'''
        
    def __init__(self):
        '''Initialize the session for the connection.'''
        self.session = requests.Session()
        self.state = ConnState.INIT
        self.account = None
        self.courses = []

    def loginGradescope(self, email, pswd):
        '''
        Login to gradescope using email and password.
        Note that the future commands depend on account privilages.
        '''
        init_resp = self.session.get("https://www.gradescope.com/")
        parsed_init_resp = BeautifulSoup(init_resp.text, 'html.parser')
        for form in parsed_init_resp.find_all('form'):
            if form.get("action") == "/login":
                for inp in form.find_all('input'):
                    if inp.get('name') == "authenticity_token":
                        auth_token = inp.get('value')

        login_data = {
            "utf8": "✓",
            "session[email]": email,
            "session[password]": pswd,
            "session[remember_me]": 0,
            "commit": "Log In",
            "session[remember_me_sso]": 0,
            "authenticity_token": auth_token,
        }
        login_resp = self.session.post("https://www.gradescope.com/login", params=login_data)
        if len(login_resp.history) != 0:
            if login_resp.history[0].status_code == requests.codes.found:
                self.state = ConnState.LOGGED_IN
                self.account = GSAccount(email, self.session)
                return True
        else:
            return False

    def loginSakai(self, uid, pswd):
        '''
        Login to sakai using email and password.
        Note that the future commands depend on account privilages.
        '''
        init_resp = self.session.get("https://sakai.unc.edu/portal/xlogin")
        parsed_init_resp = BeautifulSoup(init_resp.text, 'html.parser')
        for form in parsed_init_resp.find_all('form'):
            if form.get("action") == "https://sakai.unc.edu/portal/xlogin":
                for inp in form.find_all('input'):
                    if inp.get('name') == "eid":
                        auth_token = inp.get('value')

        login_data = {
            "utf8": "✓",
            "eid": uid,
            "pw": pswd,
            "session[remember_me]": 0,
            "commit": "Log In",
            "session[remember_me_sso]": 0,
            "authenticity_token": auth_token,
        }
        login_resp = self.session.post("https://sakai.unc.edu/portal/xlogin", params=login_data)
        if len(login_resp.history) != 0:
            if login_resp.history[0].status_code == requests.codes.found:
                self.state = ConnState.LOGGED_IN
                self.account = GSAccount(uid, self.session)
                return True
        else:
            return False

    def getAccount(self):
        '''
        Gets and parses account data after login. Note will return false if we are not in a logged in state, but 
        this is subject to change.
        '''
        if self.state != ConnState.LOGGED_IN:
            return False # Should raise exception
        # Get account page and parse it using bs4
        account_resp = self.session.get("https://www.gradescope.com/account")
        parsed_account_resp = BeautifulSoup(account_resp.text, 'html.parser')

        # Get instructor course data
        instructor_courses = parsed_account_resp.find('h1', class_ ='pageHeading').next_sibling
        
        for course in instructor_courses.find_all('a', class_ = 'courseBox'):
            shortname = course.find('h3', class_ = 'courseBox--shortname').text
            name = course.find('h4', class_ = 'courseBox--name').text
            cid = course.get("href").split("/")[-1]
            year = None
            print(cid, name, shortname)
            for tag in course.parent.previous_siblings:
                if 'courseList--term' in tag.get("class"):
                    year = tag.string
                    break
            if year is None:
                return False # Should probably raise an exception.
            self.account.add_class(cid, name, shortname, year, instructor = True)
        try:
            student_courses = parsed_account_resp.find('h1', class_ ='pageHeading', string = "Student Courses").next_sibling
        except:
            return
        for course in student_courses.find_all('a', class_ = 'courseBox'):
            shortname = course.find('h3', class_ = 'courseBox--shortname').text
            name = course.find('h4', class_ = 'courseBox--name').text
            cid = course.get("href").split("/")[-1]
            
            for tag in course.parent.previous_siblings:
                if tag.get("class") == "courseList--term pageSubheading":
                    year = tag.body
                    break
            if year is None:
                return False # Should probably raise an exception.
            self.account.add_class(cid, name, shortname, year)
    

    def assignmentsGradescope(self):
        """Pulls assignments from each class with due dates by iterating through a txt of class ID's, returns a dictonary of assignments and due dates"""
        if self.state != ConnState.LOGGED_IN:
            return False # Should raise exception

        # Get account page and parse it using bs4
        all_assignments = dict[str, list[list[str]]] 
        all_assignments = {}

        # Read course numbers from txt
        course_numbers = open('courseGradescope.txt', 'r'); content = course_numbers.read(); self.courses = content.split('\n'); course_numbers.close()

        for course in self.courses:
            ass = []
            date = []
            account_resp = self.session.get(f"https://www.gradescope.com/courses/{course}")
            parsed_account_resp = BeautifulSoup(account_resp.text, 'html.parser')
            ass_table = parsed_account_resp.find(id="assignments-student-table")
            assignments = ass_table.find_all(class_ = "table--primaryLink")
            for assignment in assignments:
                try:
                    if assignment.nextSibling.get_text() == 'No Submission':
                        ass.append(assignment.get_text())
                        date.append(assignment.nextSibling.nextSibling.find(class_='submissionTimeChart--dueDate').get_text())
                except:
                    continue
            all_assignments[parsed_account_resp.find(class_ = 'courseHeader--title').get_text().split('.')[0]] = [ass, date]

        return all_assignments

    def assignmentsSakai(self):
        """Pulls assignments from each class with due dates by iterating through a txt of class ID's, returns a dictonary of assignments and due dates"""
        if self.state != ConnState.LOGGED_IN:
            return False # Should raise exception

        # Get account page and parse it using bs4
        all_assignments = dict[str, list[list[str]]] 
        all_assignments = {}

        # Read course numbers from txt
        course_numbers = open('courseSakai.txt', 'r'); content = course_numbers.read(); self.courses = content.split('\n'); course_numbers.close()

        for course_assignments in self.courses:
            ass = []
            date = []
            account_resp = self.session.get(f"{course_assignments}")
            parsed_account_resp = BeautifulSoup(account_resp.text, 'html.parser')
            ass_table = parsed_account_resp.find(class_="table table-hover table-striped table-bordered") #finds assignment table on Sakai
            try:
                assignments = ass_table.find_all('td', headers="title")
            except AttributeError: #throws AttributeError "NoneType" when no assignments are within a class
                print("One or more Gradescope classes have no assignments.")
                break
            for assignment in assignments:
                print(assignment.nextSibling.nextSibling.get_text().strip())
                if assignment.nextSibling.nextSibling.get_text().strip() == 'Not Started':
                    ass.append(assignment.get_text().strip())
                    date.append(assignment.nextSibling.nextSibling.nextSibling.nextSibling.nextSibling.nextSibling.get_text().strip())
            all_assignments[parsed_account_resp.find(class_ = 'Mrphs-hierarchy--siteName-label').get_text().strip().split('.')[0]] = [ass, date]

        return all_assignments
        


# THIS IS STRICTLY FOR DEVELOPMENT TESTING :( Sorry for leaving it in.
if __name__=="__main__":
    conn = GSConnection()
    conn.loginSakai("SAKAIUSER", "SAKAIPASS")
    print(conn.state)
    #conn.get_account()
    print(conn.assignmentsSakai())
