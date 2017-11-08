import os

LOG_FILE_DIR = "SOL_Logs/"
LIST_OF_APPS = ['core', 'db', 'lib', 'service_online', 'ui']


if not os.path.exists(LOG_FILE_DIR):
    os.makedirs(LOG_FILE_DIR)

SIMPLE_FILE_HANDLER = {
    'level': 'DEBUG',
    'class': 'logging.handlers.RotatingFileHandler',
    'formatter': 'simple',
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(name)s %(funcName)s %(threadName)s %(lineno)d : %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_DIR+'/debug.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

other_handlers = {}
other_loggers = {}

for app in LIST_OF_APPS:
    handler = SIMPLE_FILE_HANDLER.copy()
    handler['filename'] = LOG_FILE_DIR + '/service_online_logs.log' #Comment this line and uncomment the next line
    other_handlers['app_%s' % app] = handler
    other_loggers[app] = {
        'handlers': ['app_%s' % app],
        'level': 'DEBUG',
        'propagate': True,
    }

LOGGING['handlers'].update(other_handlers)
LOGGING['loggers'].update(other_loggers)