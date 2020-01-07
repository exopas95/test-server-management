from flask import Flask, render_template, url_for, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
	""" Create User table"""
	__table_name__ = 'user'

	id = db.Column(db.Integer, primary_key = True)
	email = db.Column(db.String(120), unique = True, nullable=False)
	password = db.Column(db.String(80), nullable=False)
	lastName = db.Column(db.String(80), nullable=False)
	firstName = db.Column(db.String(80), nullable=False)
	team = db.Column(db.String(80), nullable=False)
	userType = db.Column(db.String(80), nullable=False)

	def __init__(self, email, password, firstName, lastName, team, userType):
		self.email = email
		self.password = bcrypt.generate_password_hash(password)
		self.firstName = firstName
		self.lastName = lastName
		self.team = team
		self.userType = userType

	@staticmethod
	def authenticate(_email, _password):
		found_user = User.query.filter_by(email = _email).first()
		if found_user:
			authenticated_user = bcrypt.check_password_hash(found_user.password, _password)
			if authenticated_user:
				return True
		return False

class TSList(db.Model):
	""" Create tsList table"""
	__table_name__ = 'tsList'

	id = db.Column(db.Integer, primary_key = True)
	tsAddress = db.Column(db.String(120), unique = True, nullable=False)
	tasAddress = db.Column(db.String(120), nullable=False)
	tsName = db.Column(db.String(80), nullable=False)
	tsVersion = db.Column(db.String(80), nullable=False)
	tsState = db.Column(db.String(80), nullable=False)
	tsManagementIp = db.Column(db.String(80), nullable=False)
	tsPlatform = db.Column(db.String(80), nullable=False)
	tsMemory = db.Column(db.Integer, nullable=False)
	tsOS = db.Column(db.String(80), nullable=False)
	originTAS = db.Column(db.String(120), nullable=True)

	def __init__(self, tsAddress, tasAddress, tsName, tsVersion, tsState, tsManagementIp, tsPlatform, tsMemory, tsOS, originTAS):
		self.tsAddress = tsAddress
		self.tasAddress = tasAddress
		self.tsName = tsName
		self.tsVersion = tsVersion
		self.tsState = tsState
		self.tsManagementIp = tsManagementIp
		self.tsPlatform = tsPlatform
		self.tsMemory = tsMemory
		self.tsOS = tsOS
		self.originTAS = originTAS

class TASList(db.Model):
	""" Create tasList table"""
	__table_name__ = 'tasList'

	id = db.Column(db.Integer, primary_key = True)
	tasAddress = db.Column(db.String(120), unique = True, nullable=False)
	tasName = db.Column(db.String(80), nullable=False)

	def __init__(self, tasAddress, tasUsername):
		self.tasAddress = tasAddress
		self.tasName = tasUsername

	# get TAS list data from database
	@staticmethod
	def getTASListFromDB():
		TASlist = TASList.query.all()
		tempList = set()
		tempInfoList = []
		
		for index in TASlist:
			TASaddr = index.tasAddress
			tempList.add(TASaddr.rstrip())
	
			if len(tempInfoList) is not 0:
				del tempInfoList[:]

			for tas in tempList:
				tempInfoList.append(tas)

			tempInfoList.sort()

		return tempList, tempInfoList

db.create_all()
db.session.commit()
