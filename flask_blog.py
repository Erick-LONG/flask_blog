from flask import Flask

# __name__参数决定程序的根目录
app = Flask (__name__)


@app.route ('/')
def hello_world():
	return 'Hello World!'

@app.route ('/user/<name>') #
def user(name):
	return '<h1>Hello,%s!</h1>'% name

@app.route ('/user/<int:id>') # 还可以类型定义/user/<int:id> float path类型
def user_id(id):
	return '<h1>Hello,%s!</h1>'% id

if __name__ == '__main__':
	app.run ()
