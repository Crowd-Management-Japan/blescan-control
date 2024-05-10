from datetime import timedelta

class Config:
    """
    Class that contains static constants.
    """
    # hostname and port for the flask application
    HOSTNAME = '0.0.0.0'
    PORT = 5555

    # server ip to deploy for map visualization
    SERVER_IP = '127.0.0.1'

    # specific settings for id used, measured value and color scale
    ID_LIST = list(range(1, 101))
    VALUE_TYPE = 'close'
    SCALE_MAX = 80
    CIRCLE_SIZE = 25
