from flask import Flask,render_template
from flask_script import Manager
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired

app = Flask (__name__)
app.config['SECRET_KEY']='hard to guess string' # 可以用来存储框架，扩展，程序等的配置变量



class NameForm(FlaskForm):
	name = StringField('姓名',validators=[DataRequired()])
	submit = SubmitField('提交')


bootstrap = Bootstrap(app)
moment = Moment(app)
@app.route ('/',methods=['get','post'])
def index1():
	name=None
	form=NameForm()
	if form.validate_on_submit():
		name=form.name.data
		form.name.data=''
	return render_template('index.html',name=name,form=form,current_time = datetime.utcnow())


@app.route ('/user/<name>')
def index(name):
	return render_template('user.html',name= name)

@app.errorhandler(404)
def page_not_find(e):
	return render_template('404.html'),404

@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'),500


if __name__ == '__main__':
	app.run (debug=True)
