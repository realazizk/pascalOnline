#!/usr/bin/env python2

########################################################################################
#	pascalOnline																	   #
#	Copyright (C) 2015  Mohamed Aziz Knani                                             #
#                                                                                      #
#	This program is free software; you can redistribute it and/or                      #
#	modify it under the terms of the GNU General Public License                        #
#	as published by the Free Software Foundation; either version 2                     #
#	of the License, or (at your option) any later version.                             #
#	                                                                                   #
#	This program is distributed in the hope that it will be useful,                    #
#	but WITHOUT ANY WARRANTY; without even the implied warranty of                     #
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                      #
#	GNU General Public License for more details.                                       #
#                                                                                      #
#	You should have received a copy of the GNU General Public License                  #
#	along with this program; if not, write to the Free Software                        #
#	Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.    #
########################################################################################

from app import app
from flask import render_template, request, redirect, url_for, make_response
import commands
from os import path
from base64 import b64encode
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import Column , DateTime , Integer , String
import hashlib

@app.errorhandler(404)
def page_not_found(e):
  return render_template('404.html'), 404

@app.route('/')
def index() :
	return render_template('main.html')

@app.route('/about')
def about() :
	return render_template('about.html')

@app.route('/compile/<string:filename>')
def compile(filename) :
	tocompile = path.join('tmp/', filename+'.pas')
	out = commands.getstatusoutput('fpc %s' % tocompile)[1]
	return render_template('compile.html', out=out.splitlines())

@app.route('/save', methods=['POST'])
def save() :
	import random
	import string
	
	# Get random string
	def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
		return ''.join(random.choice(chars) for _ in range(size))
	if 'file' not in request.cookies :
		filename = id_generator()
	else :
		filename = request.cookies['file']
	
	# Save file (I think it's secure enough)
	with open(path.join('tmp', filename+'.pas'), 'w+') as myfile :
		myfile.write(request.form['komutdosyasi'].encode('utf-8'))
		myfile.close()

	# Check if input box got values (not only spaces)
	if request.form['inpt'].strip() :
		print request.form['inpt']
		with open(path.join('tmp', filename+'.inp'), 'w+') as inpfile :
			inpfile.write(request.form['inpt'])
			inpfile.close()
			boo = True
	else : boo = False

	response = make_response(redirect(url_for('compile', filename=filename)))
	response.set_cookie('file', filename)
	response.set_cookie('pgm', b64encode(request.form['komutdosyasi'].encode('utf-8')))
	if boo :
		response.set_cookie('inp', b64encode(request.form['inpt']))
	return response

@app.route('/run')
def run() :

        from subprocess import Popen, PIPE, STDOUT
	if  'file' in request.cookies :
		filename = request.cookies['file']
	else :
		return redirect('/')
        if 'inp' in request.cookies:
                inp = b64decode(request.cookies['inp'])
        else:
                inp = ''
	# I use commands for now (This works only on *NIX)
	p = Popen([path.join('tmp/', filename)], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        out= p.communicate(input=inp)[0]
	return render_template('compile.html', out=out.splitlines())

engine = create_engine('sqlite:///pascalOnline.db',echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Paste(Base):
	__tablename__ = 'pastes'
	id = Column(Integer,primary_key=True)
	title = Column(String)
	author = Column(String)
	code = Column(String)
	publishdate=Column(DateTime)

	def __str__(self):
		return "(%d, %s, %s, %s)"%(self.id, self.title, self.author, self.code)
	# Get random avatar from md5 value of author name
	def gravatar_url(self):
		return  "http://www.gravatar.com/avatar/%s?s=50&d=retro" % hashlib.md5(self.author).hexdigest()

@app.route('/community/<int:page>')
def community(page) :
	# Get number of pages (The dumb way)
	def getpages(st) :
		if st[-1] != '0' :
			res = int(st[0])+1
		else :
			res = int(st[0])
		return res
	nv = page
	nv -= 1
	s=Session()
	# Get last 10 using python slices (an ugly hack i could use limit())
	pastes = s.query(Paste).order_by(Paste.id.desc())[10*nv:10+(nv*10)]
	pg = s.query(Paste).order_by(Paste.id.desc()).first().id
	nbpgs = getpages(str(pg))
	return render_template('community.html', pastes=pastes)

@app.route('/view/<int:n>')
def view(n) :
	s=Session()
	# Make request by id
	paste = s.query(Paste).filter_by(id=n).first()
	return render_template('view.html', paste=paste)

@app.route('/paste', methods=['POST'])
def pastein() :
	import datetime
	if request.form['komutdosyasi'] :
		newPaste = Paste(title=request.form['titleofcode'],author=request.form['author'],\
			         code=request.form['komutdosyasi'],publishdate=datetime.datetime.now())
		s=Session()
		s.add(newPaste)
		s.commit()
		return redirect(url_for('view', n=newPaste.id))
