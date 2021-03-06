# -*- coding: utf-8 -*-
from app import app, db
from flask import Blueprint, request, url_for, flash, redirect, abort, session, g
from flask import render_template
from flask import current_app
from flask.ext.login import login_user, logout_user, current_user, login_required
from forms import LikertField, MyRadioField
from forms import generate_form
from utiles import generate_answer
from app.models import Survey, Consent, Section
from app.models import Question, QuestionChoice, QuestionText
from app.models import QuestionYN ,QuestionLikertScale
from app.models import StateSurvey
from app.models import Answer
from app.models import Raffle
from app.models import GameImpatience
from app.models import GameLottery1, GameLottery2, GameRent1, GameRent2, GameUltimatum, GameDictador
from sqlalchemy.sql import func
import datetime
from . import blueprint
from app.decorators import valid_survey, there_is_stateSurvey
from ..main.errors import ErrorEndDateOut, ErrorExceeded, ErrorTimedOut
from app.game.game import Games
from sqlalchemy import or_
from sqlalchemy import and_
from flask.ext.babel import gettext


# @blueprint.route('/', methods=['GET', 'POST'])
# @blueprint.route('/index', methods=['GET', 'POST'])
# @login_required
def index():
    '''
    shows all available surveys
    '''
    stmt1 = db.session.query(StateSurvey.survey_id, StateSurvey.status).\
        filter(StateSurvey.user==current_user).subquery()
    
    stmt2 = db.session.query(StateSurvey.survey_id, func.count('*').label('r_count')).\
        filter(StateSurvey.status.op('&')(StateSurvey.FINISH_OK)).\
        group_by(StateSurvey.survey_id).subquery()

    now = datetime.datetime.utcnow()
    #outerjoint Survey and StateSurvey(with the currentUser) and number of user
    # that have made the survey
    surveys = db.session.query(Survey, stmt1.c.status, stmt2.c.r_count).\
        outerjoin(stmt1,Survey.id==stmt1.c.survey_id).\
        outerjoin(stmt2,Survey.id==stmt2.c.survey_id).\
        filter(Survey.startDate<now,Survey.endDate>now).\
        order_by(Survey.startDate)
    return render_template('/surveys/index.html',
        title = 'Index',
        # surveys= [s.Survey for s in surveys],
        surveys = surveys) 

def get_stateSurvey_or_error(id_survey,user,ip = None):
    stateSurvey, status = StateSurvey.getStateSurvey(id_survey,user,ip)
    if status == StateSurvey.NO_ERROR:
        return stateSurvey
    else:
        if status == StateSurvey.ERROR_EXCEEDED:
            raise ErrorExceeded
        if status == StateSurvey.ERROR_TIMED_OUT:
            raise ErrorTimedOut
        if status == StateSurvey.ERROR_END_DATE_OUT:
            raise ErrorEndDateOut
        if status == StateSurvey.ERROR_NO_SURVEY:
            return abort(404)
        return abort(500)    

def check_feedback(id_survey):
    '''check if survey have feedback
    '''
    ans = Answer.query.filter(Answer.user_id==current_user.id,
        Answer.question_id==Question.id,
        Question.section_id==Section.id, 
        Section.root_id==id_survey,
        Question.container==["feedback"]).first()
    if ans is not None:
        if ans.answerYN:
            return redirect(url_for('feedback.logic_feedback', id_survey = id_survey))
    return render_template('/surveys/finish.html', 
        title = 'Finish')

def run_part2_raffle(id_survey):
    '''run part2 and raffle if user no always game with untrue money
    '''
    game = Games(id_survey)
    game.part2_reimplement(current_user)
    game.raffle(current_user)
    game.match()


@blueprint.route('/survey/<int:id_survey>', methods=['GET', 'POST'])
@login_required
@valid_survey
def logicSurvey(id_survey):
    '''
    Function that decides which is the next step in the survey
    '''
    stateSurvey = get_stateSurvey_or_error(id_survey,g.user,request.remote_addr)

    if (stateSurvey.consented == False):
        return redirect(url_for('surveys.showConsent', id_survey = id_survey))
    section = stateSurvey.nextSection()
    if section is None:
        if stateSurvey.status & StateSurvey.FINISH_OK:
            run_part2_raffle(id_survey)
            return check_feedback(id_survey)
        if stateSurvey.status & StateSurvey.TIMED_OUT:
            return render_template('/surveys/error_time_date.html',
                title ='time out')
        if stateSurvey.status & StateSurvey.END_DATE_OUT:
            return render_template('/surveys/error_time_date.html',
                title ='End date out')
        print "\n raro\n Status: ", stateSurvey.status
        return abort(500) 
    if section.id in [40,43,46,49,32,33,23,52,55,58,61,38,39,27]:
        #fixed to show number of decision
        return show_number_decision(id_survey,section.id)

    if section.id in [10,11,12,13]:
        #fixed to show number of part
        return show_number_parte(id_survey,section.id)


    return redirect (url_for('surveys.showQuestions',id_survey=id_survey,id_section=section.id))


def get_number_decision(id_survey,id_section):
    ''' get number of decision
    '''
    def get_date_decision(decision, user_id,id_survey):
        '''return date when answered 
        '''
        return Answer.query.filter(Answer.user_id==user_id,\
                Answer.question_id==Question.id,\
                Question.section_id==Section.id,\
                Section.root_id==id_survey,\
                Question.decision==decision).first() is not None

    def get_date_decision1(user_id,id_survey):
        '''return date when answered 
        '''
        return Answer.query.filter(Answer.user_id==user_id,\
                Answer.question_id==Question.id,\
                Question.section_id==Section.id,\
                Section.root_id==id_survey,\
                Question.decision.in_(["decision_one_v1","decision_one_v2"])).\
                first() is not None

    id_survey = 1
    n_decision = 1

    n_decision = n_decision + 1 if get_date_decision1(current_user.id,id_survey) else n_decision
    n_decision = n_decision + 1 if get_date_decision("decision_two",current_user.id,id_survey) else n_decision
    n_decision = n_decision + 1 if get_date_decision("decision_three",current_user.id,id_survey) else n_decision
    n_decision = n_decision + 1 if get_date_decision("decision_four",current_user.id,id_survey) else n_decision
    n_decision = n_decision + 1 if get_date_decision("decision_five",current_user.id,id_survey) else n_decision
    n_decision = n_decision + 1 if get_date_decision("decision_six",current_user.id,id_survey) else n_decision

    return n_decision



@blueprint.route('/survey/<int:id_survey>/decision', methods=['GET', 'POST'])
@login_required
def show_number_decision(id_survey,id_section):
    ''' show number of decision
    '''
    if request.method == 'POST':
        return redirect (url_for('surveys.showQuestions',id_survey=id_survey,id_section=id_section))
    text = '<h1>Decisión %s</h1>' % (get_number_decision(id_survey, id_section))

    return render_template('/surveys/show_decision.html',
        text = text)

@blueprint.route('/survey/<int:id_survey>/parte', methods=['GET', 'POST'])
@login_required
def show_number_parte(id_survey,id_section):
    '''show number_part of the survey
    '''
    id_survey = 1
    ss = get_stateSurvey_or_error(id_survey,g.user)
    if request.method == 'POST':
        return redirect (url_for('surveys.showQuestions',id_survey=id_survey,id_section=id_section))

    n_part = 1

    n_part = n_part + 1 if 10 in ss.sequence[0:ss.index+1] else n_part
    n_part = n_part + 1 if 11 in ss.sequence[0:ss.index+1] else n_part
    n_part = n_part + 1 if 12 in ss.sequence[0:ss.index+1] else n_part
    n_part = n_part + 1 if 13 in ss.sequence[0:ss.index+1] else n_part

    if n_part == 2:
        text='<h1>Segunda Parte</h1>'
    elif n_part == 3:
        text='<h1>Tercera Parte</h1>'
    else :
        text = ""


    return render_template('/surveys/show_decision.html',
        text = text)



@blueprint.route('/survey/<int:id_survey>/consent', methods=['GET', 'POST'])
@blueprint.route('/survey/<int:id_survey>/consent/<int:n_consent>', methods=['GET', 'POST'])
@login_required
@valid_survey
@there_is_stateSurvey
def showConsent(id_survey,n_consent = 0):
    '''
    Show consent, n_consent is the "position of consent", no id!!
    '''
    
    survey = Survey.query.get(id_survey)
    consents = survey.consents

    if n_consent>consents.count():
        abort (404)

    if consents.count()==0:
        stateSurvey = get_stateSurvey_or_error(id_survey,g.user)
        stateSurvey.accept_consent()
        return redirect(url_for('surveys.logicSurvey',id_survey = id_survey))
    
    if request.method == 'POST' and consents.count()<=n_consent+1:
        stateSurvey = get_stateSurvey_or_error(id_survey,g.user)
        stateSurvey.accept_consent()
        return redirect(url_for('surveys.logicSurvey',id_survey = id_survey))

    if request.method == 'POST' and consents.count()>n_consent+1:
        return redirect(url_for('surveys.showConsent', id_survey = id_survey, n_consent = n_consent+1))


    return render_template('/surveys/consent.html',
        title = survey.title,
        survey = survey,
        consent = survey.consents[n_consent])




def writeQuestion(question, form):
    '''return true if it isn't a subquestion or
        if a question.parent is valid
    '''
    if question.parent is None:
        return True
    else:
        data = form["c"+str(question.parent.id)].data
        if isinstance (question.parent,QuestionYN):
            if data.lower()==question.condition.value.lower():
                return True
            else:
                return False
        if isinstance (question.parent,QuestionText) or\
         isinstance(question.parent,QuestionChoice):
            if question.condition.operation=="<":
                if data<question.condition.value:
                    return True
                else:
                    return False
            if question.condition.operation=="==":
                if data==question.condition.value:
                    return True
                else:
                    return False
            if question.condition.operation==">":
                if int(data)>int(question.condition.value):
                    return True
                else:
                    return False


@blueprint.route('/survey/<int:id_survey>/section/<int:id_section>', methods=['GET', 'POST'])
@login_required
@valid_survey
@there_is_stateSurvey
def showQuestions(id_survey, id_section):
    '''
    Show all question of a section
    '''
    stateSurvey = get_stateSurvey_or_error(id_survey,g.user,request.remote_addr)
    section = stateSurvey.nextSection()
    if section is None or section.id !=id_section:
        flash (gettext("access denied"))
        return abort (403)
        
    survey = Survey.query.get(id_survey)
    section = Section.query.get(id_section)
    questions = section.questions
   
    form = generate_form(questions)
    if form.validate_on_submit():
        for question in questions:
            if writeQuestion(question, form):
                answer = generate_answer(question,form,g.user)
            db.session.add(answer)
        db.session.commit()
        stateSurvey.finishedSection(form.time.data)
        return redirect(url_for('surveys.logicSurvey',id_survey = id_survey))

    #dirty fix to show number decision, if i know it before...
    decision = None
    if id_section in [40,41,42,43,44,45,46,47,48,49,50,51,32,33,23,52,53,54,55,56,57,58,59,60,61,62,63,38,39,27]:
        if id_section in [40,43,46,49,52,55,58,61]:
            decision = '<h3>Decisión %s, parte 1</h3>' % (get_number_decision(id_survey, id_section))
        elif id_section in [41,44,47,50,53,56,59,62]:
            decision = '<h3>Decisión %s, parte 2</h3>' % (get_number_decision(id_survey, id_section))
        elif id_section in [42,45,48,51,54,57,60,63]:
            decision = '<h3>Decisión %s, parte 3</h3>' % (get_number_decision(id_survey, id_section)-1)
        else:
            decision = '<h3>Decisión %s</h3>' % (get_number_decision(id_survey, id_section))
        print "vamos",get_number_decision(id_survey, id_section)    

    return render_template('/surveys/showQuestions.html',
            title = survey.title,
            survey = survey,
            section = section,
            # form = form,
            form = form,
            questions = questions,
            # percent = stateSurvey.percentSurvey(),
            decision = decision
            )
