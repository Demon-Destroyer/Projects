import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from flask_restful import Api, Resource, abort, reqparse, fields, marshal_with

#------- Flask App Configuration --------
app=Flask(__name__)
app.config['SECRET_KEY']='thisismysecretkey'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///quizzes.sqlite'
db=SQLAlchemy()
db.init_app(app)
api=Api(app)
app.app_context().push()

scheduler=BackgroundScheduler()
#-------------Databases------------

class Quiz(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    question=db.Column(db.String(500), nullable=False)
    options=db.Column(db.String(500), nullable=False)
    rightAnswer=db.Column(db.String(500), nullable=False)
    startDate=db.Column(db.String(500), nullable=False)
    endDate=db.Column(db.String(500), nullable=False)
    status=db.Column(db.String(500), nullable=False, default="inactive")

#format yyyy-mm-dd hr:min:sec.microsec
def change_quiz_status():
    now = datetime.datetime.now()

    quizzes_to_start = Quiz.query.filter(Quiz.startDate > now and Quiz.endDate > now).all()
    quizzes_to_stop = Quiz.query.filter(Quiz.endDate < now).all()
    for quiz in quizzes_to_start:
        quiz.status = 'active'
        db.session.commit()
    for quiz in quizzes_to_stop:
        quiz.status = 'finished'

@app.before_first_request
def start_scheduler():
    scheduler.add_job(change_quiz_status, 'interval', minutes=1)
    scheduler.start()
    

#---------------APIs----------------
quiz_field={
    'id':fields.Integer,
    'question': fields.String,
    'options':fields.String,
    'rightAnswer':fields.String,
    'startDate': fields.String,
    'endDate': fields.String,
    'status':fields.String
}

quiz_req=reqparse.RequestParser()
quiz_req.add_argument("question")
quiz_req.add_argument("options")
quiz_req.add_argument("rightAnswer")
quiz_req.add_argument("startDate")
quiz_req.add_argument("endDate")
quiz_req.add_argument("status")

class QuizAPI(Resource):


    @marshal_with(quiz_field)
    def get(self, id=None, status=None):
        if id:
            quiz=Quiz.query.get(id)
            if not quiz:
                abort(404, message="quiz not found")
            else:
                answer=quiz.rightAnswer
                return {"id":quiz.id ,"rightAnswer": answer}, 200
            
        elif status:
            quizActive=Quiz.query.filter_by(status="active").all()
            quizInactive=Quiz.query.filter_by(status="inactive").all()
            if status=="active":
                return quizActive, 200
            elif status=="inactive":
                return quizInactive, 200
        else:
            quiz=Quiz.query.all()
            return quiz, 200

    @marshal_with(quiz_field)
    def post(self, id=None):
        data= quiz_req.parse_args()

        quizData= Quiz(question=data.question, options=data.options, rightAnswer=data.rightAnswer, startDate=data.startDate, endDate=data.endDate, status=data.status)

        db.session.add(quizData)
        db.session.commit()
        return quizData, 200
    
api.add_resource(QuizAPI, '/api/quiz', '/api/quiz/<int:id>', '/api/quiz/<status>')

if __name__=='__main__':
    db.create_all()
    app.run(debug=True)