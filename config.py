import os
from dotenv import load_dotenv
from cachelib.file import FileSystemCache


#Stores the absolute path to the current directory in which this file is localed, which should be the root project directory
project_dir = os.path.abspath(os.path.dirname(__file__))


#Load any environment variables set in the .env file (these are non-flask specific and/or confidential variables like credentials)
#Other env variables in the .flaskenv file are auto-loaded
load_dotenv(os.path.join(project_dir, ".env"))


#Config object to be passed to the flask app
class Config:
    """
    Hardcoded Server Config
    """
    #This is a cryptographic key used by flask and it's many extensions and modules like session for security purposes.
    #Ideally it's set in the .env file. If not, it will fallback on the hardcoded value below.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application. Please set it in .env file.")

    #APP branding
    APP_NAME = "SAGE"
    APP_NAME_FULL = "STEP API GATEWAY ENGINE"
    APP_VERSION = "V1.0.0 (The light of day)"

    #Location of the app DB
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(project_dir, "db/app.db")

    #Flask session plugin config to store user session in a directory on server
    SESSION_PERMANENT = False
    SESSION_TYPE = "cachelib"
    SESSION_CACHELIB = FileSystemCache(cache_dir=os.path.join(project_dir, 'db/flask_session'), threshold=500)
    
    #Email and subject to use when using the 'Email Developer' Link
    PROJECT_LINK = "https://github.com/sabino-pereira/SAGE"

    #Sample query for GraphQL
    GRAPQL_SAMPLE_QUERY = """
    query sampleQuery {
        product(id: "", context: "<dynamic-context>", workspace: "<dynamic-workspace>") {
            id
            name
            approvalStatus
            currentRevision
            hasChildren
            objectType {
                id
                name
            }
        }
    }
    """

    #Quotes to Display in the user menu
    QUOTES_LIST = [
        "The reasonable man adapts himself to the world, the unreasonable one persists in trying to adapt the world to himself. <br> Therefore all progress depends on the unreasonable man.",
        "The ones who are crazy enough to think they can change the world are the ones who do.",
        "Success is not for the chosen few, but for the few who choose to fight for it.",
        "If you want something you've never had, you must be willing to do something you've never done.",
        "Comfort zones are where dreams go to die.",
        "Those who dare to fail miserably can achieve greatly.",
        "Courage is not the absence of fear, but the triumph over it.",
        "Act as if what you do makes a difference. It does.",
        "Don't be afraid to give up the good to go for the great.",
        "Everything you've ever wanted is on the other side of fear.",
        "In the beginning the Universe was created. <br> This has made a lot of people very angry and has been widely regarded as a bad move.",
        "There is nothing more permanent than a temporary solution.",
        "First do it, then do it right, then do it better.",
        "It always seems impossible until it's done.",
        "Talk is cheap. Show me the code.",
        "Simplicity is the ultimate sophistication.",
        "The best way to predict the future is to invent it.",
        "A ship in port is safe, but that's not what ships are built for.",
        "Do not go where the path may lead, go instead where there is no path and leave a trail.",
        "Believe you can and you're halfway there.",
        "Any fool can write code that a computer can understand. Good programmers write code that humans can understand.",
        "Make it work, make it right, make it fast.",
        "Code is like humor. When you have to explain it, it's bad.",
        "Experience is the name everyone gives to their mistakes.",
        "It's not a bug; it's an undocumented feature.",
        "The only way to do great work is to love what you do.",
        "Stay hungry, stay foolish.",
        "Innovation distinguishes between a leader and a follower.",
        "The most damaging phrase in the language is 'It's always been done this way'.",
        "If you think good architecture is expensive, try bad architecture.",
        "Measuring programming progress by lines of code is like measuring aircraft building progress by weight."
    ]


    """
    User Overidable Config
    """
    #This option allows to enable or disable the registration process.
    REGISTRATION_ALLOWED = True
    
    #MAX Systems that can be added per user
    MAX_SYSTEMS = 20

    #MAX Quick Access links that can be added per user
    MAX_QUICK_ACCESS_LINKS = 20

    #Default timeout duration in seconds for all api requests
    API_REQUEST_TIMEOUT = 120
    
    # Time for which a bearer token is valid after requesting in seconds
    API_BEARER_TOKEN_TTL = 300

    