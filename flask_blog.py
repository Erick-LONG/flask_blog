from flask import Flask

from flask import request
from flask import make_response
from flask import abort
from flask import redirect
# __name__参数决定程序的根目录
app = Flask (__name__)


# @app.route ('/')
# def hello_world():
# 	return 'Hello World!'

# @app.route ('/user/<name>') #
# def user(name):
# 	return '<h1>Hello,%s!</h1>'% name
#
# @app.route ('/user/<int:id>') # 还可以类型定义/user/<int:id> float path类型
# def user_id(id):
# 	return '<h1>Hello,%s!</h1>'% id

# @app.route ('/') # 请求上下文
# def index():
# 	user_agent = request.headers.get('User-Agent')
# 	return 'your browser is %s' % user_agent

# @app.route ('/') # 请求响应,可接受第二个参数为状态码
# def index():
# 	return 'bad request',400

# @app.route ('/')
# def hello_world():
# 	response =make_response('这个文档带着COOKIE!')
# 	response.set_cookie('answer','42')
# 	return response

# @app.route ('/')
# def hello_world():
# 	return redirect('http://www.baidu.com')
@app.route ('/user/<id>')
def hello_world(id):
	#user = load_user(id)
	user = False
	if not user:
		abort(404)
	return 'hello %s' % user

from flask.ext.script import Manager # 通过pip install flask-script 启用manager 启动后解析命令行
manager = Manager(app)
if __name__ == '__main__':
	manager.run ()

# if __name__ == '__main__':
# 	app.run (debug=True)
