import sqlite3

class application_database():
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")       
 
        if not self.cursor.fetchall():
            self.create_db(self.connection)


    def create_db(self,cursor):

        self.cursor.execute("""CREATE TABLE Application(
            appId TEXT,
            url TEXT,
            title TEXT,
            description TEXT,
            minInstalls INTEGER,
            realInstalls INTEGER,
            reviews INTEGER,
            score REAL,
            ratings INTEGER,
            developer TEXT,
            developerId TEXT,
            developerEmail TEXT,
            developerWebsite TEXT,
            privacyPolicy TEXT,
            developerAddress TEXT,
            icon TEXT,
            headerImage TEXT,
            released TEXT,
            updated TEXT,
            version TEXT,
            comments TEXT,
            permissions TEXT)""")


    def insert_application(self,info):
        sql = """INSERT INTO Application( 
            appId ,
            url,
            title ,
            description ,
            minInstalls ,
            realInstalls ,
            reviews ,
            score ,
            ratings ,
            developer ,
            developerId ,
            developerEmail ,
            developerWebsite ,
            privacyPolicy ,
            developerAddress ,
            icon ,
            headerImage ,
            released ,
            updated ,
            version ,
            comments ,
            permissions 
         ) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        self.execute_update(sql,info)

    def show_results(self):
        sql = """SELECT * from Application"""
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def execute_update(self,sql,attribs):
        self.cursor.execute(sql,attribs)
        self.connection.commit()
        return
