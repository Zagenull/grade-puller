from pyscope import GSConnection
from trello import TrelloApi
import datetime, time 
class gradePuller:
    """Class to Pull assignments from various places """

    def __init__(self):
        '''Initialize trello ID's'''
        self.TRELLO_APP_KEY = ""
        self.TOKEN = ""
        self.listID = ""
        self.cardPos ="bottom" #'top', 'bottom', or a number


    def timeconverter(self, x):
        '''Converts various time formats to a standardized one for trello usage'''
        try:
            my_time = datetime.datetime.strptime(x, '%b %d at %I:%M%p').date()
        except:
            try:
                my_time = datetime.datetime.strptime(x, '%b %d, %Y %I:%M %p').date()
            except:
                print("If you're seeing this timeconverter() probably broke...")
                return
        try:
            my_time2 = datetime.datetime(year=2022,day=my_time.day-1,month=my_time.month)
        except:
            try:
                my_time2 = datetime.datetime(year=2022,day=31,month=my_time.month-1)
            except:
                try:
                    my_time2 = datetime.datetime(year=2022,day=30,month=my_time.month-1)
                except:
                    try:
                        my_time2 = datetime.datetime(year=2022,day=29,month=my_time.month-1)
                    except:
                        my_time2 = datetime.datetime(year=2022,day=28,month=my_time.month-1)    
        return my_time2.strftime("%m/%d/%Y")

    def send_assignments(self):
        '''Pushes the assignments to Trello with due dates, may add support for other systems later'''
        s = GSConnection(); s.loginGradescope('GSUSER','GSPASS'); ass = s.assignmentsGradescope() #change to your pass/user
        s.loginSakai("SAKAIUSER", "SAKAIPASS") #change to your pass/user
        if ass == False:
            print("ERROR: You probably didn't change the user/pass...")
            return None
        ass.update(s.assignmentsSakai())
        trello = TrelloApi(self.TRELLO_APP_KEY, self.TOKEN)
        cards = trello.lists.get_card(idList = self.listID)
        card_names = []

        #searches txt for assignment names not to be pushed to trello, must be in the format pulled (so to add an exception first let it appear on your board to get it's name)
        courseExceptions = open('exceptions.txt', 'r'); content = courseExceptions.read(); contentSplit = content.split('\n'); courseExceptions.close()

        for i in range(len(contentSplit)): 
            card_names.append(contentSplit[i])
        for i in range(len(cards)):
            card_names.append(cards[i]['name'])

        for keys in ass:
            for i in range(len(ass[keys][0])):
                try:
                    title = f'{keys} - {ass[keys][0][i]}'
                    time = self.timeconverter(ass[keys][1][i])
                    if title not in card_names:
                        try:
                            newCard = trello.cards.new(title, idList=self.listID, pos=self.cardPos, due=time)
                        except:
                            continue
                    else:
                        continue
                except:
                    continue
        print('Success!')

if __name__=="__main__":
    assing = gradePuller()
    assing.send_assignments()
    time.sleep(3)