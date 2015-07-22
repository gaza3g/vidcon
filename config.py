import os


class Config(object):
	DEBUG = False
	TESTING = False
	CSRF_ENABLED = True
	SECRET_KEY = '43DK&$GBV$MSHY'
	SQLALCHEMY_DATABASE_URI = "postgresql://localhost/vidconuser"
	VIDCON_ROOT = '/media/edulearnupload/'


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
	VIDCON_ROOT = '/Volumes/EdulearnNETUpload/'
