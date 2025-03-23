from configparser import ConfigParser

def config(filename="database.ini", section="postgresql"):
    #Create an object parser which is equal to the ConfigParser class
    parser = ConfigParser()
    #read the config file
    parser.read(filename)
    #iterate over the filename and return each key value pair as an item in the dictionary
    #create an empty dictoinary
    db = {}
    #verification step to ensure that the parser has a section header
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section{0} is not found in the {1} file. '.format(section, filename))
    return db